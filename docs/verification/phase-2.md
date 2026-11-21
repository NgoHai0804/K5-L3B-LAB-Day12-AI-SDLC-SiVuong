# Ma trận truy vết Phase 2

Bảng gộp cả hai team: **Team Sáng** (`gather` — `AC-P2-01..04`, `AC-P2-08..12`, mở rộng) và
**Team Tối** (`quan` — `AC-P2-Q1..Q4`, `AC-P2-05..07`, `AC-P2-13`, `AC-P2-REG`, `AC-P2-MR1`).

| AC | Nội dung yêu cầu (TICKET-02 / Contract v1.1) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| `AC-P2-01` | Tuning v1.1: `contract_version`, `fish_yield` 3 loài, N5/N6 `keo_neo`, `fish_initial` 8 đàn | `tests/test_gather_fish_p2.py` (`TuningV11`) | [lat1-verification.md](../proof/phase-2/lat1-verification.md) | Đạt |
| `AC-P2-02` | Cá bơi (1.5 m/s, đổi hướng bước 120, phản xạ mép/dải) + sinh (8→12, 360 tick) | `tests/test_gather_fish_p2.py` (`FishSwim`, `FishSpawn`, `Determinism`) | [out-gather-p2.jsonl](../proof/phase-2/out-gather-p2.jsonl) · [lat1-verification.md](../proof/phase-2/lat1-verification.md) | Đạt |
| `AC-P2-03..04` | Cá Sấu + Máu/ngất (Đức) | — | — | Chưa (chờ Lát 2) |
| `AC-P2-05` | Lát 3 (Quý Anh): dữ liệu `B1[2,8]`, `B2[5,8]`, `T1[9,2]`, `T2[13,2]`, `T3[9,6]`, `T4[13,6]` trong `game.contract.json`; thứ tự tương tác (khoảng cách, bếp trước bàn, id); 2 bếp nấu song song lấy đơn `reserved` cũ nhất; khách lấp T1→T4 | `tests/test_quan_p2_lat3.py` (`TestP2Lat3StovesTables`, đọc số từ contract thật) | [lat3-quan-p2.md](../proof/phase-2/lat3-quan-p2.md) | Đạt |
| `AC-P2-06` | 6 món + `ca_keo`, `keo_neo` dưới dạng dữ liệu; nấu đúng `cook_s`, chốt đúng giá; file kho nhận nguyên liệu mới, từ chối kind lạ; contract từ chối công thức có nguyên liệu lạ | `tests/test_quan_p2_lat3.py` (`TestP2Lat3Menu`) | [lat3-quan-p2.md](../proof/phase-2/lat3-quan-p2.md) | Đạt |
| `AC-P2-07` | `tuning.day_plan` D1–D5 đúng ticket, `ingredients` = Σ công thức × suất (kiểm khi nạp contract); `chonoi/sim/day_plan.py` (`plan_for_day`, `allowed_dishes`) cho `day`; lọc menu theo kế hoạch trước kho; `no_dish` khi thiếu món kế hoạch; ghi đè `day.day_plan` sai `ingredients` → mã 2 | `tests/test_quan_p2_lat3.py` (`TestP2Lat3DayPlan`) | [lat3-quan-p2.md](../proof/phase-2/lat3-quan-p2.md) | Đạt |
| `AC-P2-08..12` | `day` + Shop + pause + HUD (Tùng, Sơn) | — | — | Chưa (chờ Lát 4) |
| `AC-P2-11` | HUD gather: cảnh báo hết giờ/ngạt/giỏ đầy, chú thích màu, đánh dấu món LIFO (Nhài) | 3 scenario + ảnh trong `docs/proof/phase-1/hud/` | [phase-1/hud/](../proof/phase-1/hud/) | Đạt |
| `AC-P2-13` | Smoke tích hợp `gather --inventory-out → quan --inventory` với số chuẩn: snapshot quán tick 0 có `stock {"bong_sung":2,"ca_loc":1}` | Chạy 2 tiến trình headless | [integration.md](../proof/phase-2/integration.md) · [quan-p2.jsonl](../proof/phase-2/quan-p2.jsonl) | Đạt |
| `AC-P2-Q1` | 2 bếp (`B1 [2,8]`, `B2 [5,8]`), 4 bàn (`T1–T4`), nấu song song đúng thứ tự đơn `reserved` cũ nhất theo `(order_tick, id bàn)` | `tests/test_quan_p2.py` (`test_two_stoves_cook_in_order_and_lau_mam_price_tip`) | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-Q2` | Đủ 6 món & 6 nguyên liệu chuẩn Phase 2, giá/thời gian nấu/boa `floor(price × 0.2)` | `tests/test_quan_p2.py` | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-Q3` | Lịch khách `120 + 900·k`, bàn trống id nhỏ nhất (`T1→T4`), lọc menu theo kế hoạch ngày (`allowed_dishes` D1–D5) trước khi lọc kho khả dụng, phát `no_dish` khi thiếu món | `tests/test_quan_p2.py` (`TestQuanPhase2ScheduleAndDayPlan`) | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-Q4` | Mở rộng Cháy món (`burn_s: 20` → 1200 tick): đúng 1200 tick vẫn bưng được; `ready_ticks > 1200` phát `dish_burnt`, bếp rảnh, thử giữ lại (`reserved`/`unfulfillable`) | `tests/test_quan_p2.py` (`TestQuanPhase2BurnExtension`) | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-REG` | Regression Phase 1 (Lát 4: `AC-P1-12..14`, `test_python_starter_units`, `test_team_check`) giữ nguyên 100% pass | Chạy chung bộ test P1 + P2 | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-MR1` | Nội dung sáng tạo cảm hứng *Dave the Diver* (`chonoi/content/dave_theme.py`) phủ đủ 6 nguyên liệu, 6 món, 3 sinh vật, 5 ngày, Shop & Chợ Nổi Review (`photo`/`dish_burnt`), tắt mặc định ở headless | `tests/test_quan_p2.py` (`TestMR1Phase2DaveContent`) | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-EX-01..07` | Mở rộng (Tùng/Sơn/Nhài) | — | — | Chưa |

