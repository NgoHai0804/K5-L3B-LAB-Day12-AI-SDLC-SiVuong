# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Hải | Kilo (deepseek-v4.1-flash) | Lát 1: oxy/ngạt/faint/biên + seam giỏ, test `test_gather_water.py` | ~15k | AI lần đầu định đếm ngạt ngay ở bước chạm 0 (lệch 1 tick); sửa theo "choke ở t+59". |
| 1 | Đức | Claude Code (Opus 5) | Lát 2: hái nút + bắt cá trong `chonoi/sim/gather.py`, 27 test `test_gather_s2.py`, ma trận truy vết AC-P1-05..08 | ~40k | **(a)** AI tự viết helper `_try_take()` riêng cho giỏ trong khi lát 1 đã có seam `_try_hold()` — trùng logic, phải xoá và nối lại vào seam của Hải. **(b)** AI gợi ý hard-code `1200`/`30` ticks thay vì `regrow_s * TICK` và `catch_cooldown_s * TICK`, vi phạm `AGENTS.md` "số liệu chỉ đọc từ contract". **(c)** AI ban đầu đặt `catch_cd_ticks` cả khi bắt thất bại vì giỏ đầy — sai so với `clarify.md` #4. Cả 3 đều phải sửa tay. Điểm AI làm tốt: tự đối chiếu `docs/contracts/README.md` §4 và phát hiện `hold_full` của lát 1 thiếu khoá `kind`. |
