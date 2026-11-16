"""So sánh các phương pháp retrieval trên cùng corpus (chunk B), câu hỏi và nhãn.

Chạy query gốc của benchmark, filter lấy từ trường `filter` khi có.
Báo Hit@1, Evidence Hit@3, Hit@5, MRR@10, thời gian và chi phí embedding.
Câu thiếu bằng chứng không vào mẫu số.

  python scripts/eval_retrieval.py --split dev --methods dense bm25-syllable bm25-word bm25-word-title hybrid
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evidence import first_hit_rank  # noqa: E402
from src.retrieval import build  # noqa: E402


def frac(n: int, N: int) -> dict:
    return {"n": n, "N": N, "rate": round(n / N, 3) if N else None, "text": f"{n}/{N}"}


def embed_stats(retriever) -> tuple[int, float]:
    """Số lần gọi embedding API và chi phí USD (lấy từ embedder Day 6)."""
    parts = getattr(retriever, "retrievers", [retriever])
    for r in parts:
        if hasattr(r, "cache"):
            return r.cache.misses, r.cache.embedder.cost_usd
    return 0, 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--methods", nargs="+", required=True)
    ap.add_argument("--no-filter", action="store_true", help="bỏ filter người dùng để đo riêng tác động")
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    questions = [q for q in json.loads((ROOT / "benchmark" / "questions.json").read_text(encoding="utf-8"))
                 if q["split"] == args.split and q["answerable"]]
    tag = "-nofilter" if args.no_filter else ""
    out_dir = args.output or ROOT / "results" / "retrieval" / f"{args.split}{tag}"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {}
    for method in args.methods:
        retriever = build(method)
        traces, latencies = [], []
        for q in questions:
            filters = None if args.no_filter else q.get("filter")
            start = time.perf_counter()
            results = retriever.search(q["question"], filters=filters, top_k=10)
            latencies.append((time.perf_counter() - start) * 1000)
            rank = first_hit_rank(results, q["gold"])
            traces.append({"query_id": q["id"], "query": q["question"], "filter": filters, "hit_rank": rank,
                           "top": [{"rank": r["rank"], "id": r["id"], "page": r["page"],
                                    "disease_no": r["metadata"].get("disease_no"),
                                    "score": round(r["score"], 5), **({"components": r["components"]}
                                                                      if "components" in r else {})}
                                   for r in results[:5]]})
        calls, cost = embed_stats(retriever)
        N = len(questions)
        ranks = [t["hit_rank"] for t in traces]
        summary[method] = {
            "retriever": retriever.name,
            "hit1": frac(sum(r == 1 for r in ranks if r), N),
            "evidence_hit3": frac(sum(1 for r in ranks if r and r <= 3), N),
            "hit5": frac(sum(1 for r in ranks if r and r <= 5), N),
            "mrr10": round(sum(1 / r for r in ranks if r) / N, 3),
            "misses_hit3": [t["query_id"] for t in traces if not t["hit_rank"] or t["hit_rank"] > 3],
            "median_ms": round(statistics.median(latencies), 1),
            "embedding_api_calls_this_run": calls,
            "embedding_cost_usd_this_run": round(cost, 6),
        }
        (out_dir / f"{method.replace(':', '_')}.traces.json").write_text(
            json.dumps(traces, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        s = summary[method]
        print(f"{method:18} Hit@1 {s['hit1']['text']:6} Hit@3 {s['evidence_hit3']['text']:6} "
              f"Hit@5 {s['hit5']['text']:6} MRR {s['mrr10']:.3f} {s['median_ms']:7.1f} ms  miss@3 {s['misses_hit3']}")
    (out_dir / "summary.json").write_text(json.dumps(
        {"split": args.split, "n_questions": len(questions), "filter": not args.no_filter,
         "corpus": "data/day6/chunks_B.json (526 chunk, Qdrant day06_rhm_b)", "methods": summary},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