## Ghi chú tích hợp
- `chonoi/inventory.py`: `KINDS_P1` giữ 4 nguyên liệu Phase 1; `KINDS = KINDS_P1 + ("ca_keo", "keo_neo")` là tập đủ 6 nguyên liệu dùng cho đọc/ghi kho. `chonoi/contract.py` và `chonoi/scenario.py` import `KINDS` — xem [ADR-0001](../adr/0001-du-lieu-quan-v11.md).
- Phần `chonoi/sim/quan.py` đọc động `stoves`, `tables`, `menu`, `burn_s` từ `tuning` và nhận `allowed_dishes` từ chế độ `day`.
- Lát 3 (Quý Anh) đã đưa phần dữ liệu quán v1.1 vào `game.contract.json` (`quan.stoves`, `quan.tables`, `menu`, `day_plan`).
- `contract_version`, khối gather/monsters/shop và CLI `day` vẫn do Sơn/Hải/Tùng nâng cấp.

## Thay đổi test P1 (có lý do)
- `tests/test_smoke_p1.py`: `len(fish)` **6 → 8** — chuẩn v1.1 (TICKET-02 §1.2). Không phải nới test cho xanh.
- `tests/test_gather_water.py:136`: nới assert `hold_full` theo hợp đồng §4 (`docs/clarify.md` #5, do Lát 2 thêm `kind`).
- `tests/test_quan_lat3.py`: Phase 2 đổi 1 bàn → 4 bàn và 3 → 6 món, nên test đọc danh sách bàn từ contract (lượt khách lấp T1→T4 thay vì chờ T1 trống; bàn bận = cả 4 bàn có khách; độ phủ món = cả 6 món).
- `tests/test_quan_lat4.py`: `INGREDIENT_GUIDE` và `DISH_LORE` mở rộng từ 4→6 nguyên liệu và 3→6 món nên đổi so sánh `assertEqual` thành `issubset` (mọi mục Phase 1 được giữ nguyên).

## Đánh giá ngắn
- Đạt: **Lát 1** (`AC-P2-01..02`, Hải) và **Lát 3** (`AC-P2-05..07`, Quý Anh); regression P1 xanh với số chuẩn v1.1.
- Chưa: các lát 2, 4 và mở rộng.
- Cần chỉnh: chốt manifest v1.1 (Sơn) trước khi bật `--mode day`; gắn tag `phase-2`.
