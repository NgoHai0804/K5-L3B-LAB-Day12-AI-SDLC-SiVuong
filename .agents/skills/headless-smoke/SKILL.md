---
name: headless-smoke
description: Chạy toàn bộ test và smoke hai tiến trình (gather -> file kho -> quan) theo PRD-0 mục G, rồi ghi kết quả. Dùng trước khi commit, đẩy hoặc gắn tag phase-n.
---

# headless-smoke

1. Chạy toàn bộ test (phải xanh):
   `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
   (Windows: `PYTHONPATH="tests;."`)
2. Smoke hai tiến trình trong thư mục tạm:
   ```bash
   echo '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > dock.json
   echo '{"frames":[{"tick":0,"interact":true}]}' > dock-inputs.json
   python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
   python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
   ```
   Yêu cầu: cả hai lệnh thoát mã 0; `catch.json` = `{"items":{"bong_sung":2,"ca_loc":1}}`; dòng đầu `quan.jsonl` có `"stock":{"bong_sung":2,"ca_loc":1}`.
3. Tất định: chạy cùng một lệnh hai lần rồi so byte (`cmp out1.jsonl out2.jsonl`).
4. Ghi kết quả thật (lệnh, mã thoát, số test) vào `docs/proof/phase-n/` và mô tả commit. Không sửa test cho xanh khi luật sai.
