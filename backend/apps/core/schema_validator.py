# -*- coding: utf-8 -*-
"""JSON Schema 校验封装。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
from django.conf import settings
from jsonschema.validators import Draft202012Validator, RefResolver

from apps.core.exceptions import SCHEMA_VALIDATION_FAILED, BusinessException


class SchemaValidator:
    """基于 jsonschema 的写入前校验。"""

    def __init__(self, schema_root: Path | None = None) -> None:
        self.skills_root = Path(schema_root or settings.DRAMA_SKILLS_ROOT)

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
        if relative_path.startswith("schemas/"):
            return self.skills_root / relative_path
        return self.skills_root / "schemas" / relative_path

    def _build_validator(
        self, schema: dict[str, Any], schema_path: Path | None
    ) -> Draft202012Validator:
        artifacts_dir = self.skills_root / "schemas" / "artifacts"
        store: dict[str, Any] = {}
        if artifacts_dir.exists():
            for file_path in artifacts_dir.glob("*.schema.json"):
                content = json.loads(file_path.read_text(encoding="utf-8"))
                store[file_path.name] = content
                if "$id" in content:
                    store[content["$id"]] = content
        base_uri = (schema_path.parent if schema_path else artifacts_dir).as_uri() + "/"
        resolver = RefResolver(base_uri=base_uri, referrer=schema, store=store)
        return Draft202012Validator(schema, resolver=resolver)
