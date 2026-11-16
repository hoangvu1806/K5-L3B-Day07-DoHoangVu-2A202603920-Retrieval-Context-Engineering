# Benchmark Day 7

Tạo bằng `python scripts/build_benchmark.py`, kiểm tra bằng `python scripts/verify_benchmark.py` (không gọi API). Chốt ngày 2026-11-16, trước mọi lần chạy retrieval hay agent của Day 7.

| Split | Có đáp án | Thiếu bằng chứng | Nguồn |
|---|---:|---:|---|
| dev | 24 | 2 (`u01`, `u02`) | 18 câu dev Day 6 (`d01`–`d18`) + 6 câu test Day 6 (`t01`–`t06`) |
| test | 5 (`n01`–`n05`) | 2 (`u03`, `u04`) | Câu mới |

## Vì sao viết test mới

Test Day 6 không được dùng để chỉnh cấu hình Day 6, nhưng kết quả của nó đã được xem (biết câu nào trượt). Day 7 thử nhiều phương pháp và cấu hình hơn, nên dùng lại test cũ thì khó gọi là đánh giá độc lập. Sáu câu đó được chuyển sang dev và gắn `note`. Năm câu test mới lấy từ các bệnh chưa có câu nào trong Day 6 (bệnh 12, 26, 36, 44, 54), phủ đủ các loại: `truc_tiep`, `dieu_kien`, `dien_dat_lai`, `metadata_filter`.

## Câu có đáp án

Schema theo `data/README.md`: `gold` là danh sách `{source_id, page, pages, evidence}`. Evidence được so sau khi gộp khoảng trắng và phải nằm trọn trong một chunk có trang gold trong `metadata.pages` (quy ước Day 6). Trên chunk B mọi câu đều đạt. Trên chunk A có 3 câu (`d04`, `n04`, `n05`) bị cắt ngang qua hai cửa sổ 500 ký tự, nên không thể hit trên A.

`filter` (ví dụ `{"disease_no": 54}` ở `n02`) là ngữ cảnh người dùng đưa trước khi tìm, không suy ra từ đáp án. Câu `n02` cần filter vì bệnh 55 (gãy xương hàm trên) có đoạn cố định hai hàm tương tự.

## Câu thiếu bằng chứng

Mỗi câu gần chủ đề và có một đoạn dễ gây nhầm (`near_miss`), để kiểm tra agent có từ chối hay suy diễn:

| ID | Câu hỏi (rút gọn) | Đoạn dễ nhầm | Vì sao thiếu |
|---|---|---|---|
| u01 | Nồng độ hydrogen peroxide khi tẩy trắng răng nhiễm màu tetracycline | tr. 47: "Có thể tiến hành tẩy trắng răng khi răng bị nhiễm màu" | Không có thuốc, nồng độ, quy trình |
| u02 | Thuốc trị nấm miệng do Candida ở trẻ | tr. 170: "nấm mốc từ gạo, lạc" (nguyên nhân ung thư) | Không có bệnh nấm miệng |
| u03 | Số giờ đeo khay trong suốt (Invisalign) cho sai khớp cắn loại II | tr. 64: Headgear "ít nhất 14 h/ngày" | Chỉ có Headgear và khí cụ chức năng; trả lời "14 giờ" là sai |
| u04 | Bảo hiểm y tế chi trả bao nhiêu phần trăm cấy Implant | tr. 1: "Bảo hiểm Xã hội Việt Nam (để phối hợp)" trong mục Nơi nhận | Không có thông tin chi phí |

Cách kiểm tra: quét từ khóa (`absence_check.keywords`) trên toàn bộ 547 chunk A và 526 chunk B, rồi đọc tay các đoạn quanh `near_miss` cùng mục điều trị của các bệnh liên quan. Từ khóa trúng mà không liên quan thì ghi vào `allowed_hits` kèm lý do (`u01`: "nồng độ" ở tr. 144 là nồng độ estradiol). Các câu này không tính vào mẫu số retrieval metrics. Chúng chỉ dùng để đo abstention của agent.
