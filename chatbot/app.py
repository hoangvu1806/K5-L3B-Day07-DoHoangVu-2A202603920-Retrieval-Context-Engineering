"""Web UI cho agent Day 7 (FastAPI + Jinja, cùng kiểu Day 6).

Chạy từ thư mục gốc repo:
    python -m uvicorn chatbot.app:app --port 8000

Khi khởi động, engine dựng sẵn index BM25 và mở kết nối Qdrant/embedding,
nên câu hỏi đầu tiên không phải chờ.
"""
import json
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .benchmark import load_benchmark
from .engine import AgentEngine, load_diseases

HERE = Path(__file__).resolve().parent
log = logging.getLogger("uvicorn.error")

_engine: AgentEngine | None = None
_lock = threading.Lock()
_warm_error: str | None = None


def engine() -> AgentEngine:
    global _engine
    with _lock:
        if _engine is None:
            _engine = AgentEngine()
        return _engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _warm_error
    try:
        info = engine().warmup()
        log.info("Agent warmup xong: index %ss, dense %ss", info["index_s"], info["dense_s"])
    except Exception as exc:  # noqa: BLE001 - vẫn phục vụ; báo lỗi ở /api/health
        _warm_error = f"{type(exc).__name__}: {exc}"
        log.warning("Warmup lỗi: %s", _warm_error)
    yield


app = FastAPI(title="RHM Agent · Day 7", lifespan=lifespan)
templates = Jinja2Templates(directory=str(HERE / "templates"))


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    config: str | None = None
    disease_no: int | None = Field(default=None, ge=1, le=57)


SAMPLES = [
    {"q": "Khi nào thì nhổ răng khôn mọc lệch, và vì sao?", "disease": None},
    {"q": "Đau dây thần kinh V không rõ nguyên nhân thì khi nào được mổ?", "disease": None},
    {"q": "Khi cố định hai hàm bằng nút Ivy thì giữ trong bao lâu?", "disease": 54},
    {"q": "Trong viêm quanh Implant, xương tiêu đến mức nào thì nên tháo Implant?", "disease": None},
    {"q": "Đeo khay trong suốt Invisalign bao nhiêu giờ mỗi ngày?", "disease": None},
    {"q": "Quyết định ban hành tài liệu này có hiệu lực từ khi nào?", "disease": None},
]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    eng = engine()
    configs = [{"name": c.name, "description": c.description, "top_k": c.top_k, "retriever": c.retriever}
               for c in eng.configs.values()]
    return templates.TemplateResponse(request, "index.html", {
        "samples": SAMPLES, "diseases": load_diseases(), "configs": configs, "default": eng.default})


@app.get("/api/benchmark")
def benchmark():
    try:
        return load_benchmark()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Thiếu file kết quả: {exc.filename}")


@app.get("/api/health")
def health():
    warm = _engine.warm if _engine else {"ready": False}
    return {**warm, "error": _warm_error}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/ask/stream")
def ask_stream(body: AskRequest):
    """Server-Sent Events: meta, search* (mỗi lượt tool call), answer, done; lỗi trả error."""
    def events():
        try:
            for event, data in engine().answer_stream(body.query.strip(), body.config, body.disease_no):
                yield _sse(event, data)
        except Exception as exc:  # noqa: BLE001
            yield _sse("error", {"detail": f"{type(exc).__name__}: {exc}"})
    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
