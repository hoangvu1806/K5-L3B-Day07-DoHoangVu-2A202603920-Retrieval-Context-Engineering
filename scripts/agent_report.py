"""Tổng hợp chỉ số agent cho một split, từ trace và nhãn chấm tay.

Tự tính (không cần nhãn): Context Evidence Rate (evidence gold nằm trong context cuối),
tool use, phân bố số lượt search, thời gian, token, chi phí, số câu từ chối.
Từ nhãn trong reviews.json (chấm tay): answer_grade, citation_support, abstention_correct,
tổng hợp bằng starter/agent_metrics.py.

  python scripts/agent_report.py --split dev --configs G0-dense G1-hybrid G2-hybrid-k5
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter"))

from agent_metrics import aggregate  # noqa: E402

from src.evidence import chunk_has_evidence  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def frac(n: int, N: int) -> str:
    return f"{n}/{N} ({n / N:.0%})" if N else "0/0 (không áp dụng)"


def auto_metrics(questions: dict, traces: list[dict]) -> dict:
    ok = [t for t in traces if t["status"] != "error"]
    answerable = [t for t in ok if questions[t["query_id"]]["answerable"]]
    ctx_hit = [t["query_id"] for t in answerable
               if any(chunk_has_evidence({"source_id": "byt-rhm-3108-2015", "page": c["page"],
                                          "metadata": {"pages": c["pages"]}, "text": c["text"]},
                                         questions[t["query_id"]]["gold"]) for c in t["context"])]
    searches = [sum(e["event"] == "search" for e in t["events"]) for t in ok]
    secs = [t["seconds"] for t in ok]
    cost = [t["usage"]["llm_cost_usd"] for t in ok]
    ctx_chars = [max([e["context_chars"] for e in t["events"] if e["event"] == "search"] or [0]) for t in ok]
    return {
        "runs": len(traces), "errors": len(traces) - len(ok),
        "context_evidence_rate": frac(len(ctx_hit), len(answerable)),
        "context_evidence_n": len(ctx_hit),
        "context_misses": [t["query_id"] for t in answerable if t["query_id"] not in ctx_hit],
        "answered": sum(t["status"] == "answered" for t in ok),
        "abstained": sum(t["status"] == "abstain" for t in ok),
        "search_count_distribution": dict(sorted(Counter(searches).items())),
        "mean_searches": round(statistics.mean(searches), 2) if searches else None,
        "mean_context_chars": round(statistics.mean(ctx_chars)) if ctx_chars else None,
        "mean_seconds": round(statistics.mean(secs), 2) if secs else None,
        "median_seconds": round(statistics.median(secs), 2) if secs else None,
        "total_llm_cost_usd": round(sum(cost), 5),
        "mean_prompt_tokens": round(statistics.mean(t["usage"]["prompt_tokens"] for t in ok)) if ok else None,
        "invalid_citation_refs": sum(len(t["invalid_refs"]) for t in ok),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--configs", nargs="+", required=True)
    args = ap.parse_args()
    questions = {q["id"]: q for q in load(ROOT / "benchmark" / "questions.json")}
    report = {}
    for name in args.configs:
        d = ROOT / "results" / "agent" / args.split / name
        traces = load(d / "traces.json")
        row = {"auto": auto_metrics(questions, traces)}
        reviews_path = d / "reviews.json"
        if reviews_path.exists():
            labeled = aggregate(load(d / "cases.json"), traces, load(reviews_path))
            ga = labeled["grounded_answer"]
            ga["sum"] = ga["1"] + 2 * ga["2"]
            row["labeled"] = labeled
        report[name] = row
        a = row["auto"]
        line = (f"{name:14} ctx {a['context_evidence_rate']:12} ans/abst {a['answered']}/{a['abstained']} "
                f"searches {a['search_count_distribution']} {a['mean_seconds']}s ${a['total_llm_cost_usd']}")
        if "labeled" in row:
            L = row["labeled"]
            line += (f" | grade {L['grounded_answer']['sum']}/{2 * L['grounded_answer']['N']} "
                     f"{ {k: L['grounded_answer'][k] for k in '012'} } "
                     f"cit {L['citation_validity']['n']}/{L['citation_validity']['N']} "
                     f"abst {L['abstention']['n']}/{L['abstention']['N']} "
                     f"false_abst {L['false_abstention']['n']}/{L['false_abstention']['N']}")
        print(line)
    out = ROOT / "results" / "agent" / args.split / "summary.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
