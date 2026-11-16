"""Test offline cho code Day 7 (BM25, RRF, evidence, vòng lặp agent).

Client model và retriever ở đây là giả, chỉ để kiểm tra logic; không phải benchmark.
"""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import ABSTAIN_PREFIX, Agent, AgentConfig  # noqa: E402
from src.evidence import chunk_has_evidence, first_hit_rank  # noqa: E402
from src.retrieval import BM25Retriever, HybridRetriever  # noqa: E402


def chunk(cid, text, disease_no=None, page=1):
    return {"id": cid, "text": text, "source_id": "doc", "source": "x.pdf", "page": page,
            "metadata": {"pages": [page], "disease_no": disease_no, "disease": f"BỆNH {disease_no}"}}


CHUNKS = [chunk("a", "nhổ răng khôn mọc lệch càng sớm càng tốt", 1, 9),
          chunk("b", "điều trị áp xe má bằng rạch dẫn lưu", 30, 118),
          chunk("c", "gãy xương hàm cố định hai hàm 4- 6 tuần", 54, 191)]


class FakeRetriever:
    name = "fake"

    def __init__(self, ranked):
        self.ranked = ranked

    def search(self, query, *, filters=None, top_k=3):
        return [{**c, "score": 1.0 / i, "rank": i} for i, c in enumerate(self.ranked[:top_k], 1)]


class FakeClient:
    """Trả lần lượt các message đã định sẵn, theo giao diện openai chat.completions."""

    def __init__(self, messages):
        self.queue = list(messages)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self.calls = []

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        msg = self.queue.pop(0)
        usage = SimpleNamespace(model_dump=lambda: {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001})
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage)


def tool_call(query, cid="t1"):
    fn = SimpleNamespace(name="search_documents", arguments='{"query": "%s"}' % query)
    tc = SimpleNamespace(id=cid, function=fn)
    tc.model_dump = lambda: {"id": cid, "type": "function",
                             "function": {"name": fn.name, "arguments": fn.arguments}}
    return SimpleNamespace(content="", tool_calls=[tc])


def final(text):
    return SimpleNamespace(content=text, tool_calls=None)


class RetrievalTests(unittest.TestCase):
    def test_bm25_ranks_and_filters(self):
        bm25 = BM25Retriever(CHUNKS, tokenizer="syllable")
        self.assertEqual(bm25.search("răng khôn mọc lệch", top_k=3)[0]["id"], "a")
        self.assertEqual([r["id"] for r in bm25.search("cố định hai hàm", filters={"disease_no": 30})], [])
        with self.assertRaises(ValueError):
            bm25.search("x", filters={"page": 1})

    def test_title_enrichment_matches_disease_name(self):
        plain = BM25Retriever(CHUNKS, tokenizer="syllable")
        titled = BM25Retriever(CHUNKS, tokenizer="syllable", with_title=True)
        self.assertEqual(plain.search("bệnh 54", top_k=1), [])
        self.assertEqual(titled.search("bệnh 54", top_k=1)[0]["id"], "c")

    def test_rrf_uses_ranks_only(self):
        r1, r2 = FakeRetriever([CHUNKS[0], CHUNKS[1]]), FakeRetriever([CHUNKS[1], CHUNKS[2]])
        out = HybridRetriever([r1, r2], k=60, candidates=2).search("q", top_k=3)
        self.assertEqual(out[0]["id"], "b")  # có mặt ở cả hai danh sách
        self.assertAlmostEqual(out[0]["score"], 1 / 62 + 1 / 61)
        self.assertEqual([r["rank"] for r in out], [1, 2, 3])

    def test_evidence_normalizes_whitespace_and_pages(self):
        c = chunk("x", "Gõ dọc:\nđau nhẹ.   + Gõ ngang", page=25)
        c["metadata"]["pages"] = [25, 26]
        gold = [{"source_id": "doc", "page": 26, "evidence": "Gõ dọc: đau nhẹ."}]
        self.assertTrue(chunk_has_evidence(c, gold))
        self.assertEqual(first_hit_rank([CHUNKS[0], c], gold), 2)


class AgentTests(unittest.TestCase):
    def make(self, messages, **cfg):
        client = FakeClient(messages)
        config = AgentConfig(name="t", retriever="fake", **cfg)
        return Agent(config, FakeRetriever(CHUNKS), client=client), client

    def test_answer_with_citation_maps_to_chunk_id(self):
        agent, _ = self.make([tool_call("răng khôn"), final("Nhổ càng sớm càng tốt [S1].")])
        res = agent.run("Răng khôn mọc lệch xử trí sao?")
        self.assertEqual(res.status, "answered")
        self.assertEqual(res.citations, ["a"])
        self.assertEqual(sum(e["event"] == "search" for e in res.events), 1)

    def test_abstain_prefix_and_missing_citation(self):
        agent, _ = self.make([tool_call("x"), final(f"{ABSTAIN_PREFIX}: tài liệu không nói.")])
        self.assertEqual(agent.run("?").status, "abstain")
        agent, _ = self.make([tool_call("x"), final("Trả lời không có nguồn.")])
        res = agent.run("?")
        self.assertEqual((res.status, res.citations), ("abstain", []))

    def test_invalid_ref_is_recorded(self):
        agent, _ = self.make([tool_call("x"), final("Ý A [S1], ý B [S9].")])
        res = agent.run("?")
        self.assertEqual(res.invalid_refs, ["S9"])
        self.assertEqual(res.citations, ["a"])

    def test_duplicates_and_budget(self):
        agent, _ = self.make([tool_call("a", "t1"), tool_call("b", "t2"), final("x [S1]")],
                             top_k=1, budget_chars=10_000)
        res = agent.run("?")
        self.assertEqual(res.events[1]["skipped_duplicate"], ["a"])
        agent, _ = self.make([tool_call("a"), final("x")], top_k=3, budget_chars=10)
        res = agent.run("?")
        self.assertEqual(len(res.events[0]["skipped_budget"]), 3)
        self.assertEqual(res.context, [])

    def test_search_limit_removes_tools(self):
        agent, client = self.make([tool_call("a"), final("x [S1]")], max_searches=1)
        agent.run("?")
        self.assertIn("tools", client.calls[0])
        self.assertNotIn("tools", client.calls[1])

    def test_empty_answer_is_retried_once_without_tools(self):
        agent, client = self.make([tool_call("a"), final(""), final("x [S1]")])
        res = agent.run("?")
        self.assertEqual(res.status, "answered")
        self.assertIn("empty_answer_retry", [e["event"] for e in res.events])
        self.assertNotIn("tools", client.calls[2])

    def test_provider_error_is_reported_not_faked(self):
        agent, client = self.make([])
        res = agent.run("?")
        self.assertEqual(res.status, "error")
        self.assertIsNotNone(res.error)

    def test_filter_passed_to_model_and_retriever(self):
        seen = {}

        class Spy(FakeRetriever):
            def search(self, query, *, filters=None, top_k=3):
                seen["filters"] = filters
                return super().search(query, filters=filters, top_k=top_k)

        client = FakeClient([tool_call("x"), final("y [S1]")])
        Agent(AgentConfig(name="t", retriever="spy"), Spy(CHUNKS), client=client).run("?", filters={"disease_no": 54})
        self.assertEqual(seen["filters"], {"disease_no": 54})
        self.assertIn("bệnh số 54", client.calls[0]["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
