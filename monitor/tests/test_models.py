from django.test import TestCase

from monitor.models import Log, Monitor, StatusPage


class ModelsTests(TestCase):
    def setUp(self):
        self.monitor = Monitor.objects.create(
            name="Test Website",
            value_to_check="https://example.com",
            request_timeout=5,
            interval=10,
            is_active=True,
        )
        self.monitor.save()

        self.log = Log.objects.create(
            monitor=self.monitor,
            status="Successful responses",
            ping=10,
            response_time=94,
        )
        self.log.save()

        self.status_page = StatusPage.objects.create(
            name="Test Status Page",
            slug="test",
        )
        self.status_page.monitors.add(self.monitor)
        self.status_page.save()

    def test_monitor_creation(self):
        self.assertEqual(self.monitor.name, "Test Website")
        self.assertEqual(self.monitor.value_to_check, "https://example.com")
        self.assertEqual(self.monitor.request_timeout, 5)
        self.assertEqual(self.monitor.interval, 10)
        self.assertEqual(self.monitor.is_active, True)

    def test_log_creation(self):
        self.assertEqual(self.log.monitor, self.monitor)
        self.assertEqual(self.log.status, "Successful responses")
        self.assertEqual(self.log.ping, 10)
        self.assertEqual(self.log.response_time, 94)

    def test_status_page_creation(self):
        self.assertEqual(self.status_page.monitors.first(), self.monitor)
        self.assertEqual(self.status_page.name, "Test Status Page")
        self.assertEqual(self.status_page.slug, "test")
