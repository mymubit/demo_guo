# -*- coding: utf-8 -*-
"""测试辅助。"""
from __future__ import annotations

import json
import os
from pathlib import Path

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.drama.services.project_settings import ProjectSettingsService

# 技能仓根：优先环境变量，默认使用仓库内副本（backend/../drama-skills）
SKILLS_ROOT = os.environ.get(
    "DRAMA_SKILLS_ROOT",
    str(Path(__file__).resolve().parents[4] / "drama-skills"),
)

def _skills_fixture(*parts: str) -> Path:
    root = Path(SKILLS_ROOT)
    return root.joinpath("tools", "fixtures", *parts)


FIXTURE_SETTINGS = json.loads(
    _skills_fixture("config", "project-settings.json").read_text(encoding="utf-8")
)

FIXTURES = json.loads(
    _skills_fixture("artifacts", "valid-artifacts.json").read_text(encoding="utf-8")
)


def create_user(username: str = "tester", password: str = "test-pass-123") -> User:
    return User.objects.create_user(username=username, password=password)


def create_project(user: User, title: str = "测试项目") -> object:
    return ProjectSettingsService().create_project(
        user, title, entry_type="original_track"
    )


def auth_client(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client
