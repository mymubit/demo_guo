# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.creation.script_normalizer import (
    apply_script_normalizer,
    normalize_episode,
    parse_script_markdown_to_scenes,
)


class ScriptNormalizerTests(SimpleTestCase):
    def test_parse_markdown_with_caret_and_bold_dialogue(self):
        md = """
^ 色调: 冷灰蓝 | 声音: 轮渡引擎轰鸣
跨江渡轮甲板，林晓棠独自凭栏。
**林晓棠** (抬头颤抖): 我尝不出味道了。
【未完待续】
"""
        scenes = parse_script_markdown_to_scenes(md, 1)
        self.assertGreaterEqual(len(scenes), 1)
        self.assertGreaterEqual(len(scenes[0]["dialogues"]), 1)
        self.assertEqual(scenes[0]["dialogues"][0]["speaker"], "林晓棠")
        self.assertTrue(scenes[0]["sceneNumber"].startswith("1-"))

    def test_normalize_episode_rebuilds_scenes_from_sparse_markdown(self):
        ep = {
            "episodeNumber": 1,
            "title": "开局",
            "scriptMarkdown": "△ 女主进门。\n林晓棠：你回来了。",
        }
        out = normalize_episode(ep)
        self.assertGreaterEqual(len(out["scenes"]), 1)
        self.assertLess(out["wordCount"], 200)
        self.assertIn("1-1 日 内", out["scriptMarkdown"])
        self.assertIn("林晓棠：", out["scriptMarkdown"])
        self.assertNotIn("这件事还没完", out["scriptMarkdown"])

    def test_strips_legacy_placeholder_lines(self):
        lines = [
            "1-1 日 内 客厅",
            "△ 林晓棠进门。",
            "林晓棠：你回来了。",
        ]
        lines.extend(
            f"林晓棠：这件事还没完，我会查到底。（{i}）" for i in range(1, 40)
        )
        ep = {
            "episodeNumber": 1,
            "title": "第一集",
            "scriptMarkdown": "\n".join(lines),
        }
        out = normalize_episode(ep)
        self.assertNotIn("这件事还没完", out["scriptMarkdown"])
        self.assertLess(len(out["scriptMarkdown"]), 500)

    def test_apply_script_normalizer_batch(self):
        payload = {
            "episodes": [
                {
                    "episodeNumber": 1,
                    "title": "第一集",
                    "scriptMarkdown": "**陆成**：这事不对劲。",
                },
                {
                    "episodeNumber": 2,
                    "title": "第二集",
                    "scenes": [
                        {
                            "sceneHeading": "2-1 夜 内 办公室",
                            "sceneNumber": "2-1",
                            "timeOfDay": "夜",
                            "interiorExterior": "内",
                            "location": "办公室",
                            "actions": [{"order": 1, "content": "△ 陆成翻看文件"}],
                            "dialogues": [
                                {"order": 1, "speaker": "陆成", "line": "证据在这。"},
                                {"order": 2, "speaker": "林晓棠", "line": "你早就知道？"},
                            ],
                        }
                    ],
                },
            ]
        }
        out, log = apply_script_normalizer(payload, {"formatVariant": "variant-b"})
        self.assertGreaterEqual(log.get("rebuiltCount", 0), 1)
        self.assertGreaterEqual(out["episodes"][0]["sceneCount"], 1)
        self.assertNotIn("（1）", out["episodes"][0]["scriptMarkdown"])
