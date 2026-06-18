"""Legacy sub-skill trace 序列化（旧 orchestration 流水线专用）。"""
from __future__ import annotations

from typing import Any, Dict, List

from apps.creation.models import AgentExecutionRun, SubSkillExecutionLog


def serialize_sub_skill(log: SubSkillExecutionLog) -> Dict[str, Any]:
    return {
        "id": log.skill_id,
        "skill_id": log.skill_id,
        "type": log.skill_type,
        "cli": log.cli,
        "script": log.script,
        "status": log.status,
        "message": log.error_message,
        "duration_ms": log.duration_ms,
        "input_summary": log.input_summary or {},
        "output_summary": log.output_summary or {},
        "input_payload": log.input_payload or {},
        "output_payload": log.output_payload or {},
        "llm_io": log.llm_io or {},
        "started_at": log.started_at.isoformat() if log.started_at else "",
        "finished_at": log.finished_at.isoformat() if log.finished_at else "",
    }


def serialize_legacy_sub_skills(run: AgentExecutionRun) -> Dict[str, Any]:
    """聚合 sub_skill_logs 与 execution_trace，供 Admin / 旧编排调试使用。"""
    logs = run.sub_skill_logs.all().order_by("order_index", "started_at")
    sub_skills: List[Dict[str, Any]] = [serialize_sub_skill(log) for log in logs]
    execution_trace = [
        {
            "id": item["id"],
            "type": item["type"],
            "cli": item["cli"],
            "script": item["script"],
            "status": item["status"],
            "message": item["message"],
        }
        for item in sub_skills
    ]
    return {"sub_skills": sub_skills, "execution_trace": execution_trace}
