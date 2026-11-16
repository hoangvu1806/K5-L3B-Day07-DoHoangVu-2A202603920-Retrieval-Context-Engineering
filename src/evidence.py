"""Định nghĩa hit dùng chung cho mọi phương pháp (quy ước benchmark Day 6).

Một chunk chứa evidence khi: đúng source_id, trang gold nằm trong metadata.pages,
và evidence (gộp khoảng trắng) nằm trọn trong text chunk (gộp khoảng trắng).
"""
from __future__ import annotations

import re


def ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_has_evidence(chunk: dict, gold: list[dict]) -> bool:
    pages = set(chunk.get("metadata", {}).get("pages") or [chunk["page"]])
    text = ws(chunk["text"])
    return any(chunk["source_id"] == g["source_id"] and g["page"] in pages and ws(g["evidence"]) in text
               for g in gold)


def first_hit_rank(results: list[dict], gold: list[dict]) -> int | None:
    for i, c in enumerate(results, 1):
        if chunk_has_evidence(c, gold):
            return i
    return None
