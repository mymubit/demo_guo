# -*- coding: utf-8 -*-
import json
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, BACKEND_DIR)

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.creation.models import Project, ProjectFusionArtifact
from apps.drama.defaults import DRAMA_ROLE_DEFAULTS
from apps.drama.presentation.normalize import normalize_payload

schema_by_key = {}
for role in DRAMA_ROLE_DEFAULTS:
    key = role.get("default_output_artifact_key")
    schema = (role.get("output_contract") or {}).get("schema_version")
    if key:
        schema_by_key[key] = schema

title = sys.argv[1] if len(sys.argv) > 1 else "e2e-drama-expert"
project = Project.objects.filter(title=title).first()
if not project:
    print("project not found:", title)
    sys.exit(1)

print("project:", project.title, project.id)
for artifact in ProjectFusionArtifact.objects.filter(project=project).order_by("artifact_key"):
    body = normalize_payload(artifact.payload)
    schema = schema_by_key.get(artifact.artifact_key, "?")
    if isinstance(body, dict):
        keys = list(body.keys())
    elif isinstance(body, list):
        keys = [f"list[{len(body)}]"]
    else:
        keys = [type(body).__name__]
    print(f"{artifact.artifact_key}\t{schema}\t{keys}")
