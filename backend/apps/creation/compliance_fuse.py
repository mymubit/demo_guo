# -*- coding: utf-8 -*-
"""compliance-fuse：9 大类熔断红线快检（规则层，先于/补充 CLI compliance-check）。"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_FUSE_CATEGORIES: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    (
        "political-sensitive",
        "政治敏感",
        (
            r"台独|港独|藏独|疆独|法轮功|六四|天安门事件|颠覆政权|分裂国家",
            r"历史虚无主义|否定抗战|美化侵略",
        ),
    ),
    (
        "pornographic-vulgar",
        "色情低俗",
        (
            r"全裸|露点|性交|做爱|淫荡|淫秽|色情片|约炮|裸聊|擦边球",
            r"乳沟|床戏.*露骨|生殖器",
        ),
    ),
    (
        "violent-bloody",
        "暴力血腥",
        (
            r"肢解|开膛破肚|内脏流出|斩首|割喉|鲜血喷溅|血肉模糊",
            r"虐杀|酷刑.*详细|活活打死",
        ),
    ),
    (
        "minor-protection",
        "未成年人保护",
        (
            r"未成年.*(?:吸烟|喝酒|赌博|纹身|接吻|性爱|怀孕)",
            r"校园霸凌|学生.*(?:吸毒|嫖娼)|中学生.*恋爱",
            r"校服.*(?:接吻|上床|饮酒)",
        ),
    ),
    (
        "crime-method-display",
        "犯罪手法展示",
        (
            r"(?:详细|一步步).*(?:盗窃|诈骗|杀人|制毒|爆炸物)",
            r"制作(?:炸弹|毒药|开锁工具).*(?:教程|步骤|方法)",
            r"反侦查.*(?:手段|技巧|教程)|销毁证据.*(?:方法|步骤)",
        ),
    ),
    (
        "horror-content",
        "恐怖内容",
        (
            r"厉鬼|附身|降头|邪教仪式|召唤恶魔",
            r"尸体.*(?:腐烂|肢解)|惨叫.*(?:凄厉|撕心裂肺)",
        ),
    ),
    (
        "distorted-values",
        "价值观扭曲",
        (
            r"美化犯罪|犯罪有理|杀人无所谓|贩毒致富",
            r"拜金炫富.*(?:崇拜|效仿)|教唆.*(?:自杀|自残)",
        ),
    ),
    (
        "human-trafficking",
        "人口买卖/拐卖",
        (
            r"拐卖(?:妇女|儿童|人口)|人口贩卖|卖人口|卖孩子|买卖人口",
            r"器官(?:买卖|摘除|移植).*(?:黑市|非法|强制)|地下器官",
            r"(?:强迫|诱骗|胁迫).*(?:卖身|卖淫|从娼|性交易)",
        ),
    ),
    (
        "terrorism-extremism",
        "恐怖主义/极端主义",
        (
            r"恐怖(?:袭击|主义|组织|分子)|圣战|jihad|isis|塔利班",
            r"炸弹.*(?:引爆|爆炸|恐袭)|大规模(?:杀伤|屠杀|伤亡).*袭击",
            r"极端主义.*(?:宣扬|招募|传播)|煽动种族(?:灭绝|仇恨|屠杀)",
        ),
    ),
)

_DEFERRED_CATEGORIES = (
    ("reference-plagiarism", "参考设定抄袭/融梗", "由 verify-creation / compliance-check 检测"),
    ("production-overbudget", "制作超标", "由制作参数与场景复杂度评估"),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_compliance_fuse_scan(text: str) -> Dict[str, Any]:
    """扫描剧本文本，触碰任一红线即 fuseTriggered=True。"""
    body = (text or "").strip()
    if not body:
        return {
            "fuseTriggered": False,
            "passed": True,
            "skipped": True,
            "reason": "无剧本文本",
            "checkedAt": _now_iso(),
            "source": "compliance-fuse-rule",
            "categories": [],
            "issues": [],
        }

    hits: List[Dict[str, Any]] = []
    issues: List[str] = []

    for code, label, patterns in _FUSE_CATEGORIES:
        cat_hits: List[str] = []
        for pattern in patterns:
            for match in re.finditer(pattern, body, flags=re.IGNORECASE):
                snippet = body[max(0, match.start() - 8) : match.end() + 8].replace("\n", " ")
                cat_hits.append(snippet[:80])
        if cat_hits:
            hits.append(
                {
                    "code": code,
                    "label": label,
                    "riskLevel": "P0",
                    "matchCount": len(cat_hits),
                    "samples": cat_hits[:3],
                }
            )
            issues.append(f"熔断·{label}（{len(cat_hits)} 处）")

    deferred = [
        {"code": c, "label": l, "note": n, "checked": False}
        for c, l, n in _DEFERRED_CATEGORIES
    ]
    fuse = len(hits) > 0

    return {
        "fuseTriggered": fuse,
        "passed": not fuse,
        "skipped": False,
        "grade": "D" if fuse else None,
        "checkedAt": _now_iso(),
        "source": "compliance-fuse-rule",
        "categoryCount": 9,
        "ruleCategoriesChecked": len(_FUSE_CATEGORIES),
        "categories": hits,
        "deferredCategories": deferred,
        "issues": issues[:12],
    }


def merge_fuse_with_cli(rule_report: dict, cli_report: Optional[dict] = None) -> Dict[str, Any]:
    """合并规则层与 CLI 合规结果。"""
    cli = cli_report if isinstance(cli_report, dict) else {}
    fuse = bool(rule_report.get("fuseTriggered")) or bool(cli.get("fuseTriggered"))
    issues = list(rule_report.get("issues") or [])
    for item in cli.get("issues") or cli.get("violations") or []:
        s = str(item).strip()
        if s and s not in issues:
            issues.append(s)
    return {
        "fuseTriggered": fuse,
        "passed": not fuse and bool(cli.get("passed", True)) and bool(rule_report.get("passed", True)),
        "ruleScan": rule_report,
        "cliScan": {
            "passed": cli.get("passed"),
            "level": cli.get("level"),
            "fuseTriggered": cli.get("fuseTriggered"),
        },
        "issues": issues[:16],
        "checkedAt": _now_iso(),
        "source": "compliance-fuse-merged",
    }
