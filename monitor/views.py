from django.http import HttpResponse
from django.shortcuts import render

from .models import ApiRequest, Monitor, StatusPage


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


def crone(request, monitor_id):
    monitor = Monitor.objects.get(id=monitor_id)
    ApiRequest.objects.create(monitor=monitor)
    return HttpResponse(status=204)
