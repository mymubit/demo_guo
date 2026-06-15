# -*- coding: utf-8 -*-
"""调用 demo4book runtime/sub-* CLI（网站执行层，不复制检测逻辑到 Python）。"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config_loader import FusionSkillConfig, get_fusion_config

logger = logging.getLogger(__name__)

SUB_SKILL_CLI = {
    "sub-brief": ("sub-brief", "index.js"),
    "sub-world": ("sub-world", "index.js"),
    "sub-plan": ("sub-plan", "index.js"),
    "sub-gate": ("sub-gate", "index.js"),
    "sub-score": ("sub-score", "index.js"),
    "sub-compliance": ("sub-compliance", "index.js"),
    "sub-deliver": ("sub-deliver", "index.js"),
    "sub-marketing": ("sub-marketing", "index.js"),
    "sub-pipeline": ("sub-pipeline", "index.js"),
}


class FusionCliRunner:
    def __init__(self, config: FusionSkillConfig | None = None):
        self.config = config or get_fusion_config()
        self._node = shutil.which("node")
        if not self._node:
            raise RuntimeError("未找到 node 可执行文件，无法调用融合子技能 CLI")

    def _script(self, sub_skill: str) -> Path:
        rel = SUB_SKILL_CLI.get(sub_skill)
        if not rel:
            raise ValueError(f"未知子技能：{sub_skill}")
        path = self.config.runtime_dir / rel[0] / rel[1]
        if not path.is_file():
            raise FileNotFoundError(f"子技能脚本不存在：{path}")
        return path

    def run(
        self,
        sub_skill: str,
        args: List[str],
        *,
        cwd: Optional[Path] = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        script = self._script(sub_skill)
        cmd = [self._node, str(script), *args]
        workdir = cwd or self.config.demo4book_root
        logger.info("fusion cli: %s", " ".join(cmd))
        proc = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env={**os.environ},
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        parsed = None
        if stdout:
            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError:
                parsed = None
        return {
            "sub_skill": sub_skill,
            "exit_code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "json": parsed,
            "ok": proc.returncode == 0,
        }

    def run_file(
        self,
        script_path: Path,
        args: List[str],
        *,
        label: str = "",
        cwd: Optional[Path] = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """执行 registry 中 script/runtime 字段指向的独立 Node 脚本。"""
        path = Path(script_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"子技能脚本不存在：{path}")
        cmd = [self._node, str(path), *args]
        workdir = cwd or self.config.demo4book_root
        logger.info("fusion cli file: %s", " ".join(cmd))
        proc = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env={**os.environ},
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        parsed = None
        if stdout:
            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError:
                parsed = None
        return {
            "sub_skill": label or path.stem,
            "exit_code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "json": parsed,
            "ok": proc.returncode == 0,
        }

    def gate_episode(
        self,
        script_path: Path,
        *,
        episode: int = 1,
        outline_path: Optional[Path] = None,
        strict: bool = False,
    ) -> Dict[str, Any]:
        args = [
            f"--input={script_path.resolve()}",
            f"--episode={episode}",
            "--json",
        ]
        if outline_path and outline_path.is_file():
            args.append(f"--outline={outline_path.resolve()}")
        if not strict:
            args.append("--no-strict")
        return self.run("sub-gate", args)

    def gate_full(
        self,
        script_path: Path,
        *,
        episodes: Optional[int] = None,
        compliance_tier: str = "domestic",
        strict: bool = False,
    ) -> Dict[str, Any]:
        args = [f"--input={script_path.resolve()}", "--full", "--json"]
        if episodes:
            args.append(f"--episodes={episodes}")
        if compliance_tier and compliance_tier != "domestic":
            args.append(f"--compliance-tier={compliance_tier}")
        if not strict:
            args.append("--no-strict")
        return self.run("sub-gate", args)

    def score_quick(
        self,
        script_path: Path,
        *,
        bridge: bool = True,
        output_path: Optional[Path] = None,
        strict: bool = False,
    ) -> Dict[str, Any]:
        args = [
            f"--input={script_path.resolve()}",
            "--mode=quick",
            "--format=json",
        ]
        if bridge:
            args.append("--bridge")
        if output_path:
            args.append(f"--output={output_path.resolve()}")
        if not strict:
            args.append("--no-strict")
        return self.run("sub-score", args, timeout=180)

    def compliance(self, script_path: Path, *, strict: bool = False) -> Dict[str, Any]:
        args = [f"--input={script_path.resolve()}", "--json"]
        if not strict:
            args.append("--no-strict")
        return self.run("sub-compliance", args)

    def enrich_brief(
        self,
        input_path: Path,
        *,
        output_path: Optional[Path] = None,
        strict: bool = False,
    ) -> Dict[str, Any]:
        args = [f"--input={input_path.resolve()}", "--json"]
        if output_path:
            args.append(f"--output={output_path.resolve()}")
        if strict:
            args.append("--strict")
        return self.run("sub-brief", args)

    def validate_world(self, input_path: Path, *, strict: bool = False) -> Dict[str, Any]:
        args = [f"--input={input_path.resolve()}", "--json"]
        if not strict:
            args.append("--no-strict")
        return self.run("sub-world", args)

    def validate_plan(
        self,
        input_path: Path,
        *,
        episodes: Optional[int] = None,
        strict: bool = False,
    ) -> Dict[str, Any]:
        args = [f"--input={input_path.resolve()}", "--json"]
        if episodes:
            args.append(f"--episodes={episodes}")
        if not strict:
            args.append("--no-strict")
        return self.run("sub-plan", args)
