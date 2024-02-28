from django.conf import settings
from django.db import models
from django.utils import timezone

# FIXME
# class Monitor(models.Model):
#     name = models.CharField(max_length=100)
#     monitor_type = models.Choices({"http request":"Http Request", "ping":"Ping", "cron job":"Cron Job"})
#     request_timeout = models.FloatField()
#     interval = models.FloatField()
#     # TODO Email as array(Postgre) or relationship(many2one)
#     add_date = models.DateTimeField(default=timezone.now)
#     status = models.Choices({"online":"Online", "ofline":"Ofline"})
#     is_active = models.IntegerField()

class Log(models.Model):
    request_date = models.DateTimeField(default=timezone.now)
    domain = models.TextField()
    ping = models.IntegerField()
    response_time = models.IntegerField()
    cert = models.TextField()
    status_code = models.IntegerField()
    status = models.CharField(max_length=50)
    cert_from = models.DateTimeField(null=True)
    cert_to = models.DateTimeField(null=True)
    domain_exp = models.DateTimeField(null=True)
    days_to_domain_exp = models.IntegerField()


    def __str__(self):
        return self.request_date

class StatusPage(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=20)
    # TODO