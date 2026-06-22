# -*- coding: utf-8 -*-
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.creation.models import Project, ProjectChunk
from apps.skill.skills.streaming_json_parser import IncrementalJsonArrayParser, extract_episode_number

User = get_user_model()


class IncrementalJsonArrayParserTests(TestCase):
    def test_root_array_two_objects(self):
        parser = IncrementalJsonArrayParser(array_keys=("episodes",))
        stream = '[{"episodeNumber":1,"title":"A"},{"episodeNumber":2,"title":"B"}]'
        items = []
        for chunk in (stream[:20], stream[20:]):
            items.extend(list(parser.feed(chunk)))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["episodeNumber"], 1)
        self.assertEqual(items[1]["title"], "B")

    def test_wrapped_episodes_key(self):
        parser = IncrementalJsonArrayParser(array_keys=("episodes",))
        raw = json.dumps({"episodes": [{"episodeNumber": 3, "x": 1}]})
        items = list(parser.feed(raw))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["episodeNumber"], 3)

    def test_code_fence_prefix(self):
        parser = IncrementalJsonArrayParser(array_keys=("episodes",))
        raw = '```json\n[{"episodeNumber":1}]\n```'
        items = list(parser.feed(raw))
        self.assertEqual(len(items), 1)

    def test_escaped_quotes_in_string(self):
        parser = IncrementalJsonArrayParser(array_keys=("episodes",))
        raw = '[{"episodeNumber":1,"line":"say \\"hi\\""}]'
        items = list(parser.feed(raw))
        self.assertEqual(len(items), 1)
        self.assertIn("hi", items[0]["line"])

    def test_extract_episode_number_fallback(self):
        self.assertEqual(extract_episode_number({}, 5), 5)
        self.assertEqual(extract_episode_number({"episodeNumber": 2}, 5), 2)


class ProjectAgentNotesApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900008801", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="notes-test",
            theme="overbearing-ceo",
            core_idea="测试记忆",
            episode_count=10,
            format_variant="B",
            fusion_status=Project.FUSION_DRAFT,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_patch_and_get_agent_notes(self):
        url = f"/api/creation/projects/{self.project.id}/agent-notes/"
        resp = self.client.patch(
            url,
            {"agent_notes": {"rejects": ["狗血反转"], "style_preferences": ["快节奏"]}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.project.refresh_from_db()
        self.assertEqual(self.project.agent_notes.get("rejects"), ["狗血反转"])

        get_resp = self.client.get(url)
        self.assertEqual(get_resp.data["data"]["agent_notes"]["style_preferences"], ["快节奏"])


class ProjectChunksApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900008802", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="chunk-test",
            theme="overbearing-ceo",
            core_idea="测试分片",
            episode_count=10,
            format_variant="B",
            fusion_status=Project.FUSION_DRAFT,
        )
        ProjectChunk.objects.create(
            project=self.project,
            kind="episode_scripts",
            index=1,
            data={"episodeNumber": 1, "body": "第一集"},
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_chunks(self):
        url = f"/api/creation/projects/{self.project.id}/chunks/"
        resp = self.client.get(url, {"kind": "episode_scripts"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        self.assertEqual(resp.data["data"]["total"], 1)
        self.assertEqual(resp.data["data"]["last_episode_index"], 1)
        self.assertEqual(resp.data["data"]["items"][0]["index"], 1)
