# -*- coding: utf-8 -*-
"""校验结果数据类 — 对齐 Node.js CLI 返回的 {passed, issues} 格式。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    passed: bool
    issues: List[str] = field(default_factory=list)
    sub_skill: str = ""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": self.issues,
            "subSkill": self.sub_skill,
        }

    @classmethod
    def ok(cls, sub_skill: str = "") -> "ValidationResult":
        return cls(passed=True, sub_skill=sub_skill)

    @classmethod
    def fail(cls, issues: List[str], sub_skill: str = "") -> "ValidationResult":
        return cls(passed=False, issues=issues, sub_skill=sub_skill)
