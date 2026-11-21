# Ma trận truy vết Phase 1

> Contract v1.0 tại thời điểm gắn tag `phase-1` (sau này lên v1.3). Bằng chứng JSONL trong `docs/proof/phase-1/`
> là bản chạy **đúng contract v1.0** lúc gắn tag. Test hiện hành đã gộp vào `tests/test_rules_p1.py` (luật) và
> `tests/test_smoke_p1.py` (hộp đen, 20 test).

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01 | Bơi/ramp/chặn biên: ramp ≤ `ramp_max_ticks`, 4 mép clamp, `d ≥ 0`, heading dương = xuống, đi chéo ≈ `swim_speed` — `test_smoke_p1.py::Movement` | [`out-gather.jsonl`](../proof/phase-1/out-gather.jsonl) (tick 0: `pos [2,0]`, 6 đàn cá, mọi nút `d=0`) | Đạt |
| AC-P1-02 | Oxy + `oxygen_empty` + `dive`/`surface`: dưới nước −1/tick, mặt nước +`oxygen_refill_per_tick`, kẹp `[0, oxygen_max_ticks]`; phát `oxygen_empty` khi từ dương → 0 — `test_rules_p1.py::Oxygen` (`test_underwater_drains_surface_refills`, `test_dive_and_surface_events`) | [`out-choke.jsonl`](../proof/phase-1/out-choke.jsonl) (tick 1 `oxygen_empty {oxygen_ticks:0}`) | Đạt |
| AC-P1-03 | Ngạt/`choke`/`faint`: đủ `choke_interval_ticks` dưới nước với oxy 0 ⇒ −1 HP + `choke {hp}`; HP 0 ⇒ `faint` (LIFO) → `gather_end` `fainted`, kho rỗng — `test_rules_p1.py::Oxygen` | [`out-choke.jsonl`](../proof/phase-1/out-choke.jsonl) (tick 60 `choke {hp:2}`) · [`out-faint.jsonl`](../proof/phase-1/out-faint.jsonl) (`faint {cause:"choke",lost:[...],hp:0}`, `gather_end {reason:"fainted",inventory:{items:{}}}`) | Đạt |
| AC-P1-04 | Giỏ LIFO + `hold_full` đúng 4 khóa `action`/`node_id`\|`fish_id`/`required`/`free` (hái và bắt) — `test_rules_p1.py::Harvest::test_hold_full_on_gather`, `::Catch::test_catch_hold_full_keeps_fish_no_cooldown`, `::Oxygen::test_faint_drops_hold_lifo_and_empty_inventory` | [`out-faint.jsonl`](../proof/phase-1/out-faint.jsonl) (`lost` theo LIFO: `["bong_sung","bong_sung","ca_loc"]`) | Đạt |
| AC-P1-05 | Hái nút `ready` gần nhất ở mặt nước (`interact_radius`, tie theo id nhỏ, `node_yield`, `regrow_s` → `node_regrown`; cập bến xét TRƯỚC hái) — `test_rules_p1.py::Harvest` (`test_gather_at_radius_edge_and_regrow`, `test_node_regrown_event`, `test_no_gather_underwater`, `test_nearest_node_tie_by_id`) | [`out-gather.jsonl`](../proof/phase-1/out-gather.jsonl) (nút N1–N4 `ready`, `d=0`) | Đạt |
| AC-P1-06 | Bắt cá chỉ khi dưới nước + `catch_cd_ticks == 0`; `catch_radius`, `yield` theo loài, xóa đàn, hồi `catch_cooldown_s`; hết giờ vẫn vào kho — `test_rules_p1.py::Catch` | [`out-gather.jsonl`](../proof/phase-1/out-gather.jsonl) (6 đàn `ca_linh`/`ca_loc`) | Đạt |
| AC-P1-07 | Cập bến `docked`; hết giờ `time` giữ giỏ; `tick_limit` **không** ghi kho; ghi kho một lần, `fainted` ⇒ `{}` — `test_smoke_p1.py::Movement::test_time_ends_gather_and_keeps_hold`, `::Contract::test_con_01_ticks_zero_and_end_line` | [`out-gather.jsonl`](../proof/phase-1/out-gather.jsonl) (`end` `reason`), [`out-faint.jsonl`](../proof/phase-1/out-faint.jsonl) | Đạt |
| AC-P1-08 | Hợp đồng JSONL: cùng seed ⇒ byte-giống; input/mode sai (`river`/`night`/nút lạ) ⇒ thoát **2, không ghi output**; scenario ngoài miền ⇒ mã 2 — `test_smoke_p1.py::Contract` (`test_con_02_deterministic_bytes`, `test_con_03_*`), `::ScenarioModes` | `tests/test_smoke_p1.py` (20 test hộp đen, đều xanh) | Đạt |
| AC-P1-09 | HUD sáng tối thiểu (Máu, oxy, giỏ, đồng hồ, gợi ý hái/cập bến, cảnh báo) — `chonoi/web/index.html` | [`out-gather.jsonl`](../proof/phase-1/out-gather.jsonl) · `chonoi/web/index.html` | Đạt |
| AC-P1-10 | Tích hợp Sáng→Tối qua file kho (§G): `gather --inventory-out → quan --inventory` cho `stock` đúng; sai schema / cấm `stock`+`--inventory` ⇒ mã 2 — `test_smoke_p1.py::Integration` | [`out-gather.jsonl`](../proof/phase-1/out-gather.jsonl) → `test_smoke_p1.py::Integration::test_inv_01_gather_writes_inventory_quan_reads_it` | Đạt |
| AC-P1-11 | Khách/giữ chỗ/kiên nhẫn: khách đầu `first_customer_tick`, giữ chỗ khi gọi, hết `patience_s` ⇒ `customer_left` + −uy tín, `no_dish` khi thiếu món — `test_rules_p1.py::Customers` | `tests/test_rules_p1.py::Customers` | Đạt |
| AC-P1-12 | Bếp/bưng/phục vụ/tiền/boa/uy tín: `cook_started → dish_ready → dish_picked → served → paid`; boa `floor(price × tip_rate)` khi đủ `tip_min_patience_ratio`; đóng ca trả khách đang ăn và nhả khách chờ — `test_rules_p1.py::Service` | `tests/test_rules_p1.py::Service` | Đạt |

## Đánh giá ngắn
- Yêu cầu đạt / chưa đạt: **Lát 1** (AC-P1-01..04) và **Lát 2** (AC-P1-05..07) — đạt; lõi `quan` (AC-P1-11..12) — đạt; hợp đồng + tích hợp + HUD (AC-P1-08..10) — đạt. Toàn bộ suite hiện hành **116/116 xanh**.
- Bằng chứng then chốt: [`out-choke.jsonl`](../proof/phase-1/out-choke.jsonl) (chuỗi `oxygen_empty` tick 1 → `choke` tick 60) và [`out-faint.jsonl`](../proof/phase-1/out-faint.jsonl) (`faint` LIFO → kho rỗng) khớp luật PRD-0 §F.
- Xác định (determinism): cùng `--seed` cho JSONL giống từng byte — `test_smoke_p1.py::Contract::test_con_02_deterministic_bytes`.
- Điều cần chỉnh cho phase sau: gom số vào `game.contract.json` (đã làm ở Phase 2–3); bổ sung bằng chứng HUD dạng ảnh.
