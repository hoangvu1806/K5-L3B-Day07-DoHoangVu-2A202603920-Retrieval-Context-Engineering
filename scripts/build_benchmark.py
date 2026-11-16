"""Tạo benchmark/questions.json cho Day 7 từ benchmark Day 6 cộng các câu mới.

- Dev: 18 câu dev Day 6 + 6 câu test Day 6 (chuyển sang dev vì kết quả của
  chúng đã được xem ở Day 6) + 2 câu thiếu bằng chứng.
- Test: 5 câu mới có đáp án (bệnh chưa có câu nào trong Day 6) + 2 câu thiếu bằng chứng.

Câu mới viết theo nội dung tài liệu, chốt trước khi chạy bất kỳ retrieval Day 7 nào.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "byt-rhm-3108-2015"


def gold(page: int, evidence: str, pages: list[int] | None = None) -> list[dict]:
    return [{"source_id": SOURCE_ID, "page": page, "pages": pages or [page], "evidence": evidence}]


NEW_TEST = [
    {"id": "n01", "type": "dieu_kien", "disease_no": 26, "filter": None,
     "question": "Nang nhái sàn miệng trong trường hợp nào thì chỉ định phẫu thuật mở thông nang?",
     "expected_answer": "Khi nang có kích thước lớn gây chèn ép và ảnh hưởng đến chức năng, hoặc nang lớn mà "
                        "tình trạng toàn thân của bệnh nhân không cho phép phẫu thuật kéo dài.",
     "gold": gold(109, "Nang có kích thước lớn gây chèn ép và ảnh hưởng đến chức năng. + Nang có kích thước "
                       "lớn và tình trạng toàn thân của bệnh nhân không cho phép phẫu thuật kéo dài.")},
    {"id": "n02", "type": "metadata_filter", "disease_no": 54, "filter": {"disease_no": 54},
     "question": "Khi cố định hai hàm bằng cung Tiguersted hoặc nút Ivy thì cần giữ cố định trong bao lâu?",
     "expected_answer": "Từ 4 đến 6 tuần.",
     "gold": gold(191, "cố định hai hàm bằng cung Tiguersted hoặc nút Ivy trong thời gian từ 4- 6 tuần")},
    {"id": "n03", "type": "dien_dat_lai", "disease_no": 44, "filter": None,
     "question": "Nếu sỏi ở ống tuyến Wharton được lấy ra muộn thì tuyến dưới hàm sẽ bị ảnh hưởng ra sao?",
     "expected_answer": "Tuyến dưới hàm dễ bị viêm mạn và xơ hóa, dẫn đến phải cắt bỏ tuyến.",
     "gold": gold(158, "Viêm tuyến dưới hàm do sỏi ống tuyến nếu điều trị lấy bỏ sỏi muộn thì tuyến dưới hàm "
                       "dễ viêm mạn xơ hóa, dẫn đến phải cắt bỏ tuyến.")},
    {"id": "n04", "type": "truc_tiep", "disease_no": 12, "filter": None,
     "question": "Khi điều trị nội nha răng viêm quanh cuống, chất gì được đặt vào ống tủy để trung hòa mô viêm "
                 "vùng cuống?",
     "expected_answer": "Ca(OH)2 (canxi hydroxit), vừa trung hòa mô viêm vùng cuống vừa sát khuẩn hệ thống ống tủy.",
     "gold": gold(57, "Đặt Ca(OH)2 trong ống tủy để trung hòa mô viêm vùng cuống, sát khuẩn hệ thống ống tủy.",
                  [56, 57])},
    {"id": "n05", "type": "dieu_kien", "disease_no": 36, "filter": None,
     "question": "U men xương hàm có kích thước lớn, đã phá hủy nhiều xương thì điều trị như thế nào?",
     "expected_answer": "Phẫu thuật cắt bỏ u cùng đoạn xương hàm, phục hồi đoạn xương cắt bỏ bằng ghép xương hàm, "
                        "rồi phục hình răng để phục hồi ăn nhai.",
     "gold": gold(138, "Phẫu thuật cắt bỏ u và đoạn xương hàm. + Phục hồi đoạn xương cắt bỏ bằng kỹ thuật ghép "
                       "xương hàm.")},
]

# Câu thiếu bằng chứng: gần chủ đề, có chỗ trong tài liệu dễ bị nhầm là đáp án.
# absence_check.keywords được quét trên toàn bộ chunk A và B (scripts/verify_benchmark.py).
UNANSWERABLE = [
    {"id": "u01", "split": "dev",
     "question": "Khi tẩy trắng răng bị nhiễm màu tetracycline thì nên dùng hydrogen peroxide nồng độ bao nhiêu?",
     "absence_reason": "Tài liệu chỉ ghi 'Có thể tiến hành tẩy trắng răng khi răng bị nhiễm màu' (trang 47, "
                       "bệnh 10), không nêu thuốc, nồng độ hay quy trình tẩy trắng.",
     "near_miss": {"page": 47, "text": "Có thể tiến hành tẩy trắng răng khi răng bị nhiễm màu."},
     "absence_check": {"keywords": ["peroxide", "peroxid", "carbamide", "nồng độ"],
                       "allowed_hits": {"nồng độ": "trang 144, nồng độ estradiol trong u máu, không liên quan"}}},
    {"id": "u02", "split": "dev",
     "question": "Bệnh nấm miệng do Candida ở trẻ nhỏ được điều trị bằng thuốc gì?",
     "absence_reason": "Tài liệu không có bệnh nấm miệng; từ 'nấm' chỉ xuất hiện dưới dạng 'nấm mốc từ gạo, lạc' "
                       "trong nguyên nhân ung thư (trang 170, 174, 178).",
     "near_miss": {"page": 170, "text": "Các nấm mốc từ gạo, lạc..."},
     "absence_check": {"keywords": ["candida", "nấm miệng", "tưa lưỡi", "nystatin", "fluconazol"],
                       "allowed_hits": {}}},
    {"id": "u03", "split": "test",
     "question": "Niềng răng bằng khay trong suốt (Invisalign) cho sai khớp cắn loại II thì cần đeo khay bao nhiêu "
                 "giờ mỗi ngày?",
     "absence_reason": "Tài liệu chỉ nói về Headgear và khí cụ chức năng (đeo ít nhất 14 h/ngày, trang 64, 68, 72); "
                       "không có khay trong suốt. Trả lời '14 giờ' là gán nhầm sang khí cụ khác.",
     "near_miss": {"page": 64, "text": "Thời gian đeo Headgear trong ngày: ít nhất 14 h/ngày."},
     "absence_check": {"keywords": ["invisalign", "khay", "aligner", "máng trong suốt"],
                       "allowed_hits": {}}},
    {"id": "u04", "split": "test",
     "question": "Bảo hiểm y tế chi trả bao nhiêu phần trăm chi phí cấy ghép Implant thay một răng đã mất?",
     "absence_reason": "Tài liệu không có thông tin chi phí hay mức chi trả; 'Bảo hiểm Xã hội Việt Nam' chỉ xuất hiện "
                       "trong mục Nơi nhận của Quyết định (trang 1).",
     "near_miss": {"page": 1, "text": "Bảo hiểm Xã hội Việt Nam (để phối hợp)"},
     "absence_check": {"keywords": ["chi phí", "chi trả", "phần trăm", "bảo hiểm y tế"],
                       "allowed_hits": {}}},
]


def main() -> None:
    day6 = json.loads((ROOT / "data" / "day6" / "questions_day6.json").read_text(encoding="utf-8"))
    questions = []
    for q in day6:
        q = dict(q)
        if q["split"] == "test":
            q["split"] = "dev"
            q["note"] = "test Day 6, chuyển sang dev vì kết quả đã được xem ở Day 6"
        questions.append(q)
    for q in NEW_TEST:
        questions.append({"id": q["id"], "split": "test", "question": q["question"], "answerable": True,
                          "expected_behavior": "search_and_answer", "expected_answer": q["expected_answer"],
                          "gold": q["gold"], "type": q["type"], "filter": q["filter"],
                          "disease_no": q["disease_no"]})
    for q in UNANSWERABLE:
        questions.append({**q, "answerable": False, "expected_behavior": "search_and_abstain"})

    out = ROOT / "benchmark" / "questions.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts: dict[str, int] = {}
    for q in questions:
        key = f"{q['split']}/{'answerable' if q['answerable'] else 'abstain'}"
        counts[key] = counts.get(key, 0) + 1
    print(f"{out.relative_to(ROOT)}: {len(questions)} câu {counts}")


if __name__ == "__main__":
    main()
