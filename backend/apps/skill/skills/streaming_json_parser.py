# -*- coding: utf-8 -*-
"""从 LLM token 流中增量解析 JSON 数组元素。"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple

_CODE_FENCE_START = re.compile(r"^```(?:json)?\s*", re.I)


class IncrementalJsonArrayParser:
    """识别 `[{...}, {...}]` 或 `{"episodes":[...]}` 形态，逐条 yield 完整 object。"""

    def __init__(self, *, array_keys: Tuple[str, ...] = ("episodes", "stages")) -> None:
        self._array_keys = array_keys
        self._buffer = ""
        self._strip_offset = 0
        self._parsed_count = 0
        self._array_started = False
        self._array_key: Optional[str] = None
        self._root_is_array = False
        self._scan_pos = 0
        self._in_string = False
        self._escape = False
        self._object_depth = 0
        self._object_start: Optional[int] = None

    @property
    def parsed_count(self) -> int:
        return self._parsed_count

    def feed(self, chunk: str) -> Iterator[Dict[str, Any]]:
        if not chunk:
            return
        self._buffer += chunk
        self._maybe_strip_code_fence_prefix()
        self._detect_array_context()
        yield from self._scan_new_objects()
        self._shrink_buffer()

    def flush(self) -> Iterator[Dict[str, Any]]:
        yield from self._scan_new_objects(force=True)

    def _maybe_strip_code_fence_prefix(self) -> None:
        view = self._buffer[self._strip_offset :]
        match = _CODE_FENCE_START.match(view)
        if match:
            self._strip_offset += match.end()
            return
        if view.startswith("```"):
            return
        trimmed = view.lstrip()
        if trimmed and trimmed[0] in "{[":
            self._strip_offset += len(view) - len(trimmed)

    def _working_text(self) -> str:
        return self._buffer[self._strip_offset :]

    def _detect_array_context(self) -> None:
        if self._array_started:
            return
        text = self._working_text().lstrip()
        if not text:
            return
        if text[0] == "[":
            self._array_started = True
            self._root_is_array = True
            self._scan_pos = 1
            return
        if text[0] != "{":
            return
        for key in self._array_keys:
            marker = f'"{key}"'
            idx = text.find(marker)
            if idx < 0:
                continue
            bracket = text.find("[", idx)
            if bracket < 0:
                continue
            self._array_started = True
            self._array_key = key
            self._root_is_array = False
            self._scan_pos = bracket + 1
            return

    def _scan_new_objects(self, *, force: bool = False) -> Iterator[Dict[str, Any]]:
        if not self._array_started:
            return
        text = self._working_text()
        idx = self._scan_pos
        length = len(text)

        while idx < length:
            ch = text[idx]
            if self._object_start is None:
                if ch in " \t\r\n,":
                    idx += 1
                    continue
                if ch == "]":
                    self._scan_pos = idx + 1
                    return
                if ch != "{":
                    idx += 1
                    continue
                self._object_start = idx
                self._object_depth = 1
                self._in_string = False
                self._escape = False
                idx += 1
                continue

            if self._escape:
                self._escape = False
                idx += 1
                continue
            if ch == "\\" and self._in_string:
                self._escape = True
                idx += 1
                continue
            if ch == '"':
                self._in_string = not self._in_string
                idx += 1
                continue
            if self._in_string:
                idx += 1
                continue
            if ch == "{":
                self._object_depth += 1
            elif ch == "}":
                self._object_depth -= 1
                if self._object_depth == 0 and self._object_start is not None:
                    raw = text[self._object_start : idx + 1]
                    self._object_start = None
                    self._scan_pos = idx + 1
                    self._parsed_count += 1
                    try:
                        parsed = json.loads(raw)
                    except json.JSONDecodeError:
                        if force:
                            return
                        continue
                    if isinstance(parsed, dict):
                        yield parsed
                    idx = self._scan_pos
                    continue
            idx += 1

        self._scan_pos = idx

    def _shrink_buffer(self) -> None:
        if self._scan_pos > 65536:
            drop = self._scan_pos - 4096
            self._buffer = self._buffer[self._strip_offset + drop :]
            self._strip_offset = 0
            self._scan_pos = max(0, self._scan_pos - drop)
            if self._object_start is not None:
                self._object_start = max(0, self._object_start - drop)


def extract_episode_number(item: Dict[str, Any], fallback_index: int) -> int:
    for key in ("episodeNumber", "episode_number", "episode", "index", "number"):
        value = item.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return fallback_index
