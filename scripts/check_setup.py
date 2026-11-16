"""Kiểm tra kết nối Day 6 cho Day 7: env, Qdrant, embedding và một lần dense search thật.

So số point trong Qdrant với số chunk trong data/day6/, kiểm tra kích thước vector
khớp model, rồi chạy một truy vấn để xác nhận point id trùng chunk id trong file JSON.
Lỗi thì thoát với mã khác 0; không bao giờ dùng vector giả.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

import os  # noqa: E402

from src.day6.embeddings import OpenRouterEmbedder  # noqa: E402
from src.day6.store import QdrantStore  # noqa: E402

required = ["QDRANT_URL", "QDRANT_API_KEY", "OPENROUTER_API_KEY", "EMBEDDING_MODEL"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    sys.exit(f"Thiếu biến trong .env: {', '.join(missing)}")

embedder = OpenRouterEmbedder()
print(f"Embedding: {embedder.model_name} | dim {embedder.dimensions}")

store = QdrantStore(os.environ["QDRANT_URL"], os.environ["QDRANT_API_KEY"], embedder.dimensions)
ok = True
for strategy in ("A", "B"):
    name = store.collection(strategy)
    size = store.client.get_collection(name).config.params.vectors.size
    n_points = store.count(strategy)
    chunks = json.loads((ROOT / "data" / "day6" / f"chunks_{strategy}.json").read_text(encoding="utf-8"))
    match = n_points == len(chunks) and size == embedder.dimensions
    ok &= match
    print(f"{name}: {n_points} point, vector {size} | file: {len(chunks)} chunk -> {'OK' if match else 'LỆCH'}")

ids_b = {c["id"] for c in json.loads((ROOT / "data" / "day6" / "chunks_B.json").read_text(encoding="utf-8"))}
query = "Răng khôn hàm dưới mọc lệch xử trí thế nào?"
hits = store.search("B", embedder.embed_query(query), top_k=3)
for h in hits:
    print(f"  {h['score']:.3f} p{h['metadata'].get('page')} {h['chunk_id']} in_file={h['chunk_id'] in ids_b}")
ok &= all(h["chunk_id"] in ids_b for h in hits)
print("Setup OK" if ok else "Có điểm lệch, xem ở trên")
sys.exit(0 if ok else 1)
