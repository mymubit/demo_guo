# -*- coding: utf-8 -*-
from __future__ import annotations

__all__ = ["dispatch_command"]


def __getattr__(name: str):
    if name == "dispatch_command":
        from .dispatcher import dispatch_command

        return dispatch_command
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
