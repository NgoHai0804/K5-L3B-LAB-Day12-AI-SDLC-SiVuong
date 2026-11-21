# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 4 | NgoHai0804 | Claude / agent CLI | `leaderboard.py`, cổng ghi trong `headless.py`, `docs/verification/phase-4.md` | ~30k token | AI định ghi bảng xếp hạng cho mọi lượt `day`; nhóm sửa lại chỉ ghi khi đủ 5 Ngày chuẩn, không scenario. |
| 4 | buiquyanh9-ai | Claude / agent CLI | `web/index.html`: 3 cảnh báo, chế độ tương phản cao (H), phụ đề SFX | ~25k token | AI đặt nhãn cảnh báo ghép chuỗi (`"KHÁCH" + " SẮP GIẬN!"`) nên test dò chuỗi nguyên văn thất bại; nhóm sửa test cho khớp. |
| 4 | son309 | Claude / agent CLI | `bench.py` (rasterizer CPU, 5 trường) + `bench_cmd` | ~20k token | AI tính `p1_low_fps` từ khung chậm nhất nhưng quên chặn `frames=0`; đã thêm `max(1, …)` và giá trị dự phòng. |
| 4 | chanhochust | Claude / agent CLI | `soak.py` (bot tất định) + `soak_cmd`, `plan_repeat` cho `sim/day` | ~22k token | AI cho `DaySim` chỉ chạy 5 Ngày; nhóm thêm `plan_repeat` và lặp kế hoạch modulo để chạy 10 Ngày. |
| 4 | wewewewe07 | Claude / agent CLI | `tests/test_phase4.py`, ảnh bằng chứng `docs/proof/phase-4/`, cập nhật `TEAM.md` | ~18k token | AI chụp live bị lệch pha (snapshot `quan` đưa vào render `gather` gây lỗi `bounds.d`); nhóm bơm đúng `meta` theo pha. |
| 2–3 | cả nhóm | Claude / agent CLI | Số chuẩn, kho cá thể, độ tươi, vòng Ngày, Shop | ~120k token (cả phase) | AI hard-code vài số trong luật; nhóm gom về `game.contract.json` và thêm test tất định. |
