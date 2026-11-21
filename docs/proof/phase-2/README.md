# Bằng chứng Phase 2

> Bản chạy **Contract v1.1** (cá bơi/sinh, 6 nút, 8 đàn; kho vẫn là kho đếm ở thời điểm này).

| File | Nội dung | Cho thấy |
|---|---|---|
| `out-gather-p2.jsonl` | `--mode gather` (chuẩn v1.1) | Tick 0 có 6 nút hái `N1–N6` (kèm `keo_neo`) và **8 đàn** `F1–F8` (đủ 3 loài) |
| `gather-p2.jsonl` | gather + scenario dock, `interact` tick 0 | `gather_end {reason:"docked", inventory:{items:{bong_sung:2, ca_loc:1}}}` và dòng `end` |
| `quan-p2.jsonl` | `--mode quan --inventory <gather-p2>` | Snapshot quan tick 0 có `stock {bong_sung:2, ca_loc:1}` (smoke tích hợp Sáng→Tối) |
| `son-contract-pause.md` | Sơn — Contract v1.1, pause, HUD/menu (`AC-P2-10..12`) | 10/10 test `test_phase2_son` PASS + smoke pause |

## Tái lập (smoke tích hợp)
```bash
python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

Kiểm trực tiếp: `tests/test_rules_p2p3.py` (FishAndMonsters, DayLoop, Determinism) và `tests/test_phase2_son.py` (Manifest, DayCli, Pause).
