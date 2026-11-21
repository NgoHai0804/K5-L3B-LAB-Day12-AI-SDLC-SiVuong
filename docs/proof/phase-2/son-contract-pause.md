# Bằng chứng Phase 2 — Sơn: Contract v1.1, pause, HUD/menu

- Ngày: 2026-11-21
- Nhánh: `son-phase2`
- Phạm vi: `AC-P2-10..12`

## Đã kiểm tra

```powershell
$env:PYTHONPATH='tests;.'
python -m unittest test_phase2_son -v
```

Kết quả: **9/9 PASS**. Bao phủ manifest v1.1, nút cạnh lên, lệnh frame `buy`, scenario/CLI `day --days`, cấm cờ kho trong `day`, đóng băng pause và resume chạy gameplay ngay cùng bước.

```powershell
python .agents\skills\pause-contract-smoke\scripts\run_smoke.py
```

Kết quả: **PASS** — `sim_tick`, `phase_tick`, `time_left_ticks` đứng yên khi pause; resume tăng đúng một bước.

```powershell
$script | node --check -
git diff --check
```

Kết quả: **PASS** cho cú pháp JavaScript trong `chonoi/web/index.html` và whitespace của diff. Chưa tuyên bố kiểm tra trực quan trên trình duyệt.

## Toàn bộ regression

Lệnh chuẩn trong manifest dùng `python3`, nhưng alias đó báo `WinError 1920` trên máy Windows này. Chạy cùng suite bằng Python 3.13.2 hiện có (`python`) cho kết quả:

- 88 test: **85 PASS, 3 FAIL**.
- 1 lỗi có sẵn trước lát Sơn: `test_06_try_hold_reports_full_with_free_and_required` vì code gather có thêm khóa `kind` trong payload `hold_full`.
- 2 lỗi là kỳ vọng Contract v1.0 đã cũ: `test_catch_is_a_v10_button_and_attack_is_not` và nhánh `attack` của `test_con_03_bad_input_exit_2`; Contract v1.1 yêu cầu `attack` là nút hợp lệ.

Không sửa test khóa hoặc xóa trường contract để che ba lỗi này.

## Ranh giới tích hợp

`--mode day --days 1..5` và interface `DaySim(..., days=...)` đã sẵn sàng. Checkout hiện chưa có `chonoi/sim/day.py`/Shop của Tùng, nên chưa thể chạy vòng ngày end-to-end; headless trả lỗi đầu vào rõ ràng thay vì ghi output dở dang.
