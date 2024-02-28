from django.contrib import admin
from .models import *
from django.forms import BaseInlineFormSet


class EmailValuesInline(admin.TabularInline):
    model = EmailValues
    extra = 1

@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ("name", "monitor_type", "add_date", "status", "is_active")
    list_filter = ("monitor_type", "add_date", "is_active")
    search_fields = ("name",)
    fieldsets = [('Dane', {'fields': ['name', 'monitor_type', 'request_timeout', 'interval', 'status', 'is_active']}),]
    # TODO url or ip or domain
    inlines = [EmailValuesInline]


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    readonly_fields = [field.name for field in Log._meta.get_fields()]
    list_display = ("request_date", "domain", "ping", "response_time", "status")
    list_filter = ("request_date", "domain")
    search_fields = ("domain", "status")

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("email",)
    list_filter = ("email",)
    search_fields = ("email",)
    
# class PersonAdmin(admin.ModelAdmin):
#     list_display = ('lastName', 'firstName','email')
#     fieldsets = [
#        ('Name',        {'fields': ['firstName', 'lastName']}),
#        ('Contact Info',{'fields': ['email','phoneNumber']})
#     ]
#     inlines = [EmailInline]
# admin.site.register(Person, PersonAdmin)
# admin.site.register(Attribute)

# @admin.register(StatusPage)
# class StatusPageAdmin(admin.ModelAdmin):
#     list_display = ("request_date", "domain", "ping", "response_time", "status")
#     list_filter = ("request_date", "domain")
#     search_fields = ("domain", "status")

