from __future__ import absolute_import, unicode_literals
import os
import django
from celery import Celery
from django.conf import settings
import requests
import whois
from urllib.error import HTTPError
import urllib.request
from datetime import datetime, timezone
import tzlocal
from ping3 import ping
from django.core.mail import send_mail

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from monitor.models import Log, Monitor, EmailValues



time_zone = tzlocal.get_localzone()
now = datetime.now(time_zone)
format_str = "%Y-%m-%d %H:%M:%S %z"

app = Celery('mysite')
app.conf.enable_utc = False

app.config_from_object(settings, namespace='CELERY')

app.autodiscover_tasks()


@app.task
def collect_data_url(url, timeout, monitor_id):
    data = {}
    monitor = Monitor.objects.get(id=monitor_id)

    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            data['domain'] = url[8:]
            data['ping'] = round(ping(data['domain'], unit='ms'))
            data['response_time'] = round(response.elapsed.total_seconds() * 1000)
            data['status_code'] = response.status_code

            match data['status_code']:
                case code if 100 <= code <= 199:
                    data['status'] = "Informational responses"
                case code if 200 <= code <= 299:
                    data['status'] = "Successful responses"
                case code if 300 <= code <= 399:
                    data['status'] = "Redirection messages"
                case code if 400 <= code <= 499:
                    data['status'] = "Client error responses"
                case code if 500 <= code <= 599:
                    data['status'] = "Server error responses "

            if monitor.status == "offline":
                for tmp in EmailValues.objects.filter(monitor_id=monitor_id):
                    send_mail(
                        "Twoja monitorowana strona przeszła w status online",
                        "Strona powróciła do poprawnego działania",
                        settings.EMAIL_HOST_USER,
                        [tmp.email],
                        fail_silently=False,
                    )
                monitor.status = "online"
                monitor.save()

    except requests.exceptions.Timeout:
        data['status_code'] = 408
        data['status'] = "Connection timeout"
        if monitor.status == "online":
            for tmp in EmailValues.objects.filter(monitor_id=monitor_id):
                send_mail(
                    "Twoja monitorowana strona przeszła w status offline",
                    "Sprawdź czy wszystko działa poprawnie",
                    settings.EMAIL_HOST_USER,
                    [tmp.email],
                    fail_silently=False,
                )
            monitor.status = "offline"
            monitor.save()

    except Exception:
        data['status'] = "Error"
        try:
            conn = urllib.request.urlopen(url)
            data['status_code'] = conn.getcode()
        except HTTPError as e:
            data['status_code'] = e.code
        except:
            data['status_code'] = 404
        if monitor.status == "online":
            for tmp in EmailValues.objects.filter(monitor_id=monitor_id):
                send_mail(
                    "Twoja monitorowana strona przeszła w status offline",
                    "Sprawdź czy wszystko działa poprawnie",
                    settings.EMAIL_HOST_USER,
                    [tmp.email],
                    fail_silently=False,
                )
            monitor.status = "offline"
            monitor.save()

    if "ping" in data:
        l = Log(monitor_id=monitor, ping=data['ping'], response_time=data['response_time'],
                status_code=data['status_code'], status=data['status'])
    else:
        l = Log(monitor_id=monitor, status_code=data['status_code'], status=data['status'])

    l.save()


@app.task
def collect_data_ping(url, timeout, monitor_id):
    data = {}
    monitor = Monitor.objects.get(id=monitor_id)
    try:
        conn = urllib.request.urlopen(url)
        data['status_code'] = conn.getcode()
    except HTTPError as e:
        data['status_code'] = e.code
    except:
        data['status_code'] = 404

    try:
        data['domain'] = url[8:]
        data['ping'] = round(ping(data['domain'], unit='ms'))
        data['status'] = "Successful responses"
        if monitor.status == "offline":
            for tmp in EmailValues.objects.filter(monitor_id=monitor_id):
                send_mail(
                    "Twoja monitorowana strona przeszła w status online",
                    "Strona powróciła do poprawnego działania",
                    settings.EMAIL_HOST_USER,
                    [tmp.email],
                    fail_silently=False,
                )
            monitor.status = "online"
            monitor.save()
    except Exception as e:
        data['status'] = "Error"
        if monitor.status == "online":
            for tmp in EmailValues.objects.filter(monitor_id=monitor_id):
                send_mail(
                    "Twoja monitorowana strona przeszła w status offline",
                    "Sprawdź czy wszystko działa poprawnie",
                    settings.EMAIL_HOST_USER,
                    [tmp.email],
                    fail_silently=False,
                )
            monitor.status = "offline"
            monitor.save()
        print(e)
    l = Log(monitor_id=monitor, status=data['status'], ping=data['ping'], status_code=data['status_code'])
    l.save()


# TODO
@app.task
def ssl_monitor(url, timeout, monitor_id, days_before_to_inform):
    data = {}
    monitor = Monitor.objects.get(id=monitor_id)
    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            data['domain'] = url[8:]
            w = whois.whois(data['domain'])
            certificate_info = response.raw.connection.sock.getpeercert()
            tmp = datetime.strptime((certificate_info["notBefore"])[0:-4], '%b %d %H:%M:%S %Y')
            data['cert_from'] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

            tmp = datetime.strptime((certificate_info["notAfter"])[0:-4], '%b %d %H:%M:%S %Y')
            data['cert_to'] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

            if type(w.expiration_date) == list:
                w.expiration_date = w.expiration_date[0]

            data['domain_exp'] = w.expiration_date.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(
                format_str)

            timedelta = w.expiration_date.replace(tzinfo=timezone.utc).astimezone(time_zone) - now
            data['days_to_domain_exp'] = timedelta.days

            timedelta = (tmp.replace(tzinfo=timezone.utc).astimezone(time_zone)) - now
            data['days_to_ssl_exp'] = timedelta.days

            if data['days_to_ssl_exp'] < days_before_to_inform:
                for tmp in EmailValues.objects.filter(monitor_id=monitor_id):
                    send_mail(
                        f"Twój certyfikat SSL wygasa za: {data['days_to_ssl_exp']} dni",
                        f"Ważność twojego certyfikatu SSL dobiega końca, natomiast domena wygasa za: {data['days_to_domain_exp']} dni",
                        settings.EMAIL_HOST_USER,
                        [tmp.email],
                        fail_silently=False,
                    )

            data['status'] = "Successful responses"

            l = Log(monitor_id=monitor, status=data['status'], cert_from=data['cert_from'], cert_to=data['cert_to'],
                    domain_exp=data['domain_exp'], days_to_domain_exp=data['days_to_domain_exp'],
                    days_to_ssl_exp=data['days_to_ssl_exp'])
            l.save()
    except:
        l = Log(monitor_id=monitor, status="SSL check error")
        l.save()

# celery -A mysite worker --beat --scheduler django
