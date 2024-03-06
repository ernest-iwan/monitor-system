from django.contrib import admin

from .models import Email, EmailValues, Monitor, Log, StatusPage


class EmailValuesInline(admin.TabularInline):
    model = EmailValues
    extra = 1


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ("name", "monitor_type", "add_date", "status", "is_active")
    list_filter = ("monitor_type", "add_date", "is_active")
    search_fields = ("name",)
    fieldsets = [('Dane', {
        'fields': ['name', 'monitor_type', 'request_timeout', 'interval', 'status', 'is_active', 'value_to_check',
                   'ssl_monitor', 'days_before_exp']}), ]
    inlines = [EmailValuesInline]


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    readonly_fields = [field.name for field in Log._meta.get_fields()]
    list_display = ("request_date", "monitor", "ping", "response_time", "status", "days_to_ssl_exp")
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
    # inlines = [Monitor]

# class MenuAdmin(admin.ModelAdmin):
#     # ...
#     class Media:
#         js = ('/static/admin/js/hide_attribute.js')

# class MonitorInline(admin.StackedInline): model = Monitor extra = 1 list_display = ("name", "monitor_type",
# "add_date", "status", "is_active") list_filter = ("monitor_type", "add_date", "is_active") search_fields = ("name",
# ) fieldsets = [('Dane', {'fields': ['name', 'monitor_type', 'request_timeout', 'interval', 'status', 'is_active',
# 'value_to_check']}),]


# @admin.register(StatusPage)
# class StatusPageAdmin(admin.ModelAdmin):
#     list_display = ("request_date", "domain", "ping", "response_time", "status")
#     list_filter = ("request_date", "domain")
#     search_fields = ("domain", "status")
