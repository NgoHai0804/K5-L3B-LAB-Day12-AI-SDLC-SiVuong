# Bằng chứng Phase 3 (change request "Mùa Nước Nổi" · kho cá thể + độ tươi)

| File | Nội dung | Cho thấy |
|---|---|---|
| `gather-v12.jsonl` | `--mode gather --seed 1 --ticks 600` (v1.2/v1.3) | `hold` là **mảng cá thể** `{id,kind,fresh}` (không còn mảng kind); snapshot/`end` hợp lệ |
| `quan-v12.jsonl` | `--mode quan --seed 1 --ticks 600` (v1.2/v1.3) | `stock` là **mảng cá thể**, 2 bếp `B1,B2`, 4 bàn `T1–T4` |
| `quyanh-upload.txt` | Kiểm trước khi upload | 87 test pass; smoke tích hợp hai tiến trình theo **kho cá thể v1.2**; `determinism` gather/quan/day byte-giống |
| `out-gather.jsonl` | Bản gather **v1.1** (tham chiếu, kho đếm) | Giữ để so sánh trước/sau khi đổi schema — **không** phải bằng chứng v1.2 |

## Tái lập
```bash
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out gather-v12.jsonl
python3 -m chonoi.headless --mode quan   --seed 1 --ticks 600 --out quan-v12.jsonl
```

Kiểm trực tiếp: `tests/test_rules_p2p3.py::Freshness` (hao tươi giỏ/kho, `spoiled` theo id, giữ theo id, giá theo tươi, `test_bad_item_fixtures_exit_2`) và `tests/test_smoke_p1.py::Integration` (adapter schema kho cá thể).
