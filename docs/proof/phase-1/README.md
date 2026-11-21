# Bằng chứng Phase 1

> Bản chạy **Contract v1.0** (kho đếm `{"items":{kind:int}}`, `hold` là mảng kind) lúc gắn tag `phase-1`.
> Đây là bằng chứng lịch sử của phase; schema kho đã đổi ở v1.2 (xem `docs/proof/phase-3/`).

| File | Nội dung | Cho thấy |
|---|---|---|
| `out-gather.jsonl` | `--mode gather --seed 1 --ticks 600` | Snapshot tick 0 (`pos [2,0]`, 4 nút N1–N4, 6 đàn cá), dòng cuối `end` |
| `out-choke.jsonl` | gather fixture dưới nước, oxy 0 | Tick 1 `oxygen_empty {oxygen_ticks:0}` → tick 60 `choke {hp:2}` |
| `out-faint.jsonl` | gather fixture HP 1, dưới nước, `zero_oxy_ticks:59` | Tick 1 `choke {hp:0}` → `faint {cause:"choke",lost:[…LIFO…],hp:0}` → `gather_end {reason:"fainted",inventory:{items:{}}}` |

## Tái lập
```bash
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out-gather.jsonl
# out-choke.jsonl / out-faint.jsonl dùng scenario+inputs dựng tình huống ngạt/ngất (xem tests/test_rules_p1.py::Oxygen)
```

Kiểm hộp đen trực tiếp: `tests/test_smoke_p1.py` (Contract/Movement/Integration/ScenarioModes) và `tests/test_rules_p1.py` (Oxygen/Harvest/Catch/Customers/Service).
