# Bằng chứng kiểm chứng Phase 4 — Phát hành `v1.0.0` (Nguyễn Thanh Tùng)

## 1. Benchmark 30 giây (1280×720, seed 42, warmup 3 s)
Lệnh:
```powershell
python -m chonoi.bench --seed 42 --duration 30 --warmup 3 --out docs/proof/phase-4/bench.json
```
Kết quả (`docs/proof/phase-4/bench.json`):
```json
{"avg_fps":63.17,"p1_low_fps":38.03,"frames":1896,"measured_s":30.013,"load_ms":0.39}
```
- `avg_fps = 63.17` (đạt mốc ≥ 60 FPS)
- `p1_low_fps = 38.03` (đạt mốc ≥ 30 FPS)
- `load_ms = 0.39 ms` (đạt mốc ≤ 10 s)

## 2. Soak headless 10 Ngày (seed 7)
Lệnh:
```powershell
python -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json
```
Kết quả (`docs/proof/phase-4/soak.json`):
```json
{"days":10,"days_completed":10,"crashes":0,"results":[{"day":1,"earned":48,"reputation":3.2,"score":348},{"day":2,"earned":48,"reputation":3.2,"score":348},{"day":3,"earned":96,"reputation":3.4,"score":396},{"day":4,"earned":144,"reputation":3.6,"score":444},{"day":5,"earned":144,"reputation":3.6,"score":444},{"day":6,"earned":192,"reputation":3.8,"score":492},{"day":7,"earned":192,"reputation":3.8,"score":492},{"day":8,"earned":240,"reputation":4.0,"score":640},{"day":9,"earned":288,"reputation":4.2,"score":688},{"day":10,"earned":288,"reputation":4.2,"score":688}],"duration_s":0.8238}
```

## 3. Regression P1–P4
Lệnh:
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_quan_lat4 tests.test_quan_p2 tests.test_quan_p3 tests.test_phase4 tests.test_python_starter_units tests.test_team_check -v
```
Kết quả: **Ran 40 tests in 3.015s — OK**.
