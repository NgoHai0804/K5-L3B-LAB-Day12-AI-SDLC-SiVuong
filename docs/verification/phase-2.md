# Ma trận truy vết Phase 2

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P2-01 | Tuning v1.1: `contract_version`, `fish_yield` 3 loài, N5/N6 `keo_neo`, `fish_initial` 8 — `test_gather_fish_p2.py::TuningV11` | [`lat1-verification.md`](../proof/phase-2/lat1-verification.md) | Đạt |
| AC-P2-02 | Cá bơi (1.5 m/s, đổi hướng bước 120, phản xạ mép/dải) + sinh (8→12, 360 tick) — `::FishSwim`, `::FishSpawn`, `::Determinism` | [`out-gather-p2.jsonl`](../proof/phase-2/out-gather-p2.jsonl) · [`lat1-verification.md`](../proof/phase-2/lat1-verification.md) | Đạt |
| AC-P2-03..04 | Cá Sấu + Máu/ngất (Đức) | — | Chưa (chờ Lát 2) |
| AC-P2-05..07 | 2 bếp/4 bàn + 6 món + kế hoạch ngày (Quý Anh) | — | Chưa (chờ Lát 3) |
| AC-P2-08..12 | `day` + Shop + pause + HUD (Tùng, Sơn) | — | Chưa (chờ Lát 4) |
| AC-P2-11,13 | HUD sáng + QA + smoke/regression (Nhài) | [`quan-p2.jsonl`](../proof/phase-2/quan-p2.jsonl) (smoke Sáng→Tối) | Một phần |
| AC-P2-EX-01..07 | Mở rộng (Tùng/Sơn/Nhài) | — | Chưa |

## Thay đổi test P1 (có lý do)
- `tests/test_smoke_p1.py`: `len(fish)` **6 → 8** — chuẩn v1.1 (TICKET-02 §1.2). Không phải nới test cho xanh.
- `tests/test_gather_water.py:136`: nới assert `hold_full` theo hợp đồng §4 (`docs/clarify.md` #5, do Lát 2 thêm `kind`).

## Đánh giá ngắn
- Đạt: **Lát 1** (`AC-P2-01..02`, Hải). Regression P1 xanh với số chuẩn v1.1.
- Chưa: các lát 2–4 và mở rộng.
- Cần chỉnh: chốt manifest v1.1 (Sơn) trước khi bật `--mode day`; gắn tag `phase-2`.
