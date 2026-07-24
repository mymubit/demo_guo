# 注入基线快照（脱敏）

> 总纲 §3.6：允许分层 chars / includes·skipped 摘要 / Top 路径 / checksum / bundle_version。  
> **禁止**把完整 system/user prompt 正文提交进本目录。

## 如何导出

在 backend 容器或已配置 `DRAMA_SKILLS_ROOT` 的 Django shell 中：

```python
from apps.drama.services.prompt_builder import PromptBuilder
from apps.drama.services.skills_loader import get_skills_loader

# 使用最小合法 settings（或从项目读出后剥隐私）
settings = {
    "title": "baseline",
    "entry_type": "original_track",
    "core_idea": "基线导出用短梗概",
    "genre_matrix": {
        "emotion": "revenge",
        "identity": "reborn",
        "conflict": "family",
        "world": "modern",
        "audience_channel": "female",
    },
    "episode_count": 30,
    "creation_preferences": {},
}
system, user, manifest = PromptBuilder().build(
    "drama.topic-director",
    settings=settings,
    workflow_state={},
    artifacts={},
)
# 只落盘脱敏字段：
snap = {
    "agent_id": manifest.get("agent_id"),
    "bundle_version": manifest.get("bundle_version") or get_skills_loader().bundle_version,
    "system_chars": manifest.get("system_chars"),
    "user_chars": manifest.get("user_chars"),
    "checksum": manifest.get("checksum"),
    "layers": manifest.get("layers"),
    "modules": {
        "included": (manifest.get("modules") or {}).get("included"),
        "skipped": (manifest.get("modules") or {}).get("skipped"),
    },
    "knowledge": {
        "included": [
            {"path": x.get("path"), "chars": x.get("chars")}
            for x in ((manifest.get("knowledge") or {}).get("included") or [])
            if isinstance(x, dict)
        ][:20],
    },
    "rules": {
        "sections_included": (manifest.get("rules") or {}).get("sections_included"),
    },
}
# 写入 docs/superpowers/baselines/YYYY-MM-DD-topic-director.json
```

或运行（Docker 示例）：

```bash
docker compose exec -T backend python /app/scripts/export_injection_baseline.py
```

（脚本位于仓库 `scripts/export_injection_baseline.py`，输出到本目录。）

## 文件命名

`YYYY-MM-DD-<agent_id-short>.json`，例如 `2026-07-20-topic-director.json`。
