"""Chạy agent thật trên một split với một cấu hình trong configs/agent_configs.json.

  python scripts/run_agent.py --config G1-hybrid --split dev

Ghi results/agent/<split>/<config>/traces.json: mỗi câu gồm query_id, status,
answer, citations, events (tool call, tham số, kết quả), context cuối, usage,
thời gian, lỗi. Kèm cases.json theo định dạng starter/agent_metrics.py.
Gold không đi vào agent; chỉ được dùng ở bước tính Context Evidence Rate sau đó.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.agent import Agent, AgentConfig, result_to_dict  # noqa: E402
from src.retrieval import build  # noqa: E402


def load_config(name: str) -> AgentConfig:
    for c in json.loads((ROOT / "configs" / "agent_configs.json").read_text(encoding="utf-8")):
        if c["name"] == name:
            return AgentConfig(**c)
    raise SystemExit(f"không có cấu hình {name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--only", nargs="*", help="chỉ chạy các query id này (debug)")
    args = ap.parse_args()

    if args.split == "test" and not (ROOT / "artifacts" / "selection_decision.json").exists():
        raise SystemExit("Chưa có artifacts/selection_decision.json: chốt cấu hình trên dev trước khi chạy test.")

    cfg = load_config(args.config)
    agent = Agent(cfg, build(cfg.retriever))
    questions = [q for q in json.loads((ROOT / "benchmark" / "questions.json").read_text(encoding="utf-8"))
                 if q["split"] == args.split and (not args.only or q["id"] in args.only)]
    out_dir = ROOT / "results" / "agent" / args.split / cfg.name
    out_dir.mkdir(parents=True, exist_ok=True)

    traces = []
    for q in questions:
        res = result_to_dict(agent.run(q["question"], filters=q.get("filter")))
        traces.append({"query_id": q["id"], "question": q["question"], "filter": q.get("filter"),
                       "config": cfg.name, "model": cfg.model, **res})
        n_search = sum(e["event"] == "search" for e in res["events"])
        print(f"{q['id']:4} {res['status']:8} searches={n_search} refs={res['citation_refs']} "
              f"{res['seconds']:5.1f}s ${res['usage'].get('llm_cost_usd', 0):.5f} | {res['answer'][:90]!r}")

    (out_dir / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(cfg.__dict__, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    cases = [{"id": q["id"], "split": q["split"], "answerable": q["answerable"]} for q in questions]
    (out_dir / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"-> {out_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
