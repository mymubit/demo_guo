# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentResult:
    agent_id: str
    status: str  # completed | error | skipped
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "outputs": self.outputs,
            "errors": self.errors,
            "meta": self.meta,
        }


@dataclass
class WorkspaceInvokeOptions:
    node_index: int
    script_from: Optional[int] = None
    script_to: Optional[int] = None
    outline_mode: Optional[str] = None
    outline_from: Optional[int] = None
    outline_to: Optional[int] = None
    outline_stage_key: Optional[str] = None
