# -*- coding: utf-8 -*-
import zipfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.artifact_service import save_artifact
from apps.creation.models import Project
from apps.creation.script_export import (
    build_work_html,
    build_work_markdown,
    build_work_zip,
    project_has_exportable_content,
)

User = get_user_model()


class ScriptExportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900004404", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="导出测试",
            theme="sweet-pet",
            episode_count=2,
            pipeline_mode=Project.MODE_WORKSPACE,
        )
        save_artifact(
            self.project,
            "project_brief",
            {"workingTitle": "导出测试", "theme": "sweet-pet", "episodeCount": 2},
        )
        save_artifact(
            self.project,
            "episode_scripts",
            {
                "episodes": [
                    {
                        "episodeNumber": 1,
                        "title": "开局",
                        "full_script_text": "## 第1集\n\n场景一",
                    }
                ]
            },
        )

    def test_project_has_exportable_content(self):
        self.assertTrue(project_has_exportable_content(self.project))

    def test_build_work_markdown(self):
        md = build_work_markdown(self.project)
        self.assertIn("导出测试", md)
        self.assertIn("sweet-pet", md)

    def test_build_work_html(self):
        html = build_work_html(self.project, watermark_token="wm-test")
        self.assertIn("<html", html.lower())
        self.assertIn("导出测试", html)

    def test_build_work_zip_contains_files(self):
        data = build_work_zip(self.project)
        self.assertTrue(data)
        with zipfile.ZipFile(BytesIO(data)) as zf:
            names = set(zf.namelist())
            self.assertIn("00-full-work.md", names)
            self.assertTrue(names & {"01-project-brief.md", "05-episode-scripts.md"})
