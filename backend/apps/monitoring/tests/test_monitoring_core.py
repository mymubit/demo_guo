from django.test import SimpleTestCase, override_settings

from apps.monitoring.models import AlertRule
from apps.monitoring.serializers import FrontendEventBatchSerializer
from apps.monitoring.services.alerts import compare_value
from apps.monitoring.services.retention import normalize_monitoring_targets
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


class MonitoringBusinessErrorTests(SimpleTestCase):
    @override_settings(
        MONITORING_BUSINESS_ERROR_SAMPLE_RATE=1,
        MONITORING_VALIDATION_ERROR_SAMPLE_RATE=1,
    )
    def test_parse_business_response_from_json_content(self):
        from django.http import HttpResponse

        from apps.monitoring.services.business_error import parse_business_response

        response = HttpResponse(
            '{"code": 404, "message": "资源未找到", "data": null}',
            content_type="application/json",
        )
        parsed = parse_business_response(response)
        self.assertEqual(parsed, (404, "资源未找到"))

    @override_settings(
        MONITORING_BUSINESS_ERROR_SAMPLE_RATE=1,
        MONITORING_VALIDATION_ERROR_SAMPLE_RATE=1,
    )
    def test_build_business_error_extra_marks_failed_requests(self):
        from apps.monitoring.services.business_error import build_business_error_extra

        extra = build_business_error_extra(4001, "参数错误", slow_api=False)
        self.assertTrue(extra["business_error"])
        self.assertEqual(extra["business_code"], 4001)

    @override_settings(MONITORING_VALIDATION_ERROR_SAMPLE_RATE=0)
    def test_validation_error_sampling_can_be_disabled(self):
        from apps.monitoring.services.business_error import should_sample_business_error

        from apps.common.exceptions import VALIDATION_ERROR

        self.assertFalse(should_sample_business_error(VALIDATION_ERROR))


class MonitoringTaskErrorTests(SimpleTestCase):
    def test_build_task_failure_extra_keeps_execution_context(self):
        from apps.monitoring.services.task_error import build_task_failure_extra

        extra = build_task_failure_extra(
            task_name="creation.skill_task",
            project_id="project-1",
            node_index=2,
            status="failed",
            detail={"error": "Agent runner 未配置", "execution_run_id": "run-1"},
        )

        self.assertTrue(extra["task_error"])
        self.assertEqual(extra["task_name"], "creation.skill_task")
        self.assertEqual(extra["project_id"], "project-1")
        self.assertEqual(extra["node_index"], 2)
        self.assertEqual(extra["execution_run_id"], "run-1")


class MonitoringRetentionTests(SimpleTestCase):
    def test_normalize_monitoring_targets_filters_unknown_values(self):
        result = normalize_monitoring_targets(["exceptions", "unknown", "slow_sql", "exceptions"])

        self.assertEqual(result, ["exceptions", "slow_sql"])

    def test_normalize_monitoring_targets_defaults_to_all(self):
        result = normalize_monitoring_targets([])

        self.assertIn("exceptions", result)
        self.assertIn("api_performance", result)
