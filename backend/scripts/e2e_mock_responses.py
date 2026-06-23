# -*- coding: utf-8 -*-
"""Drama E2E 用 Mock LLM 响应 — 产出满足契约校验的最小 JSON。"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.agent_runtime.independent_service import IndependentAgentService

EPISODE_COUNT = 3


def _episodes(from_ep: int = 1, to_ep: int | None = None) -> List[Dict[str, Any]]:
    end = to_ep if to_ep is not None else EPISODE_COUNT
    return [
        {"episodeNumber": i, "title": f"第{i}集", "scenes": [{"sceneId": f"1-{i}-1", "content": "△内景 测试场景"}]}
        for i in range(from_ep, end + 1)
    ]


def _artifact_payload(artifact_key: str, *, agent_id: str, run_params: Dict[str, Any]) -> Dict[str, Any]:
    ep_from = int(run_params.get("episode_from") or run_params.get("script_from") or 1)
    ep_to = int(run_params.get("episode_to") or run_params.get("script_to") or EPISODE_COUNT)

    if artifact_key == "episode_scripts":
        return {"episodes": _episodes(ep_from, ep_to), "projectId": "e2e"}
    if artifact_key == "series_outline":
        return {"episodes": _episodes(1, EPISODE_COUNT)}
    if artifact_key == "project_brief":
        return {"status": "confirmed", "title": "E2E测试剧", "coreIdea": "甜宠逆袭测试"}
    if artifact_key == "review_report":
        return {"passed": True, "overall": "通过", "summary": "E2E mock 审查通过"}
    if artifact_key == "quality_report":
        return {"overall_score": 85, "grade": "A", "overall": 85, "verdict": "通过"}
    if artifact_key == "script_score_report":
        return {"overallScore": 85, "grade": "A"}
    if artifact_key == "compliance_report":
        return {"overall_result": "通过", "passed": True}
    if artifact_key == "marketing_kit":
        return {"titles": ["E2E测试标题"], "hooks": ["测试钩子"]}
    if artifact_key == "insight_report":
        return {"layer1_peel": {"summary": "mock"}, "overall": "通过"}
    if artifact_key == "polish_log":
        return {"suggestions": [], "summary": "mock polish"}
    if artifact_key == "character_bible":
        return {"characters": [{"name": "女主", "role": "protagonist"}, {"name": "霸总", "role": "love_interest"}]}
    if artifact_key == "world_setting":
        return {"settingSummary": "现代都市豪门", "era": "当代"}
    return {"agentId": agent_id, "mock": True}


def build_mock_output(agent_id: str, run_params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    params = dict(run_params or {})
    agent = AgentDefinitionService.get_runnable(agent_id)
    contract = agent.output_contract or {}
    artifacts = [str(k) for k in contract.get("artifacts") or []]
    if not artifacts:
        return {"mock": True}
    default_key = getattr(agent, "default_output_artifact_key", "") or artifacts[0]
    body = _artifact_payload(default_key, agent_id=agent_id, run_params=params)
    output = {default_key: body}
    IndependentAgentService.validate_output(agent, output)
    return output


def mock_llm_json(agent_id: str, run_params: Dict[str, Any] | None = None) -> str:
    return json.dumps(build_mock_output(agent_id, run_params), ensure_ascii=False)
