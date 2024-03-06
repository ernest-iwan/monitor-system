from django.db import models
from django.utils.translation import gettext as _
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import timedelta, datetime
from collections import OrderedDict
import json
import tzlocal


class Email(models.Model):
    email = models.CharField(_("Email"), max_length=100)

    class Meta:
        ordering = ["email"]
        verbose_name = _("Email")
        verbose_name_plural = _("Emaile")

    def __str__(self):
        return self.email

class Monitor(models.Model):
    TYPE_HTTP = "http_request"
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
    request_timeout = models.FloatField(_("Czas oczekiwania na żądanie"))
    interval = models.FloatField(_("Interwał"))
    add_date = models.DateTimeField(_("Data dodania"), auto_now_add=True)
    status = models.CharField(_("Status"), max_length=15, choices=STATUSES, default=STATUS_ONLINE)
    is_active = models.BooleanField(_("Czy aktywny?"))
    emails = models.ManyToManyField(Email, verbose_name=_("Emaile"))
    value_to_check = models.CharField(_("URL lub IP"), max_length=100, null=True)
    ssl_monitor = models.BooleanField(_("Monitorować SSL?"), default=False)
    days_before_exp = models.IntegerField(_("Ile dni przed poinformować?"), null=True)

    class Meta:
        ordering = ['add_date']
        verbose_name = _("Monitor")
        verbose_name_plural = _("Monitory")
    def get_logs(self):
        thirty_days_ago = datetime.now(tzlocal.get_localzone()) - timedelta(days=30)
        logs = Log.objects.filter(monitor=self, request_date__gte=thirty_days_ago)

        data = OrderedDict()
        for log in logs:
            log_date = log.request_date.date()
            if log_date not in data:
                data[log_date] = {"total": 0, "online": 0}

            data[log_date]["total"] += 1
            if log.status == "Successful responses":
                data[log_date]["online"] += 1

        thirty_days_range = [thirty_days_ago + timedelta(days=i) for i in range(31)]
        for date in thirty_days_range:
            if date.date() not in data:
                data[date.date()] = {"total": -1, "online": -1}

        for date, values in data.items():
            if values["total"] > 0:
                availability_percentage = (values["online"] / values["total"]) * 100
                data[date] = round(availability_percentage, 2)
            else:
                data[date] = -1

        sorted_data = OrderedDict(sorted(data.items()))
        return sorted_data
    def __str__(self):
        return f"{self.name} - {self.monitor_type} - ({self.status})"


class EmailValues(models.Model):
    monitor = models.ForeignKey(Monitor, verbose_name=_("Monitor"), on_delete=models.CASCADE)
    email = models.ForeignKey(Email, verbose_name=_("Email"), on_delete=models.PROTECT)

    class Meta:
        ordering = ["email"]
        verbose_name = _("Emaile")

    def __str__(self):
        return f"{self.email} - {self.monitor.name}"


class Log(models.Model):
    request_date = models.DateTimeField(_("Data zapytania"), auto_now_add=True)
    monitor = models.ForeignKey(Monitor, verbose_name=_("Monitor"), on_delete=models.CASCADE)
    ping = models.IntegerField(_("Ping"), null=True)
    response_time = models.IntegerField(_("Czas odpowiedzi"), null=True)
    status_code = models.IntegerField(_("Numer Statusu"), null=True)
    status = models.CharField(_("Status"), max_length=50, null=True)
    cert_from = models.DateTimeField(_("Certyfikat ważny od"), null=True)
    cert_to = models.DateTimeField(_("Certyfikat ważny do"), null=True)
    domain_exp = models.DateTimeField(_("Domena wygasa"), null=True)
    days_to_domain_exp = models.IntegerField(_("Dni do wygaśnięcia domeny"), null=True)
    days_to_ssl_exp = models.IntegerField(_("Dni do wygaśnięcia certyfikatu ssl"), null=True)

    class Meta:
        ordering = ["-request_date"]
        verbose_name = _("Log")
        verbose_name_plural = _("Logi")

    def __str__(self):
        return f"{self.request_date} - {self.monitor} - ({self.status})"


class StatusPage(models.Model):
    name = models.CharField(_("Nazwa"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True, max_length=20)
    monitors = models.ManyToManyField(Monitor, verbose_name=_("Monitory"))

    class Meta:
        ordering = ["-name"]
        verbose_name = "Status strony"
        verbose_name_plural = "Statusy stron"

    def __str__(self):
        return f"{self.name} - {self.slug}"


@receiver(post_delete, sender=Monitor)
def notification_handler(sender, instance, **kwargs):
    task = PeriodicTask.objects.get(
        name=f'monitor {instance.id}',
    )
    task.delete()
    task2 = PeriodicTask.objects.get(
        name=f'ssl monitor {instance.id}',
    )
    task2.delete()


@receiver(post_save, sender=Monitor)
def notification_handler(sender, instance, created, **kwargs):
    if created:
        interval, created = IntervalSchedule.objects.get_or_create(every=instance.interval,
                                                                   period=IntervalSchedule.SECONDS, )

        if instance.monitor_type == "http_request":
            task = PeriodicTask.objects.get_or_create(
                interval=interval,
                name=f'monitor {instance.id}',
                task='config.celery.collect_data_url',
                enabled=instance.is_active,
                args=json.dumps([instance.value_to_check, instance.request_timeout, instance.id]),
            )

            if instance.ssl_monitor:
                interval, created = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.DAYS, )
                task = PeriodicTask.objects.get_or_create(
                    interval=interval,
                    name=f'ssl monitor {instance.id}',
                    task='config.celery.ssl_monitor',
                    enabled=instance.is_active,
                    args=json.dumps(
                        [instance.value_to_check, instance.request_timeout, instance.id, instance.days_before_exp]),
                )

        elif instance.monitor_type == "ping":
            task = PeriodicTask.objects.get_or_create(
                interval=interval,
                name=f'monitor {instance.id}',
                task='config.celery.collect_data_ping',
                enabled=instance.is_active,
                args=json.dumps([instance.value_to_check, instance.request_timeout, instance.id]),
            )

    if not created:
        task = PeriodicTask.objects.get(
            name=f'monitor {instance.id}',
        )
        task.args = json.dumps([instance.value_to_check, instance.request_timeout, instance.id])
        task.enabled = instance.is_active

        if instance.monitor_type == "http_request":
            task.task = 'config.celery.collect_data_url'
            task2 = PeriodicTask.objects.get(
                name=f'ssl monitor {instance.id}',
            )
            task2.args = json.dumps(
                [instance.value_to_check, instance.request_timeout, instance.id, instance.days_before_exp])
            task2.enabled = instance.ssl_monitor
            task2.save()
        elif instance.monitor_type == "ping":
            task.task = 'config.celery.collect_data_ping'

        task.save()
