"""In bảng để chấm tay: mỗi câu gồm đáp án mong đợi (hoặc lý do thiếu bằng chứng),
câu trả lời từng cấu hình và nội dung các đoạn được trích dẫn.

  python scripts/review_sheet.py --split dev --configs G0-dense G1-hybrid G2-hybrid-k5 > review_dev.md

Script chỉ trình bày dữ liệu; nhãn do người chấm ghi vào reviews.json.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--configs", nargs="+", required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--chars", type=int, default=260, help="số ký tự in cho mỗi đoạn được trích")
    args = ap.parse_args()
    qs = [q for q in json.loads((ROOT / "benchmark" / "questions.json").read_text(encoding="utf-8"))
          if q["split"] == args.split and (not args.only or q["id"] in args.only)]
    runs = {c: {t["query_id"]: t for t in json.loads(
        (ROOT / "results" / "agent" / args.split / c / "traces.json").read_text(encoding="utf-8"))}
        for c in args.configs}
    for q in qs:
        print(f"\n## {q['id']} {'' if q['answerable'] else '(THIẾU BẰNG CHỨNG)'} {q['question']}")
        if q["answerable"]:
            print(f"EXPECTED: {q['expected_answer']}")
        else:
            print(f"ABSENT: {q['absence_reason']}")
        for c in args.configs:
            t = runs[c].get(q["id"])
            if not t:
                continue
            ctx = {x["ref"]: x for x in t["context"]}
            print(f"\n### {c} [{t['status']}] refs={t['citation_refs']}")
            print(re.sub(r"\n+", " / ", t["answer"] or t.get("error") or "")[:900])
            for ref in t["citation_refs"]:
                x = ctx[ref]
                print(f"  {ref} p{x['pages']}: {' '.join(x['text'].split())[:args.chars]}")


if __name__ == "__main__":
    main()
