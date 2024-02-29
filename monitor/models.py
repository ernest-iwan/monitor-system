from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import json


class StatusPage(models.Model):
    name = models.CharField(_("Nazwa"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True, max_length=20)
    # TODO

class Email(models.Model):
    email = models.CharField(_("Email"), max_length=100)

    class Meta:
        ordering = ["email"]
        verbose_name = "Email"
    
    def __str__(self):
        return _(f"{self.email}")

class Monitor(models.Model):
    TYPE_HTTP = "http request"
    TYPE_PING = "ping"
    TYPE_CRONE = "cron job"

    TYPES = (
        (TYPE_HTTP, _("Zapytanie HTTP")),
        (TYPE_PING, _("Ping")),
        (TYPE_CRONE, _("Crone Job")),
    )

    STATUS_ONLINE = "online"
    STATUS_OFFLINE = "offline"

    STATUSES = (
        (STATUS_ONLINE, _("Online")),
        (STATUS_OFFLINE, _("Offline")),
    )

    name = models.CharField("Nazwa", max_length=100)
    monitor_type = models.CharField(_("Typ monitorowania"), max_length=15, choices=TYPES, default=TYPE_HTTP)
    request_timeout = models.FloatField(_("Czas oczekiwania na rządanie"))
    interval = models.FloatField(_("Interwał"))
    add_date = models.DateTimeField(_("Data dodania"), auto_now_add=True)
    status = models.CharField(_("Status"), max_length=15, choices=STATUSES, default=STATUS_ONLINE)
    is_active = models.BooleanField(_("Czy aktywny?"))
    emails = models.ManyToManyField(Email, verbose_name=_("Emaile"))
    value_to_check = models.CharField(_("URL lub IP"), max_length=100, null=True)
    ssl_monitor = models.BooleanField(_("Monitorować SSL?"), default=False)


    class Meta:
        ordering = ['add_date']
        verbose_name = "Monitor"
        verbose_name_plural = "Monitory"

    def __str__(self):
        return _(f"{self.name} - {self.monitor_type} - ({self.status})")

class EmailValues(models.Model):
    monitor_id = models.ForeignKey(Monitor, verbose_name=_("ID Monitora"), on_delete=models.CASCADE)
    email  = models.ForeignKey(Email, verbose_name=_("Email"), on_delete=models.PROTECT)

    class Meta:
        ordering = ["email"]
        verbose_name = "Emaile"
    
    def __str__(self):
        return _(f"{self.email} - {self.monitor_id}")

class Log(models.Model):
    request_date = models.DateTimeField(_("Data zapytania") ,auto_now_add=True)
    monitor_id = models.ForeignKey(Monitor, verbose_name=_("ID Monitora"), on_delete=models.CASCADE)
    ping = models.IntegerField(_("Ping"), null=True)
    response_time = models.IntegerField(_("Czas odpowiedzi"), null=True)
    status_code = models.IntegerField(_("Numer Statusu"), null=True)
    status = models.CharField(_("Status"),max_length=50)
    cert_from = models.DateTimeField(_("Certyfikat ważny od"), null=True)
    cert_to = models.DateTimeField(_("Certyfikat ważny do"), null=True)
    domain_exp = models.DateTimeField(_("Domena wygasa"), null=True)
    days_to_domain_exp = models.IntegerField(_("Dni do wygaśnięcia domeny"), null=True)

    class Meta:
        ordering = ["-request_date"]
        verbose_name = "Log"
        verbose_name_plural = "Logi"

    def __str__(self):
        return _(f"{self.request_date} - {self.monitor_id} - ({self.status})")


@receiver(post_delete,sender=Monitor)
def notification_handler(sender, instance, **kwargs):
    task = PeriodicTask.objects.get(
            name=f'monitor {instance.id}', 
    )
    task.delete()

@receiver(post_save,sender=Monitor)
def notification_handler(sender, instance, created, **kwargs):
    if created:
        interval, created = IntervalSchedule.objects.get_or_create(every=instance.interval, period=IntervalSchedule.SECONDS,)
        if instance.monitor_type == "http request":
            task = PeriodicTask.objects.get_or_create(
                interval=interval, 
                name=f'monitor {instance.id}', 
                task='mysite.celery.collect_data_url',
                enabled = instance.is_active,
                args=json.dumps([instance.value_to_check, instance.request_timeout, instance.id]),
            )
        elif instance.monitor_type == "ping":
            task = PeriodicTask.objects.get_or_create(
                interval=interval, 
                name=f'monitor {instance.id}', 
                task='mysite.celery.collect_data_ping',
                enabled = instance.is_active,
                args=json.dumps([instance.value_to_check, instance.request_timeout, instance.id]),
            )
    if not created:
        task = PeriodicTask.objects.get(
            name=f'monitor {instance.id}', 
        )
        task.args=json.dumps([instance.value_to_check, instance.request_timeout, instance.id])
        task.enabled = instance.is_active
        if instance.monitor_type == "http request":
            task.task='mysite.celery.collect_data_url'
        elif instance.monitor_type == "ping":
            task.task='mysite.celery.collect_data_ping'
        task.save()