from django.test import SimpleTestCase, override_settings

from apps.monitoring.models import AlertRule
from apps.monitoring.serializers import FrontendEventBatchSerializer
from apps.monitoring.services.alerts import compare_value
from apps.monitoring.services.sanitizer import compact_sql, sanitize_payload


class MonitoringSanitizerTests(SimpleTestCase):
    def test_sanitize_payload_masks_sensitive_fields(self):
        payload = {
            "password": "secret",
            "token": "abc",
            "phone": "13812345678",
            "email": "demo@example.com",
        }

        result = sanitize_payload(payload)

        self.assertEqual(result["password"], "***")
        self.assertEqual(result["token"], "***")
        self.assertEqual(result["phone"], "138****5678")
        self.assertEqual(result["email"], "de***@example.com")

    def test_compact_sql_masks_literals_and_numbers(self):
        sql = "SELECT * FROM users WHERE phone = '13812345678' AND id = 123"

        result = compact_sql(sql)

        self.assertIn("'?'", result)
        self.assertNotIn("13812345678", result)
        self.assertNotIn("123", result)


class MonitoringSerializerTests(SimpleTestCase):
    @override_settings(MONITORING_MAX_BATCH_SIZE=2, MONITORING_MAX_PAYLOAD_SIZE=1024)
    def test_frontend_event_batch_accepts_valid_events(self):
        serializer = FrontendEventBatchSerializer(
            data={
                "events": [
                    {
                        "type": "custom",
                        "name": "button_click",
                        "route": "/admin/monitoring",
                        "payload": {"action": "refresh"},
                    }
                ]
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    @override_settings(MONITORING_MAX_BATCH_SIZE=1, MONITORING_MAX_PAYLOAD_SIZE=1024)
    def test_frontend_event_batch_rejects_too_many_events(self):
        serializer = FrontendEventBatchSerializer(
            data={
                "events": [
                    {"type": "custom", "name": "a"},
                    {"type": "custom", "name": "b"},
                ]
            }
        )

        self.assertFalse(serializer.is_valid())


class MonitoringAlertTests(SimpleTestCase):
    def test_compare_value_supports_all_comparators(self):
        self.assertTrue(compare_value(2, AlertRule.Comparator.GT, 1))
        self.assertTrue(compare_value(2, AlertRule.Comparator.GTE, 2))
        self.assertTrue(compare_value(1, AlertRule.Comparator.LT, 2))
        self.assertTrue(compare_value(2, AlertRule.Comparator.LTE, 2))
        self.assertFalse(compare_value(1, AlertRule.Comparator.GT, 2))
