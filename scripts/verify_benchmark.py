"""Kiểm tra benchmark/questions.json trên chunk Day 6, không gọi API.

1. Câu có đáp án: evidence (sau khi gộp khoảng trắng) phải nằm trọn trong ít nhất
   một chunk B đúng nguồn và có trang gold trong metadata.pages. Báo thêm kết quả trên A.
2. Câu thiếu bằng chứng: quét từ khóa trên toàn bộ chunk A và B. Từ khóa có trúng
   mà không nằm trong allowed_hits thì báo lỗi để người viết đọc lại.
3. Kiểm tra số lượng tối thiểu theo BENCHMARK.md.

Từ khóa vắng mặt chưa chứng minh tài liệu thiếu thông tin; mỗi câu còn được đọc
tay quanh near_miss và các bệnh liên quan (ghi trong absence_reason).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence_hits(chunks: list[dict], g: dict) -> list[dict]:
    ev = ws(g["evidence"])
    return [c for c in chunks if c["source_id"] == g["source_id"]
            and g["page"] in (c["metadata"].get("pages") or [c["page"]]) and ev in ws(c["text"])]


def main() -> int:
    questions = load("benchmark/questions.json")
    chunks = {s: load(f"data/day6/chunks_{s}.json") for s in ("A", "B")}
    errors: list[str] = []

    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        errors.append("question id bị trùng")

    for q in questions:
        if q["answerable"]:
            found = {s: any(evidence_hits(chunks[s], g) for g in q["gold"]) for s in chunks}
            status = "OK" if found["B"] else "LỖI"
            if not found["B"]:
                errors.append(f"{q['id']}: evidence không nằm trọn trong chunk B đúng trang")
            print(f"{q['id']:4} {q['split']:4} B:{status:3} A:{'ok' if found['A'] else 'cắt ngang'}")
        else:
            check = q["absence_check"]
            for kw in check["keywords"]:
                pages = sorted({c["page"] for s in chunks for c in chunks[s] if kw.lower() in ws(c["text"]).lower()})
                if pages and kw not in check.get("allowed_hits", {}):
                    errors.append(f"{q['id']}: từ khóa '{kw}' xuất hiện ở trang {pages}")
                note = check.get("allowed_hits", {}).get(kw, "")
                print(f"{q['id']:4} {q['split']:4} '{kw}': {pages or 'không có'} {note}")
            near = ws(q["near_miss"]["text"])
            if not any(near in ws(c["text"]) for c in chunks["B"]):
                errors.append(f"{q['id']}: near_miss không có trong tài liệu")

    need = {("dev", True): 15, ("dev", False): 2, ("test", True): 5, ("test", False): 2}
    for (split, answerable), n in need.items():
        have = sum(q["split"] == split and q["answerable"] == answerable for q in questions)
        print(f"{split}/{'answerable' if answerable else 'abstain'}: {have} (tối thiểu {n})")
        if have < n:
            errors.append(f"{split} thiếu câu {'có đáp án' if answerable else 'thiếu bằng chứng'}")

    for e in errors:
        print("LỖI:", e)
    print("Benchmark hợp lệ" if not errors else f"{len(errors)} lỗi")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
