"""运营中心异常（精简版）。"""
from __future__ import annotations


class OpsError(Exception):
    code = "ops_error"

    def __init__(self, message: str = ""):
        super().__init__(message or "运营操作失败")
        self.message = message or "运营操作失败"
