"""Nhãn chấm tay cho dev. Dòng: (grade hoặc None cho câu thiếu bằng chứng, citation_support, lý do, flag).

Người soạn nhãn: Claude (đọc câu trả lời, đáp án mong đợi và đoạn được trích).
flag=True: chưa chắc, cần học viên đọc lại. Học viên duyệt và sửa trực tiếp file này,
rồi chạy scripts/write_reviews.py để sinh reviews.json.
"""
T, F = True, False

LABELS = {
    "d01": {
        "G0-dense": (2, [T, T, T], "Đúng: nhổ càng sớm càng tốt để không mất xương phía xa răng 7 [S1]. S2, S3 hỗ trợ ý phụ.", F),
        "G1-hybrid": (2, [T, T], "Đúng và đủ, trích đúng đoạn nguyên tắc điều trị.", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng và đủ; S6 (tiên lượng) hỗ trợ ý bảo vệ răng 7.", F),
    },
    "d02": {
        "G0-dense": (0, [], "Từ chối nhầm: dense không lấy được đoạn 'b. Răng khôn lệch có biến chứng' (tr. 9) qua 3 lượt.", F),
        "G1-hybrid": (2, [T, T], "Đúng: điều trị nhiễm trùng (kháng sinh, bơm rửa) rồi mới nhổ [S6].", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng như G1.", F),
    },
    "d03": {
        "G0-dense": (0, [], "Từ chối nhầm: chỉ thấy pH < 5,5 của bệnh sâu răng (tr. 40), không lấy được đoạn nguyên nhân sâu răng sữa (tr. 18, pH < 5).", F),
        "G1-hybrid": (2, [T, T], "Đúng pH < 5 [S2], phân biệt đúng với pH < 5,5 của bệnh sâu răng [S3].", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng như G1.", F),
    },
    "d04": {
        "G0-dense": (2, [T], "Đúng Streptococcus mutans [S1].", F),
        "G1-hybrid": (2, [T, T], "Đúng. S2 (bệnh sâu răng, tr. 40) có cùng câu về S. mutans (đã đối chiếu text).", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng, như G1.", F),
    },
    "d05": {
        "G0-dense": (2, [T, T], "Đúng gõ dọc đau nhẹ, gõ ngang đau nhiều [S3]; S1 hỗ trợ ý so sánh viêm tủy có hồi phục.", F),
        "G1-hybrid": (2, [T, T], "Đúng; S2 là bảng chẩn đoán phân biệt tr. 26 có cùng thông tin.", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng như G1.", F),
    },
    "d06": {
        "G0-dense": (2, [T], "Đúng: trẻ đang đau rất cảnh giác, sợ hãi.", F),
        "G1-hybrid": (2, [T], "Đúng.", F),
        "G2-hybrid-k5": (2, [T], "Đúng.", F),
    },
    "d07": {
        "G0-dense": (2, [T], "Đúng 350–450 g mỗi bên, ít nhất 14 h/ngày.", F),
        "G1-hybrid": (2, [T], "Đúng.", F),
        "G2-hybrid-k5": (2, [T], "Đúng.", F),
    },
    "d08": {
        "G0-dense": (2, [T], "Đúng: chảy mủ qua lỗ ống Wharton.", F),
        "G1-hybrid": (2, [T], "Đúng.", F),
        "G2-hybrid-k5": (2, [T], "Đúng.", F),
    },

    "d09": {c: (2, [T], "Đúng khoảng 3 mm.", F) for c in ("G0-dense", "G1-hybrid", "G2-hybrid-k5")},
    "d10": {c: (2, [T], "Đúng: gãy mỏm khẩu cái và vòm khẩu cái.", F) for c in ("G0-dense", "G1-hybrid", "G2-hybrid-k5")},
    "d11": {
        "G0-dense": (2, [T], "Đúng Paramyxo virus.", F),
        "G1-hybrid": (2, [T, T], "Đúng; S1 hỗ trợ ý lây qua nước bọt.", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng như G1.", F),
    },
    "d12": {
        "G0-dense": (2, [T, T], "Đúng viêm tinh hoàn; S2 chỉ dùng để nói đó là biến chứng của bệnh mạn tính, dùng đúng.", F),
        "G1-hybrid": (2, [T], "Đúng.", F),
        "G2-hybrid-k5": (2, [T], "Đúng.", F),
    },
    "d13": {c: (2, [T], "Đúng Carbamazepine, thay bằng Oxcarbazepine hoặc gabapentin.", F) for c in ("G0-dense", "G1-hybrid", "G2-hybrid-k5")},
    "d14": {
        "G0-dense": (2, [T, T, T], "Đúng: không rõ nguyên nhân và nội khoa thất bại [S4]; lượt search thứ 3 lấy được đoạn này.", F),
        "G1-hybrid": (2, [T, T, T], "Đúng; S1 dùng cho ý phân biệt trường hợp có nguyên nhân.", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng.", F),
    },
    "d15": {
        "G0-dense": (2, [T, T, T], "Đúng tên và thành phần MTA; S2, S3 hỗ trợ ý công dụng.", F),
        "G1-hybrid": (2, [T, T], "Đúng.", F),
        "G2-hybrid-k5": (2, [T, T, T], "Đúng.", F),
    },
    "d16": {c: (2, [T, T], "Đúng 6 kg, phân biệt đúng 10 kg của khe hở vòm miệng.", F) for c in ("G0-dense", "G1-hybrid", "G2-hybrid-k5")},
    "d17": {
        "G0-dense": (2, [T, T, T], "Đúng và đủ các giai đoạn.", F),
        "G1-hybrid": (2, [T, T], "Đúng.", F),
        "G2-hybrid-k5": (2, [T, T, T], "Đúng.", F),
    },
    "d18": {
        "G0-dense": (2, [T], "Đúng PGS.TS. Nguyễn Thị Xuyên và hai đồng chủ biên.", F),
        "G1-hybrid": (0, [], "Từ chối nhầm do budget context: lượt 2 lấy được đoạn chủ biên (tr. 3) ở hạng 1 nhưng bị bỏ vì lượt 1 đã nạp đoạn Quyết định dài, dùng 2232/3000 ký tự.", F),
        "G2-hybrid-k5": (2, [T], "Đúng, nhờ top-5 lấy được trang 3.", F),
    },
    "t01": {c: (2, [T], "Đúng: khi áp xe tiến triển về phía niêm mạc miệng.", F) for c in ("G0-dense", "G1-hybrid", "G2-hybrid-k5")},
    "t02": {
        "G0-dense": (2, [T], "Đúng: cắn chìa bình thường, cắn phủ tăng. Câu 'không nêu con số' chấp nhận được.", F),
        "G1-hybrid": (2, [T], "Đúng.", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng, có cả ý mức độ tùy trường hợp.", F),
    },
    "t03": {
        "G0-dense": (2, [T, T], "Đúng quá 1/2 chiều dài Implant; S2 hỗ trợ mức dưới 2 mm.", F),
        "G1-hybrid": (2, [T], "Đúng.", F),
        "G2-hybrid-k5": (2, [T], "Đúng.", F),
    },
    "t04": {
        "G0-dense": (2, [T, T], "Đúng chỉ định và cách mổ; S2 chỉ để xác nhận đúng bệnh.", F),
        "G1-hybrid": (2, [T, F], "Đúng; S3 (u hỗn hợp tuyến mang tai) được trích chỉ để nói là bệnh khác, không hỗ trợ ý trả lời nên tính là citation không hỗ trợ.", T),
        "G2-hybrid-k5": (2, [T], "Đúng.", F),
    },
    "t05": {
        "G0-dense": (2, [T], "Đúng mức độ 1, tập há miệng bằng dụng cụ banh miệng.", F),
        "G1-hybrid": (2, [T, T, T], "Đúng; S6 và S3 hỗ trợ ý phụ.", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng.", F),
    },
    "t06": {
        "G0-dense": (2, [T], "Đúng: kể từ ngày ký, 28/7/2015 (Điều 3 nằm trong đoạn được trích).", F),
        "G1-hybrid": (2, [T], "Đúng.", F),
        "G2-hybrid-k5": (2, [T, T], "Đúng.", F),
    },
    "u01": {c: (None, [], "Từ chối đúng, không đưa con số tẩy trắng. Lưu ý: tài liệu có 'Ôxy già 3%' để súc miệng (bệnh 8); G0 nêu đúng là không dùng cho tẩy trắng.", F) for c in ("G0-dense", "G1-hybrid", "G2-hybrid-k5")},
    "u02": {c: (None, [], "Từ chối đúng: tài liệu không có nấm miệng Candida, không gợi ý thuốc ngoài tài liệu.", F) for c in ("G0-dense", "G1-hybrid", "G2-hybrid-k5")},
}
