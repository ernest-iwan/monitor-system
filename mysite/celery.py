from __future__ import absolute_import, unicode_literals
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django
django.setup()

from celery import Celery
from django.conf import settings
from celery.schedules import crontab
from monitor.models import Log, Monitor
import requests
import ssl
import whois
from datetime import datetime, timezone
import tzlocal
from ping3 import ping

now = datetime.now()
format_str = "%Y-%m-%d %H:%M:%S %z"
time_zone = tzlocal.get_localzone()

app = Celery('mysite')
app.conf.enable_utc = False

app.config_from_object(settings, namespace='CELERY')

app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, collect_data.s("https://google.com"), name='check domain google every 10 sec')
    sender.add_periodic_task(10.0, get_monitors.s(), name='get monitors')


   #  TODO
   #  Find method to setup perodic tasks for all monitors
   #  1. Setup all on run (check if exist by monitor id)
   #  2. Start periodic task on monitor add
   #  3. 1+2 option
   #  4.Other options

    # # Calls test('hello') every 30 seconds.
    # # It uses the same signature of previous task, an explicit name is
    # # defined to avoid this task replacing the previous one defined.
    # sender.add_periodic_task(30.0, test.s('hello'), name='add every 30')

    # # Calls test('world') every 30 seconds
    # sender.add_periodic_task(30.0, test.s('world'), expires=10)

    # # Executes every Monday morning at 7:30 a.m.
    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     test.s('Happy Mondays!'),
    # )

# @app.task
# def test(arg):
#     print("test")

# @app.task
# def add(x, y):
#     z = x + y
#     print(z)
@app.task
def get_monitors():
   for x in Monitor.objects.filter(is_active=True):
      print(x)

@app.task
def collect_data(url):
   data = {}
   try:
      with requests.get(url, stream=True, timeout=5) as response:
         data['request_datetime'] = datetime.now(time_zone).strftime(format_str)
         data['domain'] = url[8:]
         data['ping'] = round(ping(data['domain'], unit='ms'))
         data['respones_time'] = round(response.elapsed.total_seconds() * 1000)
         w = whois.whois(data['domain'])

         certificate_info_raw = response.raw.connection.sock.getpeercert(True)
         certificate_info = response.raw.connection.sock.getpeercert()

         data['cert'] = ssl.DER_cert_to_PEM_cert(certificate_info_raw)
         data['status_code'] = response.status_code

         tmp =  datetime.strptime((certificate_info["notBefore"])[0:-4], '%b %d %H:%M:%S %Y')
         data['cert_from'] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

         tmp =  datetime.strptime((certificate_info["notAfter"])[0:-4], '%b %d %H:%M:%S %Y')
         data['cert_to'] = tmp.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

         if type(w.expiration_date) == list:
            w.expiration_date = w.expiration_date[0]

         data['domain_exp'] = w.expiration_date.replace(tzinfo=timezone.utc).astimezone(time_zone).strftime(format_str)

         timedelta = w.expiration_date - now
         data['days_to_domain_exp'] = timedelta.days

         match data['status_code']:
            case code if code >=100 and code <= 199:
               data['status'] = "Informational responses"
            case code if code >=200 and code <= 299:
               data['status'] = "Successful responses"
            case code if code >=300 and code <= 399:
               data['status'] = "Redirection messages"
            case code if code >=400 and code <= 499:
               data['status'] = "Client error responses"
            case code if code >=500 and code <= 599:
               data['status'] = "Server error responses "

      l = Log(domain=data['domain'], ping=data['ping'], response_time=data['respones_time'], cert=data['cert'], status_code=data['status_code'], status=data['status'], cert_from=data['cert_from'], cert_to=data['cert_to'], domain_exp=data['domain_exp'], days_to_domain_exp=data['days_to_domain_exp'])
      l.save()

   except Exception as e:
      print(e)

# celery -A mysite worker --beat --scheduler django