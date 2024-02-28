from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _



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
    url = models.CharField(_("URL"), max_length=100, null=True)
    domain_or_ip = models.CharField(_("Domena lub IP"), max_length=100, null=True)


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
    request_date = models.DateTimeField("Data zapytania" ,auto_now_add=True)
    domain = models.TextField("Domena")
    ping = models.IntegerField("Ping")
    response_time = models.IntegerField("Czas odpowiedzi")
    cert = models.TextField("Certyfikat")
    status_code = models.IntegerField("Numer Statusu")
    status = models.CharField("Status",max_length=50)
    cert_from = models.DateTimeField("Certyfikat ważny od", null=True)
    cert_to = models.DateTimeField("Certyfikat ważny do", null=True)
    domain_exp = models.DateTimeField("Domena wygasa", null=True)
    days_to_domain_exp = models.IntegerField("Dni do wygaśnięcia domeny")

    class Meta:
        ordering = ["request_date"]
        verbose_name = "Log"
        verbose_name_plural = "Logi"

    def __str__(self):
        return _(f"{self.request_date} - {self.domain} - ({self.status})")

class StatusPage(models.Model):
    name = models.CharField("Nazwa", max_length=100)
    slug = models.SlugField()
    # TODO