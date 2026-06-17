"""敏感词服务（精简版）。"""
from __future__ import annotations

import logging
import re

from django.db import transaction

from .models import SensitiveWord

logger = logging.getLogger(__name__)


@transaction.atomic
def add_word(word: str, note: str = "") -> SensitiveWord:
    word = (word or "").strip()[:128]
    if not word:
        from apps.operations.exceptions import OpsError
        raise OpsError("敏感词不能为空")
    obj, created = SensitiveWord.objects.get_or_create(
        word=word, defaults={"note": note[:255]},
    )
    if not created and note:
        obj.note = note[:255]
        obj.save(update_fields=["note", "updated_at"])
    return obj


@transaction.atomic
def toggle_word(word: SensitiveWord, *, is_active: bool) -> SensitiveWord:
    word.is_active = is_active
    word.save(update_fields=["is_active", "updated_at"])
    return word


@transaction.atomic
def remove_word(word: SensitiveWord) -> None:
    word.delete()


def check_text(text: str) -> list[str]:
    """对一段文本做敏感词检查，返回命中的词列表。"""
    if not text:
        return []
    hits = []
    for w in SensitiveWord.objects.filter(is_active=True).only("word"):
        if w.word and w.word in text:
            hits.append(w.word)
    return hits
