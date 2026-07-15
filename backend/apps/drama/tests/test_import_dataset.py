# -*- coding: utf-8 -*-
"""真实数据导入命令测试。"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.drama.models import DramaProject
from apps.drama.tests.helpers import FIXTURE_SETTINGS, create_user

SKILLS_ROOT = str(Path(__file__).resolve().parents[4] / "drama-skills")


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class ImportDramaDatasetTests(TestCase):
    def test_dry_run_validates_without_persisting(self) -> None:
        user = create_user(username="import-owner")
        settings = dict(FIXTURE_SETTINGS)
        settings["title"] = "真实数据导入测试"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dataset.json"
            path.write_text(
                json.dumps(
                    {"projects": [{"settings": settings, "artifacts": []}]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            call_command(
                "import_drama_dataset",
                str(path),
                owner=user.username,
                dry_run=True,
            )
        self.assertEqual(DramaProject.objects.count(), 0)
