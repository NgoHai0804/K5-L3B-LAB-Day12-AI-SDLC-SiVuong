# Ma trận truy vết Phase 2

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P2-01 | Tuning v1.1: `contract_version`, `fish_yield` 3 loài, N5/N6 `keo_neo`, `fish_initial` 8 — `test_gather_fish_p2.py::TuningV11` | [`lat1-verification.md`](../proof/phase-2/lat1-verification.md) | Đạt |
| AC-P2-02 | Cá bơi (1.5 m/s, đổi hướng bước 120, phản xạ mép/dải) + sinh (8→12, 360 tick) — `::FishSwim`, `::FishSpawn`, `::Determinism` | [`out-gather-p2.jsonl`](../proof/phase-2/out-gather-p2.jsonl) · [`lat1-verification.md`](../proof/phase-2/lat1-verification.md) | Đạt |
| AC-P2-03..04 | Cá Sấu + Máu/ngất (Đức) | — | Chưa (chờ Lát 2) |
| AC-P2-05..07 | 2 bếp/4 bàn + 6 món + lịch khách & lọc `day_plan` (`chonoi/sim/quan.py`, `test_quan_p2.py`) | [`quan-p2.md`](../proof/phase-2/quan-p2.md) | Đạt (sim `quan` sẵn sàng v1.1; chờ chốt tuning `quan`/`menu` trong `game.contract.json`) |
| AC-P2-08..12 | `day` + Shop + pause + HUD (Tùng, Sơn) | — | Chưa (chờ tích hợp `day`/`shop` & manifest v1.1) |
| AC-P2-11,13 | HUD sáng + QA + smoke/regression (Nhài) | [`quan-p2.jsonl`](../proof/phase-2/quan-p2.jsonl) (smoke Sáng→Tối) | Một phần |
| AC-P2-EX-04 | Mở rộng Cháy món (`burn_s: 20` -> 1200 tick, `dish_burnt`, re-reserve `reserved`/`unfulfillable`) — `test_quan_p2.py::TestQuanPhase2BurnExtension` | [`quan-p2.md`](../proof/phase-2/quan-p2.md) | Đạt (bật khi `burn_s` hữu hạn; `null` trong lõi) |
| AC-P2-MR1 | Nội dung sáng tạo cảm hứng *Dave the Diver* (`chonoi/content/dave_theme.py`: 6 nguyên liệu, 6 món, 3 sinh vật, 5 ngày, Shop, Chợ Nổi Review — tắt ở headless) | [`quan-p2.md`](../proof/phase-2/quan-p2.md) | Đạt |

## Thay đổi test P1 (có lý do)
- `tests/test_smoke_p1.py`: `len(fish)` **6 → 8** — chuẩn v1.1 (TICKET-02 §1.2). Không phải nới test cho xanh.
- `tests/test_gather_water.py:136`: nới assert `hold_full` theo hợp đồng §4 (`docs/clarify.md` #5, do Lát 2 thêm `kind`).
- `tests/test_quan_lat4.py:423`: đổi `assertEqual` → `issubset` cho `INGREDIENT_GUIDE` và `DISH_LORE` vì Phase 2 mở rộng từ 4→6 nguyên liệu và 3→6 món (giữ nguyên đủ dữ liệu Phase 1).

## Đánh giá ngắn
- Đạt: **Lát 1** (`AC-P2-01..02`, Hải), phần lõi `quan` v1.1 + mở rộng `burn` + MR-1 (`tests/test_quan_p2.py`, Tùng). Regression P1 xanh với số chuẩn v1.1.
- Chưa: Lát 2 (Cá Sấu), `day`/Shop/pause (Lát 4).
- Cần chỉnh: chốt manifest v1.1 (Sơn) cho khối `quan`/`menu`/`day_plan`/`shop` trước khi bật `--mode day`.
