# Bằng chứng Phase 2 · Lát 1 (Hải) — Số chuẩn v1.1 + Cá bơi/sinh

- **Phạm vi:** `game.contract.json` (tuning v1.1) · `chonoi/sim/gather.py` (cá bơi/sinh) · khung (`inventory`/`scenario`/`contract`).
- **AC:** `AC-P2-01` (tuning v1.1) · `AC-P2-02` (cá bơi + sinh).
- **Test:** `tests/test_gather_fish_p2.py` (11 test) + sửa `tests/test_gather_water.py:136` (theo `docs/clarify.md` #5).

## Lệnh đã chạy
```powershell
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests     # Ran 80 tests ... OK
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out docs/proof/phase-2/out-gather-p2.jsonl   # exit 0
# smoke tích hợp (TICKET-02 §5):
python -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-2/dock.json --inputs docs/proof/phase-2/dock-inputs.json --ticks 1 --out docs/proof/phase-2/gather-p2.jsonl --inventory-out docs/proof/phase-2/catch.json
python -m chonoi.headless --mode quan   --seed 42 --inventory docs/proof/phase-2/catch.json --ticks 0 --out docs/proof/phase-2/quan-p2.jsonl
```
Kết quả: **80/80 test OK**; gather headless exit 0; cùng seed (7, 800 tick) **byte-giống**.

## `AC-P2-01` — Tuning v1.1
- `game.contract.json`: `contract_version:"1.1"`; `fish_yield = {ca_linh:3, ca_loc:1, ca_keo:2}`; 6 nút (thêm N5/N6 `keo_neo`);
  `fish_initial` 8 đàn; khối cá bơi/sinh (`fish_speed` 1.5, `fish_turn_every_ticks` 120, `fish_x_bounds` [4,96],
  `fish_depth_bands`, `fish_spawn`).
- Test `TuningV11`: version, fish_yield, 2 nút `keo_neo`, 8 đàn đầu ca.

## `AC-P2-02` — Cá bơi + sinh
- `_fish_step()` mỗi tick: đổi hướng theo seed ở bước bội 120 **trước** di chuyển; `_advance_fish()` bơi 1.5 m/s,
  phản xạ mép `x∈[4,96]` và dải độ sâu loài; `_spawn_fish()` mỗi 360 tick (trần 12, khoảng cách > 1 m, trọng số 40/30/30, hướng seed).
- Test `FishSwim`: bơi dịch chuyển, phản xạ mép x, giữ trong dải `ca_loc [8,20]`, đổi hướng đúng bước 120.
- Test `FishSpawn`: đầu ca 8, tick 360 → 9, trần 12 (2160 tick), `random_fish=false` tắt sinh.
- Test `Determinism`: cùng seed 800 tick ⇒ file giống từng byte.

## Smoke tích hợp Sáng → Tối
- `dock.json` (hold `ca_loc, bong_sung, bong_sung`) + `interact` tick 0 ⇒ `catch.json` = `{"items":{"bong_sung":2,"ca_loc":1}}`.
- Quán đọc `catch.json` ⇒ snapshot tick 0 `stock = {"bong_sung":2,"ca_loc":1}` (`quan-p2.jsonl`).

## Thay đổi test đã ghi lý do
- `tests/test_smoke_p1.py`: `len(fish)` **6 → 8** — số chuẩn v1.1 (TICKET-02 §1.2), không phải sửa cho xanh.
- `tests/test_gather_water.py:136`: nới assert `hold_full` để khớp hợp đồng §4 (Đức thêm `kind`; `docs/clarify.md` #5).

## Artifact
`out-gather-p2.jsonl` · `gather-p2.jsonl` · `catch.json` · `quan-p2.jsonl` · `dock.json` · `dock-inputs.json`.
