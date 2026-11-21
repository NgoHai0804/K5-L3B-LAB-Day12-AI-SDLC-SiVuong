# Bằng chứng Lát 3 — Khách · giữ chỗ · kiên nhẫn (Quý Anh)

Code: `chonoi/sim/quan.py` → `_maybe_spawn_customer`, `_customer_due`, `_available_stock`, `_can_reserve`
(kiên nhẫn / `customer_left` dùng chung `_resolve_customers_and_closing` của Lát 4).
Test: `tests/test_quan_lat3.py` (14 test, hộp đen qua headless).

## Kết quả chạy (nhánh `QuyAnh`, trên Lát 4 của Tùng)

```
PYTHONPATH=tests:. python3 -m unittest discover -s tests
Ran 57 tests ... OK            # gồm 14 test Lát 3
```

```
# kho {"ca_loc":1,"bong_sung":2}, seed 42
python3 -m chonoi.headless --mode quan --seed 42 --scenario sc.json --ticks 240 --snapshot-every 120 --out q.jsonl
exit=0
{"type":"event","tick":120,"phase":"quan","name":"customer_arrived","data":{"order_id":"C1","table_id":"T1","dish_id":"goi_bong_sung"}}
```

## AC → bằng chứng

| AC | Kiểm chứng | Kết quả |
|---|---|---|
| AC-P1-10 lịch khách | `test_ac_p1_10_first_customer_reserves_recipe`, `..._second_customer_follows_interval`, `..._schedule_uses_phase_tick_when_shift_shortened`, `..._no_spawn_on_closing_tick`, `..._random_customers_false_disables_spawn` | đạt |
| AC-P1-10 bàn / món / no_dish | `..._table_busy_skips_turn_without_event`, `..._only_cookable_dish_is_chosen`, `..._no_dish_when_stock_empty`, `..._dish_choice_deterministic_and_covers_menu` | đạt |
| AC-P1-11 kiên nhẫn / uy tín | `test_ac_p1_11_patience_runs_out`, `..._reputation_clamped_at_min`, `..._left_customer_frees_stock_for_next_order`, `..._fixture_missing_reserved_gets_recipe`, `test_ac_p1_10_patience_starts_next_step` | đạt |

Ghi chú tích hợp: chọn món dùng luồng RNG `customer_spawn` và duyệt id món theo mã Unicode, khớp bản Phase 2
của Tùng (`tùng-p2`) để khi gộp không đổi kết quả theo seed.
