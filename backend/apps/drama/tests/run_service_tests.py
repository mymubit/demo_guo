# -*- coding: utf-8 -*-
"""轻量级测试脚本 - 直接验证 Drama Service 纯逻辑"""
import sys
import os

sys.path.insert(0, '/workspace/backend')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
    django.setup()

from apps.drama.services import DramaWordCountService, DramaQualityService


def test_word_count_service():
    print("=== DramaWordCountService 测试 ===")
    
    # 1. clean_non_script
    content = "正常内容\n```python\nprint('test')\n```\n更多内容"
    cleaned = DramaWordCountService.clean_non_script(content)
    assert "print('test')" not in cleaned, "代码块未被清除"
    assert "正常内容" in cleaned, "正常内容被错误清除"
    print("✓ clean_non_script 正常")
    
    # 2. count_cjk
    assert DramaWordCountService.count_cjk("你好World123") == 2
    assert DramaWordCountService.count_cjk("") == 0
    print("✓ count_cjk 正常")
    
    # 3. count_scenes
    text = "1-1 日 内 客厅\n一些内容\n1-2 夜 外 街道\n更多内容"
    assert DramaWordCountService.count_scenes(text) == 2
    print("✓ count_scenes 正常")
    
    # 4. validate_episode - 第一集
    content = "1-1 日 内 客厅\n张三（室内）：" + "你好" * 200 + "\n李四：" + "我也好" * 200
    result = DramaWordCountService.validate_episode(content, 1)
    assert result["episode"] == 1
    assert "word_count" in result
    assert "dialogue_ratio" in result
    assert "scene_count" in result
    assert "overall" in result
    assert "recommendations" in result
    print("✓ validate_episode 第一集正常")
    
    # 5. validate_episode - 空内容
    result = DramaWordCountService.validate_episode("", 1)
    assert result["word_count"]["total"] == 0
    print("✓ validate_episode 空内容正常")
    
    print("=== DramaWordCountService 全部通过 ✓\n")


def test_quality_service():
    print("=== DramaQualityService 测试 ===")
    
    dims = DramaQualityService.DIMENSIONS
    assert len(dims) > 0
    for dim in dims:
        assert "key" in dim
        assert "name" in dim
        assert "weight" in dim
    print("✓ DIMENSIONS 结构正确")
    
    total_weight = sum(d["weight"] for d in dims)
    assert abs(total_weight - 1.0) < 0.01, f"权重和应为1，实际为{total_weight}"
    print("✓ 权重和接近 1.0")
    
    # 高分报告
    scores = {d["key"]: 95 for d in dims}
    report = DramaQualityService.build_detailed_quality_report(scores, 1)
    assert report["episode_number"] == 1
    assert report["overall_score"] >= 90
    assert report["grade"] == "S"
    assert len(report["dimensions"]) == len(dims)
    assert "grade_desc" in report
    assert len(report["grade_desc"]) > 0
    print("✓ 高分报告 (S级) 生成正确")
    
    # 低分报告
    scores = {d["key"]: 50 for d in dims}
    report = DramaQualityService.build_detailed_quality_report(scores, 3)
    assert report["grade"] == "D"
    assert report["error_count"] > 0
    assert len(report["all_issues"]) > 0
    print("✓ 低分报告 (D级) 生成正确")
    
    # 等级边界
    for score, expected in [(95, "S"), (85, "A"), (77, "B"), (65, "C"), (50, "D")]:
        scores = {d["key"]: score for d in dims}
        report = DramaQualityService.build_detailed_quality_report(scores)
        assert report["grade"] == expected, f"分数{score}应对应{expected}，实际{report['grade']}"
    print("✓ 等级边界 (S/A/B/C/D) 正确")
    
    # 显式 overall
    scores = {d["key"]: 80 for d in dims}
    scores["overall"] = 92
    report = DramaQualityService.build_detailed_quality_report(scores)
    assert report["overall_score"] == 92.0
    print("✓ 显式 overall 分数正确")
    
    # _dim_name
    for dim in dims:
        assert DramaQualityService._dim_name(dim["key"]) == dim["name"]
    assert DramaQualityService._dim_name("unknown") == "unknown"
    print("✓ _dim_name 查找正确")
    
    # _grade_desc
    for g in ["S", "A", "B", "C", "D"]:
        assert len(DramaQualityService._grade_desc(g)) > 0
    assert DramaQualityService._grade_desc("X") == ""
    print("✓ _grade_desc 所有等级正常")
    
    # _detect_issues_from_score
    assert len(DramaQualityService._detect_issues_from_score("hooks", 95)) == 0
    assert len(DramaQualityService._detect_issues_from_score("hooks", 0)) == 0
    issues = DramaQualityService._detect_issues_from_score("hooks", 50)
    assert len(issues) > 0
    for issue in issues:
        assert "severity" in issue
        assert "desc" in issue
        assert "suggestion" in issue
    print("✓ _detect_issues_from_score 正常")
    
    # build_series_quality_summary
    result = DramaQualityService.build_series_quality_summary([])
    assert result["total_episodes"] == 0
    print("✓ 空剧集汇总正常")
    
    episodes = [
        {"episode_number": 1, "scores": {d["key"]: 85 for d in dims}},
        {"episode_number": 2, "scores": {d["key"]: 70 for d in dims}},
    ]
    result = DramaQualityService.build_series_quality_summary(episodes)
    assert result["total_episodes"] == 2
    assert "series_overall_score" in result
    assert "series_grade" in result
    assert len(result["episode_summaries"]) == 2
    print("✓ 多剧集汇总正常")
    
    # 带字数统计的报告
    scores = {d["key"]: 80 for d in dims}
    wc_result = {
        "episode": 1,
        "word_count": {"total": 1000, "status": "正常", "deviation": 0},
        "dialogue_ratio": {"ratio": "30%", "status": "正常"},
        "scene_count": {"count": 2, "status": "正常"},
    }
    report = DramaQualityService.build_detailed_quality_report(scores, 1, wc_result)
    assert report["word_count_info"] is not None
    assert report["word_count_info"]["total_words"] == 1000
    print("✓ 带字数统计的报告正常")
    
    print("=== DramaQualityService 全部通过 ✓\n")


if __name__ == "__main__":
    test_word_count_service()
    test_quality_service()
    print("🎉 所有测试通过！")
