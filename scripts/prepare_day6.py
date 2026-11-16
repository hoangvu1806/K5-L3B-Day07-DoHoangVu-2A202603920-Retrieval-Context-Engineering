"""Chuyển chunk và benchmark Day 6 sang schema Day 7 (data/README.md).

Đầu vào (repo Day 6):
  starter/results/chunks_A.jsonl, chunks_B.jsonl  -> data/day6/chunks_A.json, chunks_B.json
  benchmark/questions.json                         -> data/day6/questions_day6.json

Chunk id giữ nguyên chunk_id Day 6 (cũng là point id trong Qdrant), nên kết quả
dense search và lexical search trên file JSON so khớp được với nhau.
Script chỉ đổi tên trường; không suy luận metadata, không đụng tới gold.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DAY6 = ROOT.parent / "K5-L3B-Day06-DoHoangVu-2A202603920-DataIngestionEngineering"


def convert_chunk(c: dict) -> dict:
    return {"id": c["chunk_id"], "text": c["text"], "source_id": c["document_id"],
            "source": c["source"], "page": c["page"], "metadata": c.get("metadata", {})}


def convert_question(q: dict) -> dict:
    out = {"id": q["id"], "split": q["split"], "question": q["question"],
           "answerable": True, "expected_behavior": "search_and_answer",
           "expected_answer": q["expected_answer"],
           "gold": [{"source_id": q["gold_source_id"], "page": q["gold_page"],
                     "pages": q.get("gold_pages") or [q["gold_page"]],
                     "evidence": q["evidence_quote"]}],
           "type": q.get("type"), "filter": q.get("filter")}
    return out


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--day6", type=Path, default=DEFAULT_DAY6, help="thư mục repo Day 6")
    ap.add_argument("--output", type=Path, default=ROOT / "data" / "day6")
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    for strategy in ("A", "B"):
        raw = read_jsonl(args.day6 / "starter" / "results" / f"chunks_{strategy}.jsonl")
        chunks = [convert_chunk(c) for c in raw]
        ids = [c["id"] for c in chunks]
        if len(ids) != len(set(ids)):
            raise ValueError(f"chunk id trùng trong strategy {strategy}")
        write_json(args.output / f"chunks_{strategy}.json", chunks)
        print(f"chunks_{strategy}.json: {len(chunks)} chunk")

    bench = json.loads((args.day6 / "benchmark" / "questions.json").read_text(encoding="utf-8"))
    questions = [convert_question(q) for q in bench["questions"]]
    write_json(args.output / "questions_day6.json", questions)
    by_split: dict[str, int] = {}
    for q in questions:
        by_split[q["split"]] = by_split.get(q["split"], 0) + 1
    print(f"questions_day6.json: {len(questions)} câu {by_split}")


if __name__ == "__main__":
    main()
