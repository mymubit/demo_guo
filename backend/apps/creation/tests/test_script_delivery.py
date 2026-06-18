"""创作交付单元测试。"""
import os
import shutil
import tempfile
from unittest.mock import patch

from django.test import TestCase

from apps.creation.models import Project, ScriptWork
from apps.creation.script_delivery import (
    build_script_display_html,
    build_script_markdown,
    persist_script_works,
    resolve_scripts,
)
from apps.users.models import User


class ScriptDeliveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900001111", password="TestPass123!")
        self.project = Project.objects.create(
            user=self.user,
            title="测试剧本",
            theme="urban-counterattack",
            core_idea="逆袭故事",
            episode_count=2,
            format_variant="B",
            status=Project.STATUS_COMPLETED,
        )

    def test_resolve_scripts_from_pipeline_result(self):
        pipeline = {
            "scripts": {
                "episodes": [
                    {"episode": 1, "title": "开局", "full_script_text": "## 第1集\n\n对白内容"},
                ]
            }
        }
        scripts = resolve_scripts(self.project, pipeline)
        self.assertEqual(len(scripts["episodes"]), 1)
        self.assertIn("对白内容", scripts["episodes"][0]["full_script_text"])

    def test_resolve_scripts_from_artifacts(self):
        pipeline = {
            "artifacts": {
                "episode_scripts": {
                    "episodes": [
                        {
                            "episodeNumber": 1,
                            "title": "第一集",
                            "scenes": [
                                {
                                    "sceneNumber": "1-1",
                                    "location": "客厅",
                                    "actions": [{"content": "女主进门"}],
                                    "dialogues": [{"speaker": "林晚", "line": "我回来了"}],
                                }
                            ],
                        }
                    ]
                }
            }
        }
        scripts = resolve_scripts(self.project, pipeline)
        self.assertEqual(scripts["total_episodes"], 1)
        self.assertIn("林晚", scripts["episodes"][0]["full_script_text"])

    def test_build_script_markdown_contains_body(self):
        pipeline = {
            "scripts": {
                "episodes": [
                    {"episode": 1, "full_script_text": "# 第1集\n\n场景一"},
                ]
            }
        }
        md = build_script_markdown(self.project, pipeline, watermark_token="wm-test")
        self.assertIn("测试剧本", md)
        self.assertIn("场景一", md)
        self.assertIn("wm-test", md)

    def test_build_script_display_html_escapes_html(self):
        pipeline = {
            "scripts": {
                "episodes": [
                    {"episode": 1, "full_script_text": "<script>alert(1)</script>"},
                ]
            }
        }
        html = build_script_display_html(self.project, pipeline)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    @patch("apps.creation.script_delivery.settings")
    def test_persist_script_works_writes_files(self, mock_settings):
        workspace_tmp = os.path.abspath(os.path.join(os.getcwd(), ".test_tmp"))
        os.makedirs(workspace_tmp, exist_ok=True)
        tmp_root = tempfile.mkdtemp(prefix="scriptforge_script_test_", dir=workspace_tmp)
        self.addCleanup(shutil.rmtree, tmp_root, ignore_errors=True)
        mock_settings.CREATION_SCRIPT_DIR = tmp_root
        pipeline = {
            "scripts": {
                "episodes": [
                    {"episode": 1, "full_script_text": "# 第1集\n\n正文段落"},
                ]
            }
        }
        persist_script_works(self.project, pipeline)
        self.project.refresh_from_db()
        self.assertIn("creation-script-result", self.project.rendered_result_html)
        self.assertTrue(
            ScriptWork.objects.filter(project=self.project, file_format=ScriptWork.FORMAT_MARKDOWN).exists()
        )
        project_dir = os.path.join(tmp_root, self.project.id.hex)
        self.assertTrue(os.path.isdir(project_dir))
        self.assertTrue(any(name.endswith(".md") for name in os.listdir(project_dir)))
