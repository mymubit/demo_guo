# -*- coding: utf-8 -*-
"""JSON Schema 校验封装。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
from django.conf import settings
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from apps.core.exceptions import SCHEMA_VALIDATION_FAILED, BusinessException


class SchemaValidator:
    """基于 jsonschema 的写入前校验。"""

    def __init__(self, schema_root: Path | None = None) -> None:
        self.skills_root = Path(schema_root or settings.DRAMA_SKILLS_ROOT).resolve()

    def load_schema(self, relative_path: str) -> dict[str, Any]:
        path = self._resolve_path(relative_path)
        if not path.exists():
            raise FileNotFoundError(f"Schema 不存在: {relative_path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def validate(self, instance: Any, schema: dict[str, Any], *, schema_path: Path | None = None) -> None:
        try:
            validator = self._build_validator(schema, schema_path)
            validator.validate(instance)
        except jsonschema.ValidationError as exc:
            raise BusinessException(
                SCHEMA_VALIDATION_FAILED,
                f"Schema 校验失败: {exc.message}",
                http_status=422,
            ) from exc

    def validate_file(self, instance: Any, relative_path: str) -> None:
        path = self._resolve_path(relative_path)
        schema = self.load_schema(relative_path)
        self.validate(instance, schema, schema_path=path)

    def _resolve_path(self, relative_path: str) -> Path:
        # schemas/ 与 v6/ 均相对 skills_root；其余相对 schemas/
        if relative_path.startswith("schemas/") or relative_path.startswith("v6/"):
            return self.skills_root / relative_path
        candidate = self.skills_root / relative_path
        if candidate.exists():
            return candidate
        return self.skills_root / "schemas" / relative_path

    def _build_validator(
        self, schema: dict[str, Any], schema_path: Path | None
    ) -> Draft202012Validator:
        schemas_root = self.skills_root / "schemas"
        registry = _schema_registry(schemas_root)
        if schema_path is not None:
            anchor = schema_path.as_uri()
            resource = Resource.from_contents(schema)
            registry = registry.with_resource(anchor, resource)
            return Draft202012Validator(schema, registry=registry)
        return Draft202012Validator(schema, registry=registry)


@lru_cache(maxsize=8)
def _schema_registry(schemas_root: Path) -> Registry:
    resources: list[tuple[str, Resource]] = []
    if not schemas_root.exists():
        return Registry()
    artifacts_root = schemas_root / "artifacts"
    for file_path in schemas_root.rglob("*.schema.json"):
        content = json.loads(file_path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(content)
        resources.append((file_path.as_uri(), resource))
        rel_from_root = file_path.relative_to(schemas_root).as_posix()
        resources.append((rel_from_root, resource))
        schema_id = content.get("$id")
        if isinstance(schema_id, str):
            resources.append((schema_id, resource))
        if artifacts_root in file_path.parents:
            rel_from_artifacts = file_path.relative_to(artifacts_root).as_posix()
            resources.append((rel_from_artifacts, resource))
            resources.append((f"{artifacts_root.as_uri()}/{rel_from_artifacts}", resource))
    return Registry().with_resources(resources)
