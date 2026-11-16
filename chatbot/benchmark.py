"""Đọc kết quả benchmark Day 7 đã chạy cho tab Benchmark (không chạy lại gì).

Nguồn:
  benchmark/questions.json                      câu hỏi, gold, câu thiếu bằng chứng
  results/retrieval/<split>/summary.json        Hit@1/@3/@5, MRR theo phương pháp
  results/retrieval/<split>/<method>.traces.json  top-5 mỗi câu
  results/agent/<split>/summary.json            chỉ số agent (tự tính + nhãn chấm tay)
  results/agent/<split>/<config>/traces.json    trace agent từng câu
  results/agent/<split>/<config>/reviews.json   nhãn chấm tay
  artifacts/selection_decision.json             cấu hình được chọn trên dev
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _opt(path: Path) -> Any:
    return _json(path) if path.exists() else None


def load_benchmark() -> dict[str, Any]:
    questions = _json(ROOT / "benchmark" / "questions.json")
    configs = _json(ROOT / "configs" / "agent_configs.json")
    out: dict[str, Any] = {"questions": questions, "configs": configs,
                           "selection": _opt(ROOT / "artifacts" / "selection_decision.json"),
                           "retrieval": {}, "agent": {}}
    for split in ("dev", "test"):
        rdir = ROOT / "results" / "retrieval" / split
        summary = _opt(rdir / "summary.json")
        if summary:
            out["retrieval"][split] = {
                "summary": summary,
                "ranks": {m: {t["query_id"]: t["hit_rank"] for t in _json(rdir / f"{m}.traces.json")}
                          for m in summary["methods"]}}
        adir = ROOT / "results" / "agent" / split
        if not adir.exists():
            continue
        block: dict[str, Any] = {"summary": _opt(adir / "summary.json"), "runs": {}}
        for cfg in configs:
            traces = _opt(adir / cfg["name"] / "traces.json")
            if traces is None:
                continue
            reviews = {r["query_id"]: r for r in (_opt(adir / cfg["name"] / "reviews.json") or [])}
            block["runs"][cfg["name"]] = {t["query_id"]: {
                "status": t["status"], "answer": t["answer"], "citation_refs": t["citation_refs"],
                "searches": [{"query": e["query"], "added_refs": e["added_refs"],
                              "results": e["results"][:5]} for e in t["events"] if e["event"] == "search"],
                "context": [{k: c[k] for k in ("ref", "id", "page", "pages", "disease_no", "text")}
                            for c in t["context"]],
                "seconds": t["seconds"], "cost": t["usage"].get("llm_cost_usd"), "error": t.get("error"),
                "review": reviews.get(t["query_id"])} for t in traces}
        out["agent"][split] = block
    return out
