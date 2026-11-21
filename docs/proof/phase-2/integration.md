# Smoke tích hợp Phase 2 — gather --inventory-out → quan --inventory (Lát 3 / QA lead)

Chạy trên nhánh `QuyAnh` với dữ liệu quán v1.1 (4 bàn, 6 món).

```
$ python3 -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather-p2.jsonl --inventory-out catch.json
exit=0
$ cat catch.json
{"items":{"bong_sung":2,"ca_loc":1}}
$ python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan-p2.jsonl
exit=0
$ head -1 quan-p2.jsonl
{"type":"snapshot","tick":0,"sim_tick":0,"mode":"quan","phase":"quan","phase_tick":0,"state":"playing","time_left_ticks":10800,"money":0,"earned":0,"reputation":3.0,"score":300,"player":{"pos":[8.0,5.0],"vel":[0.0,0.0]},"stock":{"bong_sung":2,"ca_loc":1},"hand":null,"stoves":[{"id":"B1","pos":[2.0,8.0],"state":"idle","dish":null,"cook_ticks_left":0,"ready_ticks":0},{"id":"B2","pos":[5.0,8.0],"state":"idle","dish":null,"cook_ticks_left":0,"ready_ticks":0}],"tables":[{"id":"T1","pos":[9.0,2.0],"customer_id":null},{"id":"T2","pos":[13.0,2.0],"customer_id":null},{"id":"T3","pos":[9.0,6.0],"customer_id":null},{"id":"T4","pos":[13.0,6.0],"customer_id":null}],"customers":[]}
```

Kết quả: snapshot quán tick 0 có `"stock":{"bong_sung":2,"ca_loc":1}`, đúng file tiến trình đầu ghi, và liệt kê đủ B1–B2, T1–T4 → **Đạt**.

`--mode day --days 1` chưa chạy được ở commit này (CLI `day` thuộc Lát 4a/4b của Tùng, Sơn).
