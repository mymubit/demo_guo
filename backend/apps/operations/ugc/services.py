"""UGC 模板市场服务。"""
from __future__ import annotations

import logging
import re
import uuid

from django.db import transaction
from django.db.models import Avg, F
from django.utils import timezone

from apps.operations.constants import UgcTemplateStatus
from apps.operations.exceptions import UgcTemplateError

from .models import UserTemplate, UserTemplateCollection, UserTemplateRating

logger = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _ensure_slug(name: str) -> str:
    """由名称生成唯一 slug。"""
    base = _SLUG_RE.sub("-", (name or "").lower()).strip("-")[:80] or "template"
    slug = base
    i = 0
    while UserTemplate.objects.filter(slug=slug).exists():
        i += 1
        slug = f"{base}-{i}"
    return slug


# ──────────────────────────────────────────────
# 模板发布 / 审核
# ──────────────────────────────────────────────

@transaction.atomic
def publish_template(
    *,
    author,
    name: str,
    description: str = "",
    category: str = "",
    tags: list | None = None,
    cover_url: str = "",
    pack_snapshot: dict | None = None,
    source_pack=None,
    auto_submit: bool = True,
) -> UserTemplate:
    """创作者发布模板。

    auto_submit=True：直接进入待审核；否则保存为草稿。
    """
    if not name:
        raise UgcTemplateError("模板名称不能为空")
    if not pack_snapshot:
        raise UgcTemplateError("模板快照不能为空")
    tpl = UserTemplate.objects.create(
        slug=_ensure_slug(name),
        name=name[:128],
        description=description,
        category=category[:64],
        tags=tags or [],
        cover_url=cover_url[:512],
        pack_snapshot=pack_snapshot or {},
        source_pack=source_pack,
        author=author,
        status=(
            UgcTemplateStatus.PENDING
            if auto_submit
            else UgcTemplateStatus.DRAFT
        ),
    )
    logger.info("ugc.template.publish author=%s slug=%s", author, tpl.slug)
    return tpl


@transaction.atomic
def review_template(
    template: UserTemplate,
    *,
    approve: bool,
    reviewer,
    note: str = "",
) -> UserTemplate:
    """运营审核。"""
    if template.status != UgcTemplateStatus.PENDING:
        raise UgcTemplateError(f"当前状态 {template.status} 不可审核")
    template.status = (
        UgcTemplateStatus.PUBLISHED if approve else UgcTemplateStatus.REJECTED
    )
    template.reviewed_by = reviewer
    template.reviewed_at = timezone.now()
    template.review_note = note[:1000]
    if approve:
        template.published_at = timezone.now()
    template.save(update_fields=[
        "status", "reviewed_by", "reviewed_at",
        "review_note", "published_at", "updated_at",
    ])
    return template


@transaction.atomic
def offline_template(template: UserTemplate, *, operator, note: str = "") -> UserTemplate:
    """下架（运营或创作者本人）。"""
    if template.status not in (UgcTemplateStatus.PUBLISHED, UgcTemplateStatus.PENDING):
        raise UgcTemplateError(f"当前状态 {template.status} 不可下架")
    template.status = UgcTemplateStatus.OFFLINE
    template.review_note = (template.review_note + "\n" + note).strip()[:1000]
    template.save(update_fields=["status", "review_note", "updated_at"])
    return template


@transaction.atomic
def set_featured(template: UserTemplate, *, featured: bool, sort_weight: int = 0) -> UserTemplate:
    """运营置顶 / 调整排序权重。"""
    template.is_featured = featured
    template.sort_weight = sort_weight
    template.save(update_fields=["is_featured", "sort_weight", "updated_at"])
    return template


# ──────────────────────────────────────────────
# 评分 / 收藏 / 下载
# ──────────────────────────────────────────────

