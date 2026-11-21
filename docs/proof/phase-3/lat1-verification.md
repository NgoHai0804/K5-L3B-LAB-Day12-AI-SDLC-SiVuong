# Bằng chứng Phase 3 — Lát 0 (adapter kho cá thể) + Lát 1 (Lặn: hao tươi) — Hải

- **AC:** `AC-P3-01` (schema cá thể + chọn theo version, mã 2 cho kho đếm) · `AC-P3-02` (hao tươi + `spoiled`) · `AC-P3-06`/`AC-P3-07` (manifest/freshness + migration giữ main chạy).
- **Trạng thái:** adapter + gather sẵn sàng, **gate theo `contract_version`**; đang **giữ v1.1** để main xanh (ADR-0002). Bật v1.2 ở bước tích hợp cuối.

## Lệnh đã chạy
```powershell
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests        # Ran 137 tests ... OK
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out docs/proof/phase-3/out-gather.jsonl   # exit 0
# cùng seed (7, 400 tick) ⇒ byte-identical (đã hash 2 lần chạy)
```

## `AC-P3-01` / `AC-P3-06` / `AC-P3-07` — adapter kho cá thể
- `chonoi/inventory.py`: `validate_carried` (`{id,kind,fresh}`, id duy nhất, kind hợp lệ, `fresh∈[0,100]`);
  `read_inventory(path, version)` chọn schema theo `contract_version`; **v1.2 từ chối dict (kho đếm) ⇒ BadInput/mã 2**;
  `write_inventory` ghi mảng cá thể, nguyên tử.
- Số nguyên tươi 240/điểm: `fresh_to_units(30)=7200`; `units_to_fresh` khứ hồi giữ đúng nhánh ngưỡng 30.
- `game.contract.json`: `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`;
  `contract.py` kiểm dải. `contract_version` **giữ `"1.1"`** (bật 1.2 sau khi Quán/HUD xong).
- Thread version: `runner.build_sim/Session/run`, `headless.py`, `live.py`.

Test: `test_gather_freshness.py::InventoryAdapter` (validate, v1.2 từ chối kho đếm, round-trip file, ngưỡng 30).

## `AC-P3-02` — Lặn: hao tươi giỏ + `spoiled` + LIFO
- `gather.py` (gate `version>=1.2`): `hold` cá thể `{id,kind,u}`; **hao −2 đơn vị/tick** ở đầu bước; `spoiled` một lần khi
  `u<7200` (theo id); hàng mới `fresh=100` + id `I…`, hao từ bước sau; **LIFO** khi ngất; bàn giao mảng cá thể.
- Fixture ngưỡng (TEAM §“Fixture kiểm ngưỡng”): `hold [{I1,ca_linh,30}]`, một bước không input ⇒ `spoiled` ở bước 1.

Test: `test_gather_freshness.py::GatherFreshness` (cá thể hoá hold, `spoiled` bước 1, hàng mới 100 + id mới,
hao đúng 2 đơn vị/tick, LIFO khi ngất, v1.1 vẫn schema đếm).

## Chưa chạy được (phụ thuộc)
- Smoke **file** v1.2 (`gather --inventory-out` → `quan --inventory`): cần **bật v1.2** + Quán đọc schema cá thể.
- Smoke `day` bàn giao cùng tick: cần `day` (Tùng) nâng cấp theo cá thể.
- Regression P1–P2 với v1.2: cần cập nhật fixture sang mảng cá thể.

## Artifact
`out-gather.jsonl` (headless v1.1, không đổi so với Phase 2).
