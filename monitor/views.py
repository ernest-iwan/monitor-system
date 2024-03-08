from django.shortcuts import render
from django.template.defaulttags import register

from .models import Monitor, StatusPage


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


def status(request, slug):
    status_object = StatusPage.objects.get(slug=slug)
    monitors_status = True

    for elements in status_object.monitors.all():
        if elements.status == "online":
            monitors_status = True
        else:
            monitors_status = False
            break

    context = {
        "slug": slug,
        "status_object": status_object,
        "monitors_status": monitors_status,
    }
    return render(request, "status.html", context)


def monitor(request, monitor_id):
    monitor = Monitor.objects.get(id=monitor_id)

    context = {"monitor": monitor}
    return render(request, "monitor.html", context)
