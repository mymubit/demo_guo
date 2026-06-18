# -*- coding: utf-8 -*-
"""Script formatting helpers for the ScriptForge runtime."""
from __future__ import annotations

import re


def scripts_result_to_markdown(scripts_data: dict) -> str:
    parts = []
    for ep in scripts_data.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        text = str(
            ep.get("full_script_text")
            or ep.get("scriptMarkdown")
            or ep.get("content")
            or ""
        )
        if not text.strip():
            continue
        text = re.sub(r"^##\s*", "# ", text, flags=re.MULTILINE)
        if not re.match(r"^#\s*", text):
            num = ep.get("episode") or ep.get("episodeNumber") or len(parts) + 1
            text = f"# Episode {num}\n\n{text}"
        parts.append(text.strip())
    return "\n\n".join(parts)
