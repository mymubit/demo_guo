# -*- coding: utf-8 -*-
"""导出每个产物的完整 normalize 后 payload（供 presenter 精确对齐）。"""
from __future__ import annotations

import json
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, BACKEND_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from apps.creation.models import ProjectFusionArtifact
from apps.drama.models import DramaProject
from apps.drama.presentation.normalize import normalize_payload

title = sys.argv[1] if len(sys.argv) > 1 else "e2e-drama-expert"
key_filter = sys.argv[2] if len(sys.argv) > 2 else None

dp = DramaProject.objects.filter(title=title).first()
if not dp:
    print("project not found:", title)
    sys.exit(1)

payloads = {}
qs = ProjectFusionArtifact.objects.filter(project_id=dp.project_id).order_by("artifact_key")
if key_filter:
    qs = qs.filter(artifact_key=key_filter)

for artifact in qs:
    payloads[artifact.artifact_key] = normalize_payload(artifact.payload)

out = os.path.join(os.path.dirname(__file__), f"e2e_payloads_{title.replace('-', '_')}.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(payloads, f, ensure_ascii=False, indent=2)
print(f"written {out} ({len(payloads)} artifacts)")
