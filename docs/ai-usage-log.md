# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Giang Thái Sơn | Codex | HUD quán, smoke nạp kho, `AGENTS.md`, 2 skill kiểm chứng | Không hiển thị trong phiên | Lệnh `python3` chuẩn không chạy được trên Windows; đã nhận ra lỗi môi trường `WinError 1920`, không sửa test/contract và chạy lại đủ 32 test bằng Python hiện tại. |
| 1 | Hải | Kilo (deepseek-v4.1-flash) | Lát 1: oxy/ngạt/faint/biên + seam giỏ, test `test_gather_water.py` | ~15k | AI lần đầu định đếm ngạt ngay ở bước chạm 0 (lệch 1 tick); sửa theo "choke ở t+59". |
