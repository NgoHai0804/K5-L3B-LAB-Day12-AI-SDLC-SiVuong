# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01 | Bơi/ramp/chặn biên: `test_smoke_p1.py::Movement` (ramp ≤ 6 tick, 4 mép, `d≥0`, heading dương = xuống, đi chéo ≈ swim_speed) | [`lat1-verification.md`](lat1-verification.md) | Đạt |
| AC-P1-02 | Oxy + `oxygen_empty` + `dive`/`surface`: `tests/test_gather_water.py::Oxygen`, `::SurfaceBoundary` | [`out-choke.jsonl`](out-choke.jsonl) (tick 1 `oxygen_empty`) · [`lat1-verification.md`](lat1-verification.md) | Đạt |
| AC-P1-03 | Ngạt/`choke`/`faint`: `tests/test_gather_water.py::Choke`, `::FaintAndHold` | [`out-choke.jsonl`](out-choke.jsonl) (tick 60 `choke` hp 2) · [`out-faint.jsonl`](out-faint.jsonl) (`faint` LIFO) | Đạt |
| AC-P1-04 | Giỏ LIFO/`hold_full`: `tests/test_gather_water.py::HoldSeam` + `faint.lost` LIFO | [`out-faint.jsonl`](out-faint.jsonl) · [`lat1-verification.md`](lat1-verification.md) | Đạt |
| AC-P1-05 | Hái nút `ready` gần nhất ở mặt nước (`interact_radius`, tie-break id nhỏ, `node_yield`, `regrow_s` → `node_regrown`, cập bến xét TRƯỚC hái): `tests/test_gather_s2.py::TestHaiNut` (8 test) | [`lat2-gather.jsonl`](lat2-gather.jsonl) · [`test-duc.txt`](test-duc.txt) | Đạt |
| AC-P1-06 | Bắt cá chỉ khi dưới nước + `catch_cd_ticks == 0`, `catch_radius`, `fish_yield` theo loài, xoá cá, hồi chiêu: `tests/test_gather_s2.py::TestBatCa` (9 test) | [`test-duc.txt`](test-duc.txt) | Đạt |
| AC-P1-07 | `hold_full` đúng hợp đồng §4 — **đúng 4 khoá** `action` / `node_id`\|`fish_id` / `required` / `free`, **không** có khoá lạ — cho cả hái và bắt cá, qua seam `_try_hold` của lát 1 | `TestHaiNut::test_06` · `TestBatCa::test_08` · [`test-duc.txt`](test-duc.txt) | Đạt |
| AC-P1-08 | Hợp đồng file kho §1: ghi 1 lần khi `docked`/`time`/`fainted`, **không** ghi khi `tick_limit`, `fainted` ⇒ `{}`, bỏ mục 0, khoá gốc `items`, `gather_end.inventory` khớp file, sai schema/id/số âm ⇒ thoát 2: `tests/test_gather_s2.py::TestGhiKho` (10 test) | [`lat2-kho.json`](lat2-kho.json) · [`lat2-quan.jsonl`](lat2-quan.jsonl) · [`test-duc.txt`](test-duc.txt) | Đạt |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: Lát 1 (AC-P1-01..04, Hải) — **đạt**. Lát 2 (AC-P1-05..08, Đức) — **đạt**. Tổng **68/68 test xanh**.
- **Đã thu hồi:** `docs/clarify.md` #5 từng kết luận `hold_full` thiếu khoá `kind` — **tiền đề sai** do Đức đọc hợp đồng ở checkout cũ. Hợp đồng §4 luôn là `action` / `node_id`\|`fish_id` / `required` / `free`; `_try_hold` của lát 1 đúng từ đầu. Đã bỏ `kind` khỏi `_try_hold`, trả `tests/test_gather_water.py` về `assertEqual` gốc của Hải, và sửa 2 test lát 2 sang kiểm đúng 4 khoá. Bài học ghi ở `docs/clarify.md` mục "Ghi chú #5" và `docs/ai-usage-log.md`.
- Bàn giao Sáng→Tối đã chạy thật: `gather --inventory-out lat2-kho.json` → `quan --inventory lat2-kho.json`, không lỗi.
- Xác định (determinism): cùng `--seed 1` cho JSONL giống từng byte — hash ở cuối [`test-duc.txt`](test-duc.txt).
