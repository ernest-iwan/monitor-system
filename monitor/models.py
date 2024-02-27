from django.conf import settings
from django.db import models
from django.utils import timezone


class Log(models.Model):
    request_date = models.DateTimeField(default=timezone.now)
    domain = models.TextField()
    ping = models.IntegerField()
    response_time = models.IntegerField()
    cert = models.TextField()
    status_code = models.IntegerField()
    status = models.CharField(max_length=50)
    cert_from = models.DateTimeField()
    cert_to = models.DateTimeField()
    domain_exp = models.DateTimeField()
    days_to_domain_exp = models.IntegerField()


    def __str__(self):
        return self.request_date
