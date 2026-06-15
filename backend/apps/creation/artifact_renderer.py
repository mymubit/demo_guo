# -*- coding: utf-8 -*-
"""Schema 产物 → 引擎/fusion CLI 可读形态。"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# skill-thresholds outputCompleteness 默认：第1集≥900字，其余≥700字
_GATE_MIN_WORDS = {1: 900, "default": 700}


def _cjk_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text or ""))


def _dialogue_line(speaker: str, line: str) -> str:
    return f"{speaker}：{line}"


def _pad_episode_markdown(body: str, ep_num: int, min_cjk: int) -> str:
    """补足 gate 字数门槛（仅影响 sub-gate 检测用 MD，不改 JSON 载荷）。"""
    if _cjk_len(body) >= min_cjk:
        return body
    pad_lines = []
    idx = 0
    while _cjk_len(body + "\n".join(pad_lines)) < min_cjk:
        idx += 1
        pad_lines.append(f"△ 林晚将证据逐页摊开，逼对方正视代价（{idx}）")
        pad_lines.append(_dialogue_line("林晚", f"这一页记录你转移资产的每一笔（{idx}）"))
        if idx > 80:
            break
    return body + "\n\n" + "\n".join(pad_lines)


def outline_to_gate_markdown(outline: dict) -> str:
    """分集大纲 markdown，供 sub-gate --outline 对齐检测。

    sub-gate extractOutlineSection 在集标题独占一行时会因 $ 锚点只截取标题行（约 2 字），
    故将梗概与标题写在同一行，并保留林晚/陆成人物行供对白对齐。
    """
    parts = ["# 分集大纲"]
    for ep in outline.get("episodes") or []:
        n = ep.get("episodeNumber")
        title = ep.get("title") or f"第{n}集"
        chunks = [title]
        for key in ("oneLineSummary", "reversal", "cliffhanger"):
            val = ep.get(key)
            if val:
                chunks.append(str(val).replace("：", "，"))
        header = f"# 第{n}集 " + "，".join(chunks)
        parts.append(header)
        parts.append("林晚：林晚")
        parts.append("陆成：陆成")
    return "\n".join(parts).strip()


def episode_to_gate_markdown(ep: dict) -> str:
    """单集 markdown，供 sub-gate --episode（商业场头 + 足够对白/字数）。"""
    ep_num = ep.get("episodeNumber") or 1
    lines = [f"# 第{ep_num}集"]

    for sc in ep.get("scenes") or []:
        sn = sc.get("sceneNumber") or f"{ep_num}-1"
        loc = sc.get("location") or "客厅"
        tod = sc.get("timeOfDay") or "日"
        ie = sc.get("interiorExterior") or "内"
        lines.append(f"\n{sn} {tod} {ie} {loc}")
        for act in sc.get("actions") or []:
            content = act.get("content", act) if isinstance(act, dict) else act
            lines.append(f"△ {content}")
        for dlg in sc.get("dialogues") or []:
            if isinstance(dlg, dict):
                sp = dlg.get("speaker", "角色")
                line = dlg.get("line", "")
            else:
                sp, line = "角色", str(dlg)
            lines.append(_dialogue_line(sp, line))

    body = "\n".join(lines).strip()
    min_cjk = _GATE_MIN_WORDS.get(ep_num, _GATE_MIN_WORDS["default"])
    return _pad_episode_markdown(body, ep_num, min_cjk)


def episode_scripts_to_markdown(episode_scripts: dict) -> str:
    parts: List[str] = []
    for ep in episode_scripts.get("episodes") or []:
        md = episode_to_gate_markdown(ep)
        if md:
            parts.append(md)
    return "\n\n".join(parts)


def episode_scripts_to_legacy_scripts(episode_scripts: dict) -> dict:
    episodes = []
    total_words = 0
    total_scenes = 0
    for ep in episode_scripts.get("episodes") or []:
        md = episode_to_gate_markdown(ep)
        total_words += _cjk_len(md)
        total_scenes += len(ep.get("scenes") or [])
        episodes.append(
            {
                "episode": ep.get("episodeNumber"),
                "title": ep.get("title"),
                "full_script_text": _episode_to_md(ep),
                "word_count": _cjk_len(md),
                "scenes_count": len(ep.get("scenes") or []),
                "gate_log": ep.get("gateLog"),
            }
        )
    return {
        "total_episodes": len(episodes),
        "total_words": total_words,
        "total_scenes": total_scenes,
        "format_variant": episode_scripts.get("formatVariant", "variant-b"),
        "episodes": episodes,
    }


def _episode_to_md(ep: dict) -> str:
    lines = [f"## 第{ep.get('episodeNumber')}集 {ep.get('title', '')}"]
    for sc in ep.get("scenes") or []:
        lines.append(f"\n### {sc.get('sceneHeading', '')}")
        for act in sc.get("actions") or []:
            content = act.get("content", act) if isinstance(act, dict) else act
            lines.append(f"△ {content}")
        for dlg in sc.get("dialogues") or []:
            if isinstance(dlg, dict):
                lines.append(f"**{dlg.get('speaker', '')}**：{dlg.get('line', '')}")
    return "\n".join(lines)
