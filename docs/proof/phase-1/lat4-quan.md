# Bằng chứng kiểm chứng Phase 1 — Lát 4 & MR-1 (Nguyễn Thanh Tùng)

## Phạm vi kiểm chứng
- **Module lõi**: `chonoi/sim/quan.py` (Lát 4: bếp nấu, bưng món, phục vụ, tính boa, thu tiền, uy tín, hết ca `quan_end`).
- **Module sáng tạo (MR-1)**: `chonoi/content/dave_theme.py` (Sổ tay tầng nước & thực đơn, lời thoại Nam Bộ, *Chợ Nổi Review* cảm hứng *Dave the Diver* — tắt mặc định ở headless).
- **Bộ test**: `tests/test_quan_lat4.py`.

## Lệnh chạy kiểm chứng
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_quan_lat4 tests.test_python_starter_units tests.test_team_check -v
```

## Kết quả chạy thật
```text
test_guides_cover_all_core_ingredients_and_dishes (tests.test_quan_lat4.TestMR1DaveTheDiverContent) ... ok
test_review_tracker_disabled_by_default_for_headless (tests.test_quan_lat4.TestMR1DaveTheDiverContent) ... ok
test_review_tracker_summarizes_events_when_enabled (tests.test_quan_lat4.TestMR1DaveTheDiverContent) ... ok
test_ac_p1_12_cook_oldest_reserved_and_ready_ticks (tests.test_quan_lat4.TestQuanLat4Cooking) ... ok
test_ac_p1_12_interact_priority_stove_before_table_and_no_fallthrough (tests.test_quan_lat4.TestQuanLat4Cooking) ... ok
test_ac_p1_14_finish_eating_pays_and_clamps_reputation (tests.test_quan_lat4.TestQuanLat4PaymentAndClosing) ... ok
test_ac_p1_14_serve_on_last_tick_pays_closing_and_emits_quan_end (tests.test_quan_lat4.TestQuanLat4PaymentAndClosing) ... ok
test_ac_p1_14_waiting_customer_at_closing_no_rep_penalty_and_cleans_stove (tests.test_quan_lat4.TestQuanLat4PaymentAndClosing) ... ok
test_headless_cli_full_lat4_loop_deterministic (tests.test_quan_lat4.TestQuanLat4PaymentAndClosing) ... ok
test_ac_p1_13_pick_and_serve_with_tip (tests.test_quan_lat4.TestQuanLat4PickServeTip) ... ok
test_ac_p1_13_serve_on_exact_zero_patience_tick_still_valid_with_zero_tip (tests.test_quan_lat4.TestQuanLat4PickServeTip) ... ok
----------------------------------------------------------------------
Ran 22 tests in 0.464s

OK
```

## Bảng ánh xạ AC (Lát 4 & MR-1)
| AC | Nội dung kiểm chứng | Test tương ứng | Kết quả |
|---|---|---|---|
| `AC-P1-12` | Nấu đơn reserved cũ nhất, tiêu đúng nguyên liệu giữ, `cook_started`, `dish_ready`, `ready_ticks` chỉ tăng cho món đã ready ở đầu bước, không cháy (`burn_s: null`) | `test_ac_p1_12_cook_oldest_reserved_and_ready_ticks`, `test_ac_p1_12_interact_priority_stove_before_table_and_no_fallthrough` | Đạt |
| `AC-P1-13` | Ưu tiên interact `(dist, bếp trước bàn, id)`, `dish_picked`, `served`, tính boa theo `tip_min_patience_ratio`, phục vụ đúng tick kiên nhẫn về 0 vẫn hợp lệ | `test_ac_p1_13_pick_and_serve_with_tip`, `test_ac_p1_13_serve_on_exact_zero_patience_tick_still_valid_with_zero_tip` | Đạt |
| `AC-P1-14` | Ăn xong trả tiền (`paid` reason `finished_eating`), cộng uy tín kẹp trần, hết ca khách còn ăn trả ngay (`closing`), khách chờ rời không trừ uy tín, dọn bếp/tay, `quan_end`, tất định từng byte qua headless | `test_ac_p1_14_finish_eating_pays_and_clamps_reputation`, `test_ac_p1_14_serve_on_last_tick_pays_closing_and_emits_quan_end`, `test_ac_p1_14_waiting_customer_at_closing_no_rep_penalty_and_cleans_stove`, `test_headless_cli_full_lat4_loop_deterministic` | Đạt |
| `MR-1` | Nội dung cảm hứng *Dave the Diver* đầy đủ cho 4 nguyên liệu & 3 món, tắt mặc định ở headless | `TestMR1DaveTheDiverContent` (3 tests) | Đạt |
