"""Bọc agent Day 7 cho chatbot: dùng đúng Agent, prompt và cấu hình của benchmark.

Retriever được tạo một lần và dùng chung giữa các cấu hình (dense, BM25, hybrid).
answer_stream() chạy agent trong một thread và đẩy từng sự kiện (mỗi lượt search,
câu trả lời cuối) ra hàng đợi để server gửi dạng Server-Sent Events.
"""
from __future__ import annotations

import json
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Any, Iterator

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.agent import Agent, AgentConfig, format_chunk, result_to_dict  # noqa: E402
from src.retrieval import HybridRetriever, build  # noqa: E402


def load_configs() -> dict[str, AgentConfig]:
    rows = json.loads((ROOT / "configs" / "agent_configs.json").read_text(encoding="utf-8"))
    return {r["name"]: AgentConfig(**r) for r in rows}


def selected_config() -> str | None:
    path = ROOT / "artifacts" / "selection_decision.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")).get("chosen")
    return None


def load_diseases() -> list[dict]:
    manifest = json.loads((ROOT / "data" / "day6" / "manifest.json").read_text(encoding="utf-8"))
    return [{"no": d["disease_no"], "title": d["title"]} for d in manifest["diseases"]]


class AgentEngine:
    def __init__(self) -> None:
        self.configs = load_configs()
        self.default = selected_config() or next(iter(self.configs))
        self._retrievers: dict[str, Any] = {}
        self._lock = threading.Lock()
        self.warm: dict[str, Any] = {"ready": False}

    def retriever(self, method: str):
        with self._lock:
            if "dense" not in self._retrievers:
                self._retrievers["dense"] = build("dense")
            if method not in self._retrievers:
                if method.startswith("hybrid"):
                    lexical = method.split(":", 1)[1] if ":" in method else "bm25-word-title"
                    if lexical not in self._retrievers:
                        self._retrievers[lexical] = build(lexical)
                    self._retrievers[method] = HybridRetriever([self._retrievers["dense"], self._retrievers[lexical]])
                else:
                    self._retrievers[method] = build(method)
            return self._retrievers[method]

    def warmup(self) -> dict[str, Any]:
        t: dict[str, Any] = {}
        t0 = time.perf_counter()
        for cfg in self.configs.values():
            self.retriever(cfg.retriever)
        t["index_s"] = round(time.perf_counter() - t0, 2)
        t0 = time.perf_counter()
        self.retriever("dense").search("khởi động hệ thống", top_k=1)
        t["dense_s"] = round(time.perf_counter() - t0, 2)
        self.warm = {"ready": True, "default_config": self.default, **t}
        return self.warm

    def answer_stream(self, question: str, config: str | None, disease_no: int | None) -> Iterator[tuple[str, dict]]:
        cfg = self.configs.get(config or self.default)
        if cfg is None:
            raise ValueError(f"không có cấu hình {config}")
        filters = {"disease_no": disease_no} if disease_no else None
        agent = Agent(cfg, self.retriever(cfg.retriever))
        yield "meta", {"config": cfg.name, "description": cfg.description, "retriever": agent.retriever.name,
                       "model": cfg.model, "top_k": cfg.top_k, "budget_chars": cfg.budget_chars,
                       "max_searches": cfg.max_searches, "filter": filters}

        q: queue.Queue = queue.Queue()
        chunks_by_id: dict[str, dict] = {}
        retr = agent.retriever
        original = retr.search

        def spy(query, *, filters=None, top_k=3):  # giữ text chunk để UI hiển thị nguồn
            res = original(query, filters=filters, top_k=top_k)
            for r in res:
                chunks_by_id[r["id"]] = r
            return res

        def on_event(e: dict) -> None:
            if e["event"] == "search":
                added = [{"ref": ref, **_source(chunks_by_id[cid])} for ref, cid in e["added_refs"].items()]
                q.put(("search", {"query": e["query"], "ms": e["ms"], "results": e["results"],
                                  "added": added, "skipped_duplicate": len(e["skipped_duplicate"]),
                                  "skipped_budget": len(e["skipped_budget"]), "context_chars": e["context_chars"]}))

        def worker() -> None:
            agent.retriever = _Proxy(retr, spy)
            try:
                q.put(("result", result_to_dict(agent.run(question, filters=filters, on_event=on_event))))
            except Exception as exc:  # noqa: BLE001
                q.put(("error", {"detail": f"{type(exc).__name__}: {exc}"}))

        threading.Thread(target=worker, daemon=True).start()
        while True:
            kind, data = q.get()
            if kind == "search":
                yield "search", data
            elif kind == "error":
                yield "error", data
                return
            else:
                if data["status"] == "error":
                    yield "error", {"detail": data["error"]}
                    return
                yield "answer", {"status": data["status"], "answer": data["answer"],
                                 "citation_refs": data["citation_refs"], "invalid_refs": data["invalid_refs"]}
                yield "done", {"seconds": data["seconds"], **data["usage"],
                               "searches": sum(e["event"] == "search" for e in data["events"])}
                return


class _Proxy:
    """Giữ nguyên name của retriever nhưng chặn search để lấy text chunk."""

    def __init__(self, inner, search) -> None:
        self.name = inner.name
        self.search = search


def _source(c: dict) -> dict:
    m = c["metadata"]
    return {"chunk_id": c["id"], "score": round(c["score"], 4), "rank": c["rank"],
            "disease_no": m.get("disease_no"), "disease": m.get("disease"), "section": m.get("section"),
            "subsection": m.get("subsection"), "special_id": m.get("special_id"),
            "pages": m.get("pages") or [c["page"]], "text": c["text"], "header": format_chunk("", c).split("\n")[0]}