@transaction.atomic
def rate_template(*, template: UserTemplate, user, score: int, comment: str = "") -> UserTemplateRating:
    """对模板评分（1-5），同一用户多次评分只保留最后一次。"""
    if template.status != UgcTemplateStatus.PUBLISHED:
        raise UgcTemplateError("模板未发布，无法评分")
    if not (1 <= int(score) <= 5):
        raise UgcTemplateError("评分需在 1-5 之间")

    rating, created = UserTemplateRating.objects.update_or_create(
        template=template, user=user,
        defaults={"score": int(score), "comment": comment[:500]},
    )
    _refresh_rating_agg(template)
    return rating


@transaction.atomic
def collect_template(*, template: UserTemplate, user, collection_name: str = "") -> UserTemplateCollection:
    """收藏模板。"""
    if template.status != UgcTemplateStatus.PUBLISHED:
        raise UgcTemplateError("模板未发布，无法收藏")
    obj, created = UserTemplateCollection.objects.get_or_create(
        template=template, user=user,
        defaults={"collection_name": collection_name[:64] or "默认收藏夹"},
    )
    if created:
        UserTemplate.objects.filter(pk=template.pk).update(
            collection_count=F("collection_count") + 1,
        )
    return obj


@transaction.atomic
def uncollect_template(*, template: UserTemplate, user) -> bool:
    """取消收藏。"""
    deleted, _ = UserTemplateCollection.objects.filter(template=template, user=user).delete()
    if deleted:
        UserTemplate.objects.filter(pk=template.pk, collection_count__gt=0).update(
            collection_count=F("collection_count") - 1,
        )
        return True
    return False


@transaction.atomic
def download_template(*, template: UserTemplate) -> UserTemplate:
    """下载模板（计数 + 返回快照）。"""
    if template.status != UgcTemplateStatus.PUBLISHED:
        raise UgcTemplateError("模板未发布，无法下载")
    UserTemplate.objects.filter(pk=template.pk).update(
        downloads_count=F("downloads_count") + 1,
    )
    template.refresh_from_db(fields=["downloads_count"])
    return template


@transaction.atomic
def record_use(*, template: UserTemplate) -> None:
    """用户用模板跑了项目，触发计数。"""
    UserTemplate.objects.filter(pk=template.pk).update(
        uses_count=F("uses_count") + 1,
    )


def _refresh_rating_agg(template: UserTemplate) -> None:
    """重算 rating_avg / rating_count。"""
    agg = UserTemplateRating.objects.filter(template=template).aggregate(
        avg=Avg("score"), cnt=Avg("id"),
    )
    template.rating_avg = agg["avg"] or 0
    template.rating_count = UserTemplateRating.objects.filter(template=template).count()
    template.save(update_fields=["rating_avg", "rating_count", "updated_at"])


# ──────────────────────────────────────────────
# 搜索 / 列表
# ──────────────────────────────────────────────

def search_templates(
    *,
    keyword: str = "",
    category: str = "",
    tag: str = "",
    ordering: str = "popular",
    page: int = 1,
    page_size: int = 20,
):
    """前台搜索。

    ordering: popular / newest / rating / featured
    """
    qs = UserTemplate.objects.filter(status=UgcTemplateStatus.PUBLISHED)
    if keyword:
        qs = qs.filter(name__icontains=keyword)
    if category:
        qs = qs.filter(category=category)
    if tag:
        qs = qs.filter(tags__contains=[tag])

    if ordering == "newest":
        qs = qs.order_by("-published_at")
    elif ordering == "rating":
        qs = qs.order_by("-rating_avg", "-rating_count")
    elif ordering == "featured":
        qs = qs.order_by("-is_featured", "-sort_weight", "-published_at")
    else:  # popular
        qs = qs.order_by("-downloads_count", "-uses_count")

    page = max(1, int(page))
    page_size = max(1, min(50, int(page_size)))
    total = qs.count()
    items = qs[(page - 1) * page_size: page * page_size]
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }
