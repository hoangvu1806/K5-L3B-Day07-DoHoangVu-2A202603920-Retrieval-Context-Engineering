# Tiêu chí chọn cấu hình Day 7

Chốt ngày 2026-11-16, trước mọi lần chạy retrieval hay agent của Day 7. Thời điểm commit file này là bằng chứng.

Chỉ dùng **dev** (24 câu có đáp án, 2 câu thiếu bằng chứng) để chọn. Test (5 + 2 câu) chạy **một lần** cho baseline và cấu hình được chọn, sau khi file `artifacts/selection_decision.json` đã được commit.

## Chọn phương pháp retrieval (không gọi LLM)

1. Evidence Hit@3 trên dev cao nhất; các phương pháp kém nhất không quá 1 câu được coi là ngang nhau.
2. Trong nhóm ngang nhau, chọn Hit@1 cao hơn.
3. Còn ngang thì chọn phương pháp rẻ và nhanh hơn (ít lần gọi API hơn).

## Chọn cấu hình agent

1. **Điều kiện bắt buộc:** từ chối đúng cả 2 câu thiếu bằng chứng của dev. Cấu hình trả lời bừa một câu thiếu bằng chứng bị loại, trừ khi mọi cấu hình đều bị.
2. Điểm trả lời trung bình trên dev (answer_grade 0–2, chấm tay) cao nhất; chênh không quá 1 điểm tổng được coi là ngang nhau.
3. Trong nhóm ngang nhau: Context Evidence Rate cao hơn, rồi chi phí cộng thời gian trung bình thấp hơn.

## Không làm

- Không chỉnh prompt, top-k, budget hay tham số retrieval sau khi xem test. Nếu buộc phải làm, ghi rõ trong báo cáo và không gọi kết quả test là đánh giá độc lập.
- Không đưa gold, expected_answer hay near_miss vào agent hoặc query. Filter chỉ lấy từ trường `filter` (ngữ cảnh người dùng cung cấp trước).
