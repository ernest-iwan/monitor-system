from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Log, Monitor


class MonitorModelTest(TestCase):
    def test_monitor_creation(self):
        monitor = Monitor.objects.create(
            name="Test Website",
            value_to_check="https://example.com",
            request_timeout=5,
            interval=10,
            is_active=True,
        )
        self.assertEqual(monitor.name, "Test Website")
        self.assertEqual(monitor.value_to_check, "https://example.com")


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


class MonitorIntegrationTest(TestCase):
    def test_monitor_status_update(self):
        monitor = Monitor.objects.create(
            name="Test Website",
            value_to_check="http://example.com",
            request_timeout=5,
            interval=10,
            is_active=True,
        )
        Log.objects.create(monitor=monitor, status_code=200, status="OK")

        # Simulate another log entry after 1 minute with error status
        future_time = timezone.now() + timedelta(minutes=1)
        Log.objects.create(
            monitor=monitor,
            status_code=404,
            status="Not Found",
            request_date=future_time,
        )

        # Retrieve the monitor and check its status
        updated_monitor = Monitor.objects.get(id=monitor.id)
        self.assertEqual(updated_monitor.status, "online")
