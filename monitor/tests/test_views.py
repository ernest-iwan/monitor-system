from django.test import TestCase
from django.urls import reverse

from monitor.models import Monitor, StatusPage


class MonitorViewsTest(TestCase):
    def test_monitor_detail_page(self):
        monitor = Monitor.objects.create(
            name="Test Website",
            value_to_check="http://example.com",
            request_timeout=5,
            interval=10,
            is_active=True,
        )
        response = self.client.get(reverse("monitor", args=(monitor.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Website")


class StatusPageViewTest(TestCase):
    def test_status_page_view(self):
        monitor = Monitor.objects.create(
            name="Test Website",
            value_to_check="http://example.com",
            request_timeout=5,
            interval=10,
            is_active=True,
        )
        status_page = StatusPage.objects.create(
            name="Test Status Page",
            slug="test",
        )
        status_page.monitors.add(monitor)
        status_page.save()

        response = self.client.get(reverse("status", args=(status_page.slug,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Status Page")
