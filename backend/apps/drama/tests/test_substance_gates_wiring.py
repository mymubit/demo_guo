# -*- coding: utf-8 -*-
"""GenerationService 实质门禁接线回归。"""
from __future__ import annotations

import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.core.exceptions import SCHEMA_VALIDATION_FAILED, BusinessException
from apps.drama.services.generation_service import GenerationService
from apps.drama.tests.helpers import FIXTURE_SETTINGS, SKILLS_ROOT

_QUALITY_DIM_KEYS = (
    "format",
    "narrative",
    "conflict",
    "character",
    "emotion",
    "logic",
    "satisfaction",
    "hooks",
    "paywall",
    "genre_fit",
)

_QUALITY_SCHEMA = "schemas/artifacts/quality_report/1.schema.json"
_COMPLIANCE_SCHEMA = "schemas/artifacts/compliance_report/1.schema.json"


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class SubstanceGatesWiringTests(SimpleTestCase):
    def setUp(self) -> None:
        self.svc = GenerationService()

    def test_quality_report_sparse_hits_evidence_substance_gate(self) -> None:
        sparse = {
            "drama_title": "边关开荒",
            "overall_score": 82,
            "dimensions": {key: {"score": 80} for key in _QUALITY_DIM_KEYS},
        }
        content = json.dumps(sparse, ensure_ascii=False)

        with patch.object(self.svc.validator, "validate_file") as mock_validate:
            with self.assertRaises(BusinessException) as ctx:
                self.svc._parse_normalize_validate(
                    content=content,
                    artifact_key="quality_report",
                    settings=FIXTURE_SETTINGS,
                    schema_path=_QUALITY_SCHEMA,
                )

        mock_validate.assert_called_once()
        self.assertEqual(ctx.exception.code, SCHEMA_VALIDATION_FAILED)
        self.assertIn("十维评分缺少有效 evidence", ctx.exception.message)

    def test_compliance_report_thin_hits_substance_gate(self) -> None:
        thin = {
            "drama_title": "测试剧",
            "overall_result": "不通过",
            "blocking_issues": [{"description": ""}],
            "risk_items": [],
        }
        content = json.dumps(thin, ensure_ascii=False)

        with self.assertRaises(BusinessException) as ctx:
            self.svc._parse_normalize_validate(
                content=content,
                artifact_key="compliance_report",
                settings=FIXTURE_SETTINGS,
                schema_path=_COMPLIANCE_SCHEMA,
            )

        self.assertEqual(ctx.exception.code, SCHEMA_VALIDATION_FAILED)
        self.assertIn(
            "合规报告缺少具体阻断/风险描述（title+description）",
            ctx.exception.message,
        )
