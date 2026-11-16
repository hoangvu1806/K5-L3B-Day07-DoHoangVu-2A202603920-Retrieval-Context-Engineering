"""Ba phương pháp retrieval trên kho Day 6 (chunk B, collection day06_rhm_b).

- DenseRetriever: embedding query bằng đúng model Day 6, cosine exact trên Qdrant.
- BM25Retriever: BM25Okapi trên văn bản chunk; tách theo âm tiết hoặc theo từ
  (underthesea), tùy chọn ghép tên bệnh và tên mục vào văn bản được index.
- HybridRetriever: hợp nhất hai danh sách bằng Reciprocal Rank Fusion (chỉ dùng
  thứ hạng, không cộng score khác thang đo).

Mọi retriever trả về list dict: id, text, source_id, source, page, metadata,
score, rank, retriever. Filter chỉ nhận các khóa metadata do người dùng cung cấp.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[1]
FILTER_KEYS = {"disease_no"}


def load_chunks(strategy: str = "B") -> list[dict]:
    return json.loads((ROOT / "data" / "day6" / f"chunks_{strategy}.json").read_text(encoding="utf-8"))


def _check_filters(filters: dict | None) -> dict:
    filters = filters or {}
    unknown = set(filters) - FILTER_KEYS
    if unknown:
        raise ValueError(f"filter không hỗ trợ: {unknown}")
    return filters


def _match(chunk: dict, filters: dict) -> bool:
    return all(chunk["metadata"].get(k) == v for k, v in filters.items())


class QueryEmbeddingCache:
    """Cache vector query trên đĩa để chạy lại thí nghiệm không tốn thêm API.

    Khóa gồm tên model và nội dung query, nên đổi model sẽ không dùng nhầm vector cũ.
    """

    def __init__(self, embedder, path: Path = ROOT / "cache" / "query_embeddings.jsonl") -> None:
        self.embedder = embedder
        self.path = path
        self.vectors: dict[str, list[float]] = {}
        self.hits = self.misses = 0
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                self.vectors[row["key"]] = row["vector"]

    def _key(self, text: str) -> str:
        return hashlib.sha256(f"{self.embedder.model_name}\n{text}".encode("utf-8")).hexdigest()

    def embed(self, text: str) -> list[float]:
        key = self._key(text)
        if key in self.vectors:
            self.hits += 1
            return self.vectors[key]
        vector = self.embedder.embed_query(text)
        if len(vector) != self.embedder.dimensions:
            raise ValueError("kích thước vector query không khớp index")
        self.misses += 1
        self.vectors[key] = vector
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"key": key, "vector": vector}) + "\n")
        return vector


class DenseRetriever:
    name = "dense"

    def __init__(self, store, embed_cache: QueryEmbeddingCache, chunks: list[dict], strategy: str = "B") -> None:
        self.store = store
        self.cache = embed_cache
        self.strategy = strategy
        self.by_id = {c["id"]: c for c in chunks}

    def search(self, query: str, *, filters: dict | None = None, top_k: int = 3) -> list[dict]:
        filters = _check_filters(filters)
        vector = self.cache.embed(query)
        for attempt in range(3):  # Qdrant tự host đôi khi ngắt kết nối; thử lại, hết lượt thì báo lỗi
            try:
                hits = self.store.search(self.strategy, vector, top_k=top_k, filters=filters or None)
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == 2 or "disconnect" not in str(exc).lower() and "timed out" not in str(exc).lower():
                    raise
                self.retries = getattr(self, "retries", 0) + 1
                time.sleep(1.5 * (attempt + 1))
        out = []
        for rank, h in enumerate(hits, 1):
            chunk = self.by_id.get(h["chunk_id"])
            if chunk is None:
                raise KeyError(f"point {h['chunk_id']} có trong Qdrant nhưng không có trong data/day6")
            out.append({**chunk, "score": h["score"], "rank": rank, "retriever": self.name})
        return out


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text).lower()


def tokenize_syllable(text: str) -> list[str]:
    return re.findall(r"\w+", _norm(text))


def tokenize_word(text: str) -> list[str]:
    from underthesea import word_tokenize  # nạp chậm, chỉ khi cần

    tokens = word_tokenize(_norm(text))
    return [t.replace(" ", "_") for t in tokens if re.search(r"\w", t)]


TOKENIZERS = {"syllable": tokenize_syllable, "word": tokenize_word}


def index_text(chunk: dict, with_title: bool) -> str:
    """Văn bản đưa vào BM25. with_title ghép tên bệnh và tên mục vì chunk B
    thường bắt đầu bằng tiêu đề mục con, không lặp lại tên bệnh."""
    if not with_title:
        return chunk["text"]
    m = chunk["metadata"]
    head = " ".join(str(x) for x in (m.get("disease"), m.get("section"), m.get("subsection")) if x)
    return f"{head}\n{chunk['text']}"


class BM25Retriever:
    def __init__(self, chunks: list[dict], tokenizer: str = "syllable", with_title: bool = False,
                 k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = chunks
        self.tokenize = TOKENIZERS[tokenizer]
        self.name = f"bm25-{tokenizer}{'-title' if with_title else ''}"
        start = time.perf_counter()
        self.bm25 = BM25Okapi([self.tokenize(index_text(c, with_title)) for c in chunks], k1=k1, b=b)
        self.index_seconds = time.perf_counter() - start

    def search(self, query: str, *, filters: dict | None = None, top_k: int = 3) -> list[dict]:
        filters = _check_filters(filters)
        scores = self.bm25.get_scores(self.tokenize(query))
        order = sorted((i for i, c in enumerate(self.chunks) if _match(c, filters)),
                       key=lambda i: (-scores[i], i))
        return [{**self.chunks[i], "score": float(scores[i]), "rank": r, "retriever": self.name}
                for r, i in enumerate(order[:top_k], 1) if scores[i] > 0]


class HybridRetriever:
    """RRF: score = sum 1/(k + rank) qua các retriever; mỗi retriever lấy `candidates` kết quả."""

    def __init__(self, retrievers: list, k: int = 60, candidates: int = 20) -> None:
        self.retrievers = retrievers
        self.k = k
        self.candidates = candidates
        self.name = "hybrid-rrf(" + "+".join(r.name for r in retrievers) + ")"

    def search(self, query: str, *, filters: dict | None = None, top_k: int = 3) -> list[dict]:
        fused: dict[str, dict] = {}
        for r in self.retrievers:
            for hit in r.search(query, filters=filters, top_k=self.candidates):
                row = fused.setdefault(hit["id"], {**hit, "score": 0.0, "components": {}})
                row["score"] += 1.0 / (self.k + hit["rank"])
                row["components"][r.name] = hit["rank"]
        ranked = sorted(fused.values(), key=lambda h: (-h["score"], h["id"]))[:top_k]
        return [{**h, "rank": i, "retriever": self.name} for i, h in enumerate(ranked, 1)]


def build(method: str, *, need_dense: bool = True) -> Any:
    """Tạo retriever theo tên dùng trong config: dense, bm25-syllable, bm25-word,
    bm25-word-title, hybrid (dense + bm25-word-title)."""
    chunks = load_chunks("B")

    def dense():
        import os

        from dotenv import load_dotenv

        from src.day6.embeddings import OpenRouterEmbedder
        from src.day6.store import QdrantStore

        load_dotenv(ROOT / ".env")
        embedder = OpenRouterEmbedder()
        store = QdrantStore(os.environ["QDRANT_URL"], os.environ["QDRANT_API_KEY"], embedder.dimensions)
        return DenseRetriever(store, QueryEmbeddingCache(embedder), chunks)

    if method == "dense":
        return dense()
    if method.startswith("bm25-"):
        parts = method.split("-")
        return BM25Retriever(chunks, tokenizer=parts[1], with_title="title" in parts)
    if method.startswith("hybrid"):
        lexical = method.split(":", 1)[1] if ":" in method else "bm25-word-title"
        return HybridRetriever([dense(), build(lexical)])
    raise ValueError(f"không biết method {method}")
