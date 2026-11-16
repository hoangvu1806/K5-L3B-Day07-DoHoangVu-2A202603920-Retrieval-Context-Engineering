"""Sinh results/agent/<split>/<config>/reviews.json từ scripts/labels_<split>.py.

Kiểm tra: mỗi câu có nhãn, số nhãn citation bằng số citation trong trace,
câu bị từ chối nhưng có đáp án phải được chấm 0. In danh sách câu gắn cờ cần duyệt.

  python scripts/write_reviews.py --split dev
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    args = ap.parse_args()
    labels = importlib.import_module(f"labels_{args.split}").LABELS
    questions = {q["id"]: q for q in json.loads((ROOT / "benchmark" / "questions.json").read_text(encoding="utf-8"))}
    flagged = []
    for cdir in sorted((ROOT / "results" / "agent" / args.split).iterdir()):
        if not (cdir / "traces.json").exists():
            continue
        reviews = []
        for t in json.loads((cdir / "traces.json").read_text(encoding="utf-8")):
            qid = t["query_id"]
            if t["status"] == "error":
                continue
            grade, support, reason, flag = labels[qid][cdir.name]
            if len(support) != len(t["citations"]):
                raise SystemExit(f"{cdir.name}/{qid}: {len(support)} nhãn citation, trace có {len(t['citations'])}")
            row = {"query_id": qid, "citation_support": support, "reason": reason, "needs_human_check": flag,
                   "labeled_by": "Claude (soạn), học viên duyệt câu gắn cờ"}
            if questions[qid]["answerable"]:
                if t["status"] == "abstain" and grade != 0:
                    raise SystemExit(f"{cdir.name}/{qid}: từ chối câu có đáp án phải chấm 0")
                row["answer_grade"] = grade
            else:
                row["abstention_correct"] = t["status"] == "abstain"
            if flag:
                flagged.append(f"{cdir.name}/{qid}: {reason}")
            reviews.append(row)
        (cdir / "reviews.json").write_text(json.dumps(reviews, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{cdir.name}: {len(reviews)} nhãn")
    print(f"\nCần học viên duyệt ({len(flagged)}):")
    for f in flagged:
        print(" -", f)


if __name__ == "__main__":
    main()
