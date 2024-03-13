from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Log, Monitor, StatusPage


class ModelsTests(TestCase):
    def setUp(self):
        self.monitor = Monitor.objects.create(
            name="Test Website",
            value_to_check="https://example.com",
            request_timeout=5,
            interval=10,
            is_active=True,
        )

        self.log = Log.objects.create(
            monitor=self.monitor,
            status="Successful responses",
            ping=10,
            response_time=94,
        )

        self.status_page = StatusPage.objects.create(
            name="Test Status Page",
            monitors=self.monitor,
            slug="test",
        )

    def test_monitor_creation(self):
        self.assertEqual(self.monitor.name, "Test Website")
        self.assertEqual(self.monitor.value_to_check, "https://example.com")
        self.assertEqual(self.monitor.request_timeout, 5)
        self.assertEqual(self.monitor.interval, 10)
        self.assertEqual(self.monitor.is_active, True)

    def test_log_creation(self):
        self.assertEqual(self.log.monitor, self.monitor)
        self.assertEqual(self.log.status, "Successful responses")
        self.assertEqual(self.log.response_time, 94)
        self.assertEqual(self.log.is_active, True)

    def test_status_page_creation(self):
        self.assertEqual(self.status_page.monitors, self.monitor)
        self.assertEqual(self.status_page.name, "Test Status Page")
        self.assertEqual(self.status_page.slug, "test")


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


class MonitorLogModelTest(TestCase):
    def test_log_creation(self):
        monitor = Monitor.objects.create(
            name="Test Website",
            value_to_check="http://example.com",
            request_timeout=5,
            interval=10,
            is_active=True,
        )
        log = Log.objects.create(monitor=monitor, status_code=200, status="OK")
        self.assertEqual(log.monitor, monitor)
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.status, "OK")


class StatusPageModelTest(TestCase):
    def test_log_creation(self):
        monitor = Monitor.objects.create(
            name="Test Website",
            value_to_check="http://example.com",
            request_timeout=5,
            interval=10,
            is_active=True,
        )
        log = Log.objects.create(monitor=monitor, status_code=200, status="OK")
        self.assertEqual(log.monitor, monitor)
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.status, "OK")


class MonitorIntegrationTest(TestCase):
    def test_monitor_status_update(self):
        monitor = Monitor.objects.create(
            name="Test Website",
            value_to_check="http://example.com",
            request_timeout=5,
            interval=10,
            is_active=True,
        )
        Log.objects.create(monitor=monitor, status_code=200, status="Successful responses")

        future_time = timezone.now() + timedelta(minutes=1)
        Log.objects.create(
            monitor=monitor,
            status_code=404,
            status="Not Found",
            request_date=future_time,
        )

        updated_monitor = Monitor.objects.get(id=monitor.id)
        self.assertEqual(updated_monitor.status, "online")
