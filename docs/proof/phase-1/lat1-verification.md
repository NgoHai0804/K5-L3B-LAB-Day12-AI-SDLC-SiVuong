# Bằng chứng Lát 1 (Hải) — Bơi · Oxy · Ngạt · Biên · Giỏ

- **Phạm vi:** `chonoi/sim/gather.py` (lát 1) · test `tests/test_gather_water.py` (9 test) · AC `AC-P1-01..04`.
- **Khung có sẵn (không viết lại):** bơi + ramp + chặn mép (`_move`/`ramp_velocity`), đồng hồ, cập bến. Lát 1 thêm:
  `_water()` (biên mặt nước → oxy → ngạt → ngất) và seam giỏ `_hold_free()` / `_try_hold()`.

## Lệnh đã chạy

```powershell
# Toàn bộ test (đóng băng + luật lát 1)
$env:PYTHONPATH="tests;."; python -m unittest discover -s tests
# Ran 41 tests ... OK   (9 test mới trong test_gather_water.py đều xanh)

# Headless chạy sạch 600 tick
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out docs/proof/phase-1/out-gather.jsonl   # exit 0, 62 dòng, dòng cuối reason "tick_limit"
```

Kết quả: **41/41 test OK**; headless exit 0.

## Bằng chứng theo AC

### `AC-P1-01` — Bơi / ramp / chặn biên
Khung `_move` giữ nguyên; `test_smoke_p1.py::Movement` (ramp trong trần, chặn 4 mép, `d` không âm, heading dương = xuống,
đi chéo ≈ `swim_speed`) vẫn **xanh**.

### `AC-P1-02` — Oxy / biên mặt nước / `oxygen_empty`
Từ `out-choke.jsonl` (nước, `oxygen_ticks` khởi tạo 1):

```json
{"type":"event","tick":1,"phase":"gather","name":"oxygen_empty","data":{"oxygen_ticks":0}}
```

Test `Oxygen.test_01` (rút cạn + `oxygen_empty` đúng 1 lần, tick 2), `test_02` (hồi ở mặt nước 10 → 16),
`SurfaceBoundary.test_03_dive_surface` (`dive`/`surface` chỉ khi đổi phía, data `{pos}`).

### `AC-P1-03` — Ngạt / `choke` / `faint`
Từ `out-choke.jsonl` (dưới nước, oxy chạm 0 ở tick 1):

```json
{"type":"event","tick":60,"phase":"gather","name":"choke","data":{"hp":2}}
```

⇒ ngạt đầu đúng ở tick `1 + 59 = 60` (kẹp đếm `zero_oxy_ticks`, `choke_interval_ticks = 60`), −1 Máu.
`test_04_surfacing_at_choke_step_avoids_choke`: nổi lên đúng bước đáng ngạt ⇒ hồi oxy, **không** ngạt (hp giữ 3).

Từ `out-faint.jsonl` (`hp = 1`, `zero_oxy_ticks = 59`):

```json
{"type":"event","tick":1,"phase":"gather","name":"choke","data":{"hp":0}}
{"type":"event","tick":1,"phase":"gather","name":"faint","data":{"cause":"choke","lost":["bong_sung","bong_sung","ca_loc"],"hp":0}}
{"type":"event","tick":1,"phase":"gather","name":"gather_end","data":{"reason":"fainted","inventory":{"items":{}}}}
```

`lost` là **mảng kind theo thứ tự bỏ LIFO** (nhặt `ca_loc, bong_sung, bong_sung` ⇒ bỏ ngược lại), khớp
`docs/contracts/README.md` §4. Kho ghi ra `docs/proof/phase-1/inv-faint.json` = `{"items":{}}` (rỗng).

### `AC-P1-04` — Giỏ LIFO / `hold_full`
Seam `_try_hold()` cho lát 2 (Đức) gọi: đủ chỗ ⇒ append (LIFO); thiếu chỗ ⇒ `hold_full`
(`action`, `node_id`/`fish_id`, `required`, `free`), không thêm. `HoldSeam.test_06` kiểm cả hai nhánh.
LIFO khi bỏ giỏ được kiểm gián tiếp qua `faint.lost` ở trên.

## Artifact
- `out-gather.jsonl` — headless 600 tick, exit 0.
- `out-choke.jsonl` / `lat1-choke.json` — kịch bản ngạt.
- `out-faint.jsonl` / `lat1-faint.json` / `inv-faint.json` — kịch bản ngất + kho rỗng.
