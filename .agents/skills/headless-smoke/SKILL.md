---
name: headless-smoke
description: Chạy toàn bộ test và smoke hai tiến trình (gather -> file kho -> quan) theo hợp đồng tích hợp, rồi ghi kết quả. Dùng trước khi commit, đẩy hoặc gắn tag phase-n.
---

# headless-smoke

1. Chạy toàn bộ test (phải xanh):
   `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
   (Windows: `PYTHONPATH="tests;."`)
2. Smoke hai tiến trình trong thư mục tạm (schema **kho cá thể v1.2/v1.3**):
   ```bash
   echo '{"gather":{"hold":[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"bong_sung","fresh":100},{"id":"I3","kind":"bong_sung","fresh":100}]}}' > dock.json
   echo '{"frames":[{"tick":0,"interact":true}]}' > dock-inputs.json
   python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
   python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
   ```
   - Windows/PowerShell: ghi file bằng UTF-8 **không BOM** (dùng `[System.IO.File]::WriteAllText($p, $json, (New-Object System.Text.UTF8Encoding($false)))`); BOM làm runner báo `Unexpected UTF-8 BOM` và thoát **2**.
   - Yêu cầu: cả hai lệnh thoát mã **0**; `catch.json` có 3 cá thể `{id, kind, fresh}` (sau 1 tick `fresh ≈ 99.99`); dòng đầu `quan.jsonl` có `stock` là đúng 3 cá thể đó.
   - Kho đếm cũ `{"items":{kind:int}}` **không còn hợp lệ** ở v1.2+ (`kind lạ`/kho đếm ⇒ mã 2); không dùng lại fixture cũ.
3. Tất định: chạy cùng một lệnh hai lần rồi so byte (`cmp out1.jsonl out2.jsonl`).
4. Ghi kết quả thật (lệnh, mã thoát, số test) vào `docs/proof/phase-n/` và mô tả commit. Không sửa test cho xanh khi luật sai.
