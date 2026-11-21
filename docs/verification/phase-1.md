# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01 | Bơi/ramp/chặn biên: `test_smoke_p1.py::Movement` (ramp ≤ 6 tick, 4 mép, `d≥0`, heading dương = xuống, đi chéo ≈ swim_speed) | [`lat1-verification.md`](lat1-verification.md) | Đạt |
| AC-P1-02 | Oxy + `oxygen_empty` + `dive`/`surface`: `tests/test_gather_water.py::Oxygen`, `::SurfaceBoundary` | [`out-choke.jsonl`](out-choke.jsonl) (tick 1 `oxygen_empty`) · [`lat1-verification.md`](lat1-verification.md) | Đạt |
| AC-P1-03 | Ngạt/`choke`/`faint`: `tests/test_gather_water.py::Choke`, `::FaintAndHold` | [`out-choke.jsonl`](out-choke.jsonl) (tick 60 `choke` hp 2) · [`out-faint.jsonl`](out-faint.jsonl) (`faint` LIFO) | Đạt |
| AC-P1-04 | Giỏ LIFO/`hold_full`: `tests/test_gather_water.py::HoldSeam` + `faint.lost` LIFO | [`out-faint.jsonl`](out-faint.jsonl) · [`lat1-verification.md`](lat1-verification.md) | Đạt |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: Lát 1 (AC-P1-01..04, Hải) — **đạt** (41/41 test xanh). Lát 2/hái/bắt cá/kho (AC-P1-05..08) — chờ Đức.
- Điều cần chỉnh cho phase sau: nối `_try_hold()` vào hái/catch (lát 2) để phát `hold_full` end-to-end.
