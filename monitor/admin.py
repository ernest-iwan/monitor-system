from django.contrib import admin
from .models import *

@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ("name", "monitor_type", "add_date", "status", "is_active")
    list_filter = ("monitor_type", "add_date", "is_active")
    search_fields = ("name",)

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    readonly_fields = [field.name for field in Log._meta.get_fields()]
    list_display = ("request_date", "domain", "ping", "response_time", "status")
    list_filter = ("request_date", "domain")
    search_fields = ("domain", "status")

# @admin.register(StatusPage)
# class StatusPageAdmin(admin.ModelAdmin):
#     list_display = ("request_date", "domain", "ping", "response_time", "status")
#     list_filter = ("request_date", "domain")
#     search_fields = ("domain", "status")
