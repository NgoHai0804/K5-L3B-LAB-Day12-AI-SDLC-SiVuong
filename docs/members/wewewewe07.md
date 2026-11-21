# wewewewe07 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm: kiểm thử và bằng chứng. Viết `tests/test_phase4.py` (v1.3 + extensions, bench 5 trường, soak 2 Ngày tất định, bảng xếp hạng sắp/giới hạn/Unicode/xuất, cổng ghi + mã thoát 2, dò dấu vết trong `index.html`). Điền `TEAM.md` (5 người) và chuyển `tests/test_team_check.py` sang dùng chuỗi TEAM mẫu inline, đồng thời thêm test đọc `TEAM.md` thật. Lưu ảnh bằng chứng vào `docs/proof/phase-4/`.
- Tôi đã review: chạy lại toàn bộ suite hộp đen và đối chiếu `docs/verification/phase-4.md` với từng AC.
- AI sai ở đâu và tôi phát hiện thế nào: khi chụp ảnh cảnh báo, AI bơm một snapshot pha `quan` (meta `{x,z}`) vào bộ vẽ `gather` (cần meta `{x,d}`) → lỗi `Cannot read properties of undefined`. Tôi nhận ra `meta` phải khớp **pha** và bơm đúng `bounds` cho từng pha mới ra ảnh.
- Điều tôi học được: test "đọc file thật" dễ vỡ khi file thật đổi; tách phần bất biến (thuật toán kiểm) khỏi phần dữ liệu (file) bằng cách dùng fixture inline là cách giữ test vừa chặt vừa bền.
