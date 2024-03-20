from django.contrib import admin

from .models import ApiRequest, Email, EmailValues, Log, Monitor, StatusPage


# Admin view used as inline formset in Monitor admin view
class EmailValuesInline(admin.TabularInline):
    model = EmailValues
    extra = 1


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ("name", "monitor_type", "add_date", "status", "is_active")
    list_filter = ("monitor_type", "add_date", "is_active")
    search_fields = ("name",)
    fieldsets = [
        (
            "Dane",
            {
                "fields": [
                    "name",
                    "monitor_type",
                    "request_timeout",
                    "interval",
                    "status",
                    "is_active",
                    "value_to_check",
                    "ssl_monitor",
                    "days_before_exp",
                ]
            },
        ),
    ]
    inlines = [EmailValuesInline]


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    readonly_fields = [field.name for field in Log._meta.get_fields()]
    list_display = (
        "request_date",
        "monitor",
        "ping",
        "response_time",
        "status",
        "days_to_ssl_exp",
    )
    list_filter = ("request_date", "monitor")
    search_fields = ("monitor_id", "status")


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("email",)
    list_filter = ("email",)
    search_fields = ("email",)


@admin.register(StatusPage)
class StatusPageAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    list_filter = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(ApiRequest)
class ApiRequestAdmin(admin.ModelAdmin):
    readonly_fields = [field.name for field in ApiRequest._meta.get_fields()]
    list_display = ("request_date", "monitor")
    list_filter = ("request_date", "monitor")
    search_fields = ("monitor",)
