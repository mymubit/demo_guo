# -*- coding: utf-8 -*-
"""
management command: python manage.py run_evolve_audit

子命令：
  daily       每日进化审计（低分追溯 + 高分提炼）
  proposals   列出待审核提案
  approve     审核通过指定提案
  reject      驳回指定提案
"""
from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "短剧技能进化审计 —— 低分追溯、高分提炼、提案管理"

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="subcommand", help="子命令")

        subparsers.add_parser("daily", help="执行每日进化审计（低分+高分）")

        subparsers.add_parser("proposals", help="列出所有待审核提案")

        approve_p = subparsers.add_parser("approve", help="审核通过指定提案文件")
        approve_p.add_argument("filename", help="提案文件名（pending-proposals/ 下的 .json）")

        reject_p = subparsers.add_parser("reject", help="驳回指定提案文件")
        reject_p.add_argument("filename", help="提案文件名")
        reject_p.add_argument("--reason", default="", help="驳回原因")

    def handle(self, *args, **options):
        subcommand = options.get("subcommand")

        if subcommand == "daily" or subcommand is None:
            self._run_daily()
        elif subcommand == "proposals":
            self._list_proposals()
        elif subcommand == "approve":
            self._approve(options["filename"])
        elif subcommand == "reject":
            self._reject(options["filename"], options.get("reason", ""))
        else:
            raise CommandError(f"未知子命令: {subcommand}")

    def _run_daily(self):
        from apps.creation.evolve_audit import run_daily_evolve_audit

        self.stdout.write("▶ 开始每日进化审计...")
        result = run_daily_evolve_audit()
        self.stdout.write(self.style.SUCCESS(
            f"✓ 审计完成 "
            f"低分追溯={result['lowScoreAudited']} "
            f"高分提炼={result['highScoreExtracted']} "
            f"errors={len(result['errors'])}"
        ))
        if result["errors"]:
            self.stdout.write(self.style.WARNING(f"  失败项目: {result['errors']}"))
        self.stdout.write(f"  提案目录: {result['pendingProposalsDir']}")

    def _list_proposals(self):
        from apps.creation.evolve_audit import list_pending_proposals

        proposals = list_pending_proposals()
        if not proposals:
            self.stdout.write("暂无待审核提案")
            return

        self.stdout.write(f"共 {len(proposals)} 个待审核提案：\n")
        for p in proposals:
            ptype = p.get("type", "?")
            score = p.get("score", "?")
            audited = p.get("auditedAt", "")[:16]
            summary = p.get("summary", "")[:60]
            self.stdout.write(f"  [{ptype}] score={score} @ {audited}")
            self.stdout.write(f"    {summary}")
            self.stdout.write("")

    def _approve(self, filename: str):
        from apps.creation.evolve_audit import approve_proposal

        if approve_proposal(filename):
            self.stdout.write(self.style.SUCCESS(f"✓ 已通过: {filename}"))
            self.stdout.write("  请手动将 approved/ 中的提案内容合并到对应规则文件")
        else:
            raise CommandError(f"文件不存在: {filename}")

    def _reject(self, filename: str, reason: str):
        from apps.creation.evolve_audit import reject_proposal

        if reject_proposal(filename, reason):
            self.stdout.write(self.style.WARNING(f"✗ 已驳回: {filename}"))
        else:
            raise CommandError(f"文件不存在: {filename}")
