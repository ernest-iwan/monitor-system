import time
import urllib.request
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError

import requests
import tzlocal
import whois
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from ping3 import ping

from monitor.models import ApiRequest, EmailValues, Log, Monitor

time_zone = tzlocal.get_localzone()
now = datetime.now(time_zone)
format_str = "%Y-%m-%d %H:%M:%S %z"


@shared_task()
def collect_data_url(url, timeout, monitor_id):
    data = {}
    monitor = Monitor.objects.get(id=monitor_id)

    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            data["domain"] = url.replace("https://", "").replace("http://", "")
            data["domain"].replace("https://", "")
            data["ping"] = round(ping(data["domain"], unit="ms"))
            data["response_time"] = round(response.elapsed.total_seconds() * 1000)
            data["status_code"] = response.status_code

            # Map status code ranges to status categories
            match data["status_code"]:
                case code if 100 <= code <= 199:
                    data["status"] = "Informational responses"
                case code if 200 <= code <= 299:
                    data["status"] = "Successful responses"
                case code if 300 <= code <= 399:
                    data["status"] = "Redirection messages"

            # If monitor status changes, notify via email
            if monitor.status == "offline":
                notify_status_change(monitor, "online")

    except requests.exceptions.Timeout:
        data["status_code"] = 408
        data["status"] = "Connection timeout"
        if monitor.status == "online":
            notify_status_change(monitor, "offline")

    except Exception:
        try:
            conn = urllib.request.urlopen(url)
            data["status_code"] = conn.getcode()
            data["status"] = "Successful responses"
        except HTTPError as e:
            data["status_code"] = e.code
            data["status"] = "Error"
            if monitor.status == "online":
                notify_status_change(monitor, "offline")
        except Exception:
            data["status_code"] = 404
            data["status"] = "Error"
            if monitor.status == "online":
                notify_status_change(monitor, "offline")

    # Create log entry
    create_log_entry(monitor, data)


@shared_task()
def collect_data_ping(url, timeout, monitor_id):
    data = {}
    monitor = Monitor.objects.get(id=monitor_id)

    try:
        conn = urllib.request.urlopen(url)
        data["status_code"] = conn.getcode()
    except HTTPError as e:
        data["status_code"] = e.code
    except Exception:
        data["status_code"] = 404

    try:
        data["domain"] = url.replace("https://", "").replace("http://", "")
        data["ping"] = round(ping(data["domain"], unit="ms", timeout=timeout))
        data["status"] = "Successful responses"
        if monitor.status == "offline":
            notify_status_change(monitor, "online")
    except Exception:
        data["status"] = "Error"
        if monitor.status == "online":
            notify_status_change(monitor, "offline")

    # Create log entry
    create_log_entry(monitor, data)


@shared_task()
def collect_data_crone(url, timeout, monitor_id):
    monitor = Monitor.objects.get(id=monitor_id)

    time.sleep(timeout)

    start_time = datetime.now(time_zone) - timedelta(seconds=timeout)
    end_time = datetime.now(time_zone)
    api_requests = ApiRequest.objects.filter(monitor=monitor, request_date__range=(start_time, end_time))

    if api_requests.exists():
        api_request = api_requests.first()
        response_time = api_request.request_date.astimezone(time_zone) - start_time

        data = {
            "status": "Successful responses",
            "status_code": 200,
            "response_time": response_time.total_seconds() * 1000,
        }
        if monitor.status == "offline":
            notify_status_change(monitor, "online")
    else:
        data = {
            "status": "No ApiRequest within the specified interval",
            "status_code": 404,
            "response_time": 0,
        }
        if monitor.status == "online":
            notify_status_change(monitor, "offline")

    create_log_entry(monitor, data)


@shared_task()
def ssl_monitor(url, timeout, monitor_id, days_before_to_inform):
    # FIXME pozostawić tylko pobieranie SSL
    data = {}
    monitor = Monitor.objects.get(id=monitor_id)

    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            data["domain"] = url.replace("https://", "").replace("https://", "")
            w = whois.whois(data["domain"])
            certificate_info = response.raw.connection.sock.getpeercert()
            tmp = datetime.strptime((certificate_info["notBefore"])[0:-4], "%b %d %H:%M:%S %Y")
            data["cert_from"] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)
            tmp = datetime.strptime((certificate_info["notAfter"])[0:-4], "%b %d %H:%M:%S %Y")
            data["cert_to"] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)
            data["ping"] = round(ping(data["domain"], unit="ms"))

            if type(w.expiration_date) is list:
                w.expiration_date = w.expiration_date[0]

            data["domain_exp"] = (
                w.expiration_date.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)
            )
            timedelta = w.expiration_date.replace(tzinfo=timezone.utc).astimezone(time_zone) - now
            data["days_to_domain_exp"] = timedelta.days

            timedelta = (tmp.replace(tzinfo=timezone.utc).astimezone(time_zone)) - now
            data["days_to_ssl_exp"] = timedelta.days

            if data["days_to_ssl_exp"] < days_before_to_inform:
                notify_ssl_expiry(monitor, data["days_to_ssl_exp"], data["days_to_domain_exp"])

            data["status"] = "Successful responses"

    except Exception:
        data["status"] = "SSL check error"

    # Create log entry
    try:
        conn = urllib.request.urlopen(url)
        data["status_code"] = conn.getcode()
    except HTTPError as e:
        data["status_code"] = e.code
    except Exception:
        data["status_code"] = 404

    create_log_entry(monitor, data)


def notify_status_change(monitor, new_status):
    for tmp in EmailValues.objects.filter(monitor=monitor.id):
        send_mail(
            f"Twoja monitorowana strona przeszła w status {new_status}",
            (
                "Strona powróciła do poprawnego działania"
                if new_status == "online"
                else "Sprawdź czy wszystko działa poprawnie"
            ),
            settings.EMAIL_HOST_USER,
            [tmp.email],
            fail_silently=False,
        )
    monitor.status = new_status
    monitor.save()


def notify_ssl_expiry(monitor, days_to_ssl_exp, days_to_domain_exp):
    for tmp in EmailValues.objects.filter(monitor=monitor.id):
        send_mail(
            f"Twój certyfikat SSL wygasa za: {days_to_ssl_exp} dni",
            f"Ważność twojego certyfikatu SSL dobiega końca, natomiast domena wygasa za: {days_to_domain_exp} dni",
            settings.EMAIL_HOST_USER,
            [tmp.email],
            fail_silently=False,
        )


def create_log_entry(monitor, data):
    if monitor.monitor_type == "ping":
        log = Log(
            monitor=monitor,
            ping=data["ping"],
            response_time=0,
            status_code=data["status_code"],
            status=data["status"],
        )
    elif "ping" in data:
        log = Log(
            monitor=monitor,
            ping=data["ping"],
            response_time=data["response_time"],
            status_code=data["status_code"],
            status=data["status"],
        )
    elif "domain_exp" in data:
        log = Log(
            monitor=monitor,
            ping=data["ping"],
            response_time=0,
            status=data["status"],
            cert_from=data["cert_from"],
            cert_to=data["cert_to"],
            domain_exp=data["domain_exp"],
            days_to_domain_exp=data["days_to_domain_exp"],
            days_to_ssl_exp=data["days_to_ssl_exp"],
        )
    elif monitor.monitor_type == "cron_job":
        log = Log(
            monitor=monitor,
            ping=0,
            response_time=data["response_time"],
            status=data["status"],
        )
    else:
        log = Log(
            monitor=monitor,
            ping=0,
            response_time=0,
            status_code=data["status_code"],
            status=data["status"],
        )

    log.save()
