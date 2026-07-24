# -*- coding: utf-8 -*-
"""W6 删旧守卫：文件系统 / 路由 410 / 源码 banned 扫描。"""
from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

_DRAMA_ROOT = Path(settings.BASE_DIR) / "apps" / "drama"
_REPO_ROOT = Path(settings.BASE_DIR).parent

_DELETED_RELATIVE_PATHS = (
    "v2_urls.py",
    "v2_views.py",
    "v2_serializers.py",
    "v2_service.py",
    "services/v6_runtime.py",
    "services/v6_workbench.py",
    "services/v6_control_plane.py",
    "services/generation_service.py",
    "services/generation_gate.py",
)

_SCAN_ROOTS = (
    _DRAMA_ROOT / "orchestrator",
    _DRAMA_ROOT / "skills_bridge",
    _DRAMA_ROOT / "api" / "v3",
    _DRAMA_ROOT / "tasks_v3.py",
)

_BANNED_TOKENS = (
    "v6_runtime",
    "v6_workbench",
    "v6_control_plane",
    "/api/v2/studio",
)


def _iter_py_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if root.is_dir():
        return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]
    return []


class LegacyGoneFilesystemTests(SimpleTestCase):
    def test_deleted_backend_modules_absent(self) -> None:
        missing_ok: list[str] = []
        still_present: list[str] = []
        for rel in _DELETED_RELATIVE_PATHS:
            path = _DRAMA_ROOT / rel
            if path.exists():
                still_present.append(str(path))
            else:
                missing_ok.append(rel)
        self.assertEqual(
            still_present,
            [],
            msg="legacy modules must be deleted: " + "; ".join(still_present),
        )
        self.assertEqual(len(missing_ok), len(_DELETED_RELATIVE_PATHS))

    def test_frontend_studio_directory_absent(self) -> None:
        studio_dir = _REPO_ROOT / "frontend" / "src" / "studio"
        self.assertFalse(studio_dir.exists(), msg=f"expected deleted: {studio_dir}")


class LegacyGoneRouteTests(APITestCase):
    def test_v2_studio_bootstrap_returns_410(self) -> None:
        resp = self.client.get("/api/v2/studio/bootstrap/")
        self.assertEqual(resp.status_code, 410)
        body = resp.json()
        self.assertEqual(body["code"], 410)
        self.assertIn("/api/v3", body["message"])


class LegacyGoneSourceScanTests(SimpleTestCase):
    def test_v3_product_paths_have_no_banned_tokens(self) -> None:
        hits: list[str] = []
        for root in _SCAN_ROOTS:
            self.assertTrue(root.exists(), msg=f"scan root missing: {root}")
            for path in _iter_py_files(root):
                text = path.read_text(encoding="utf-8")
                for token in _BANNED_TOKENS:
                    if token in text:
                        hits.append(f"{path.relative_to(_DRAMA_ROOT)}: {token}")
        self.assertEqual(
            hits,
            [],
            msg="banned legacy tokens in V3 product paths: " + "; ".join(hits),
        )

    def test_frontend_app_pages_have_no_banned_tokens(self) -> None:
        frontend_roots = (
            _REPO_ROOT / "frontend" / "src" / "app",
            _REPO_ROOT / "frontend" / "src" / "pages",
        )
        hits: list[str] = []
        for root in frontend_roots:
            self.assertTrue(root.exists(), msg=f"scan root missing: {root}")
            for path in root.rglob("*"):
                if path.suffix not in {".ts", ".tsx"}:
                    continue
                if "node_modules" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8")
                for token in _BANNED_TOKENS:
                    if token in text:
                        hits.append(f"{path.relative_to(_REPO_ROOT)}: {token}")
        self.assertEqual(
            hits,
            [],
            msg="banned legacy tokens in frontend: " + "; ".join(hits),
        )
