# -*- coding: utf-8 -*-
"""将 tools/ 加入 sys.path，并导出 SKILLS_ROOT。

各校验/生成脚本应在 import lib.* 之前执行::

    from _bootstrap import SKILLS_ROOT, TOOLS_ROOT  # noqa: E402 — 需先改 sys.path
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parent
SKILLS_ROOT = TOOLS_ROOT.parent

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))
