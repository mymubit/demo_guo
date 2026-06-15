# -*- coding: utf-8 -*-
from django.test import SimpleTestCase, override_settings

from apps.skill.llm.volcengine_config import (
    VOLCANO_KEY_CODING_PLAN,
    VOLCANO_KEY_PAYG,
    effective_volcano_base_url,
    get_volcano_coding_base_url,
    get_volcano_payg_base_url,
    infer_volcano_key_type,
    resolve_volcano_base_url,
)


class VolcanoConfigTests(SimpleTestCase):
    @override_settings(
        VOLCANO_ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3",
        VOLCANO_ARK_CODING_BASE_URL="https://ark.cn-beijing.volces.com/api/coding/v3",
    )
    def test_resolve_and_infer(self):
        self.assertEqual(
            resolve_volcano_base_url(VOLCANO_KEY_CODING_PLAN),
            "https://ark.cn-beijing.volces.com/api/coding/v3",
        )
        self.assertEqual(
            resolve_volcano_base_url(VOLCANO_KEY_PAYG),
            "https://ark.cn-beijing.volces.com/api/v3",
        )
        self.assertEqual(
            infer_volcano_key_type("https://ark.cn-beijing.volces.com/api/coding/v3"),
            VOLCANO_KEY_CODING_PLAN,
        )
        self.assertEqual(
            infer_volcano_key_type("https://ark.cn-beijing.volces.com/api/v3"),
            VOLCANO_KEY_PAYG,
        )

    @override_settings(
        VOLCANO_ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3",
        VOLCANO_ARK_CODING_BASE_URL="https://ark.cn-beijing.volces.com/api/coding/v3",
    )
    def test_effective_base_url_prefers_key_type(self):
        self.assertEqual(
            effective_volcano_base_url(
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                key_type=VOLCANO_KEY_CODING_PLAN,
            ),
            get_volcano_coding_base_url(),
        )
        self.assertEqual(
            effective_volcano_base_url(
                base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
                key_type=VOLCANO_KEY_PAYG,
            ),
            get_volcano_payg_base_url(),
        )
