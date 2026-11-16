"""Nhãn chấm tay cho test (G0-dense baseline và G2-hybrid-k5 được chọn).

Claude soạn; toàn bộ test gắn cờ để học viên duyệt (flag=True). Định dạng như labels_dev.py.
"""
T, F = True, False
BOTH = ("G0-dense", "G2-hybrid-k5")

LABELS = {
    "n01": {c: (2, [T], "Đúng và đủ hai chỉ định mở thông nang (tr. 109).", T) for c in BOTH},
    "n02": {c: (2, [T], "Đúng 4–6 tuần; filter bệnh 54 giữ đúng đoạn gãy xương hàm dưới.", T) for c in BOTH},
    "n03": {
        "G0-dense": (2, [T, T, T], "Đúng: viêm mạn xơ hóa, phải cắt tuyến [S7]; S4 (chỉ định cắt tuyến khi xơ hóa), S2 (phòng bệnh) hỗ trợ ý phụ.", T),
        "G2-hybrid-k5": (2, [T, T], "Đúng [S3]; S1 hỗ trợ ý phòng bệnh.", T),
    },
    "n04": {
        "G0-dense": (2, [T], "Đúng Ca(OH)2, trung hòa mô viêm và sát khuẩn; các bước nội nha đúng đoạn.", T),
        "G2-hybrid-k5": (2, [T], "Đúng Ca(OH)2.", T),
    },
    "n05": {c: (2, [T], "Đúng: cắt u và đoạn xương hàm, ghép xương hàm, phục hình răng.", T) for c in BOTH},
    "u03": {c: (None, [], "Từ chối đúng; nêu rõ 14 h/ngày là của Headgear/khí cụ chức năng, không gán cho khay trong suốt.", T) for c in BOTH},
    "u04": {c: (None, [], "Từ chối đúng; không bịa tỷ lệ chi trả.", T) for c in BOTH},
}
