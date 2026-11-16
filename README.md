# Day 7 — Agentic RAG

> **Bài làm:** Đỗ Hoàng Vũ · 2A202603920 · L3B. Tiếp nối [Day 6](https://github.com/hoangvu1806/K5-L3B-Day06-DoHoangVu-2A202603920-DataIngestionEngineering) (tài liệu Răng Hàm Mặt, QĐ 3108/QĐ-BYT).
>
> **Setup & chạy tái lập**
> ```bash
> pip install -r requirements.txt
> cp .env.example .env            # điền Qdrant + OpenRouter
> python scripts/prepare_day6.py  # chunk + benchmark Day 6 -> data/day6/
> python scripts/verify_benchmark.py
> python scripts/check_setup.py   # so Qdrant với file, chạy 1 dense search thật
> PYTHONUTF8=1 python -m unittest discover -s tests -v   # Windows cần UTF-8 mode
>
> # Đánh giá retrieval & chạy agent (dev / test)
> PYTHONUTF8=1 python scripts/eval_retrieval.py --split dev --methods dense bm25-syllable bm25-word bm25-word-title hybrid
> PYTHONUTF8=1 python scripts/run_agent.py --config G0-dense --split dev
> PYTHONUTF8=1 python scripts/run_agent.py --config G1-hybrid --split dev
> PYTHONUTF8=1 python scripts/run_agent.py --config G2-hybrid-k5 --split dev
> PYTHONUTF8=1 python scripts/write_reviews.py --split dev
> PYTHONUTF8=1 python scripts/agent_report.py --split dev --configs G0-dense G1-hybrid G2-hybrid-k5
>
> # Đánh giá trên test (sau khi chốt cấu hình ở artifacts/selection_decision.json)
> PYTHONUTF8=1 python scripts/eval_retrieval.py --split test --methods dense bm25-syllable bm25-word bm25-word-title hybrid
> PYTHONUTF8=1 python scripts/run_agent.py --config G0-dense --split test
> PYTHONUTF8=1 python scripts/run_agent.py --config G2-hybrid-k5 --split test
> PYTHONUTF8=1 python scripts/write_reviews.py --split test
> PYTHONUTF8=1 python scripts/agent_report.py --split test --configs G0-dense G2-hybrid-k5
>
> # Web UI chatbot (tùy chọn, cần cài thêm chatbot/requirements.txt)
> pip install -r chatbot/requirements.txt
> python -m uvicorn chatbot.app:app --port 8000
> ```
> Dữ liệu Day 6: `day06_rhm_a` (547 chunk, cửa sổ 500 ký tự) và `day06_rhm_b` (526 chunk, theo cấu trúc), embedding `google/gemini-embedding-2` 3072 chiều, cosine. Chunk id trong `data/day6/*.json` trùng point id Qdrant. Code Qdrant/embedding lấy nguyên từ Day 6 trong `src/day6/`. `starter/baseline.py` được sửa để so evidence sau khi gộp khoảng trắng và theo danh sách trang của chunk, đúng quy ước benchmark Day 6.

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

Dùng embedding và vector store từ Day 6 để xây một agent biết tìm bằng chứng, trả lời có nguồn và nhận biết khi không đủ thông tin. Bạn tự chọn kiến trúc, số tool và cách tổ chức retrieval.

> **Tùy chọn:** [Gợi ý dùng AI để lập trình](AGENT_SETUP.md) giúp bạn làm lab; phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối dữ liệu, embedding và vector store Day 6.
2. Xây agent dùng model thật và ít nhất một khả năng truy xuất dữ liệu. Agent có thể dùng nhiều tool và nhiều lượt gọi.
3. Thử **ít nhất 3 phương pháp retrieval khác nhau**, trong đó có dense retrieval dùng vector store Day 6. Tự chọn các phương pháp còn lại; xem [gợi ý](GUIDE.md#2-thử-các-phương-pháp-retrieval).
4. Thử nhiều cấu hình, benchmark, phân tích lỗi và chọn cấu hình tốt trên **dev**; sau đó đánh giá trên **test**.

Benchmark tối thiểu có **24 câu**: dev gồm 15 câu có đáp án và 2 câu thiếu bằng chứng; test gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Xem [benchmark](BENCHMARK.md) và [rubric](RUBRIC.md).

## Thử thách nâng cao · +15 điểm

Index một tài liệu thực tế từ **100 trang** có bảng, ảnh và biểu đồ; xây agent truy xuất và trả lời các câu hỏi về nội dung đó. Hoàn thành [thử thách nâng cao](ADVANCED.md) và đạt **ít nhất 90% benchmark test** để nhận 15 điểm bonus. Phần cơ bản tối đa 85 điểm; toàn bài tối đa 100 điểm.

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [rubric](RUBRIC.md) và [quy tắc](RULES.md).
2. Tạo repo cá nhân theo [cách nộp bài](SUBMISSION.md), chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Dùng hoặc thay thế [starter](starter/README.md); bạn cần kết nối model và vector store thật.
4. Chạy `python -m unittest discover -s tests -v`. Test mock chỉ kiểm tra code, không phải benchmark agent thật.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo](report/individual/MSSV_HoTen.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.
