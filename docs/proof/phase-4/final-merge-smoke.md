# Bằng chứng gộp bản chơi cuối lên `main` (Phase 4)

Chạy trên Windows 11, Python 3.12, thư mục worktree từ `origin/main` (f2ea69b) + bản game cục bộ của buiquyanh9-ai.

| Bước | Lệnh | Kết quả |
|---|---|---|
| Toàn bộ test | `PYTHONPATH="tests;." python -m unittest discover -s tests` | `Ran 122 tests … OK` |
| Smoke 2 tiến trình (gather → kho) | `python -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json` | mã 0; `catch.json` = 3 cá thể `I1 ca_loc`, `I2/I3 bong_sung`, `fresh=99.9917` |
| Smoke 2 tiến trình (kho → quán) | `python -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl` | mã 0; snapshot đầu `stock` đúng 3 cá thể đó (`fresh 99.992`) |
| Tất định | `--mode gather` / `--mode quan --seed 1 --ticks 600` chạy 2 lần, `cmp` | giống từng byte |
| Tất định Ngày | `--mode day --days 5 --seed 1 --ticks 60000` chạy 2 lần, `cmp` | mã 0, giống từng byte |
| Soak | `python -m chonoi.soak --seed 7 --days 10 --out soak.json` | mã 0; `days_completed=10`, `crashes=0` |
| Bench (ngắn, máy cá nhân) | `python -m chonoi.bench --seed 42 --duration 5 --out bench.json` | mã 0; đủ 5 trường (`avg_fps≈73.9`, `frames=370`); số chính thức 30 s vẫn là `bench.json` |
| Cửa sổ chơi | `python -m chonoi.play --port 8765` rồi `GET /`, `GET /state` | `/` 200 (135 KB), `/state` trả snapshot `mode:"day"`, Ngày 1 |
| JS client | trích `<script>` của `chonoi/web/index.html`, `node --check` | hợp lệ (không trùng tên hàm) |

Ghi chú trung thực: `python -m chonoi.play --help` lỗi `UnicodeEncodeError` trên console Windows cp1252 (chuỗi mô tả tiếng Việt); chạy với `PYTHONIOENCODING=utf-8` thì bình thường. Không ảnh hưởng headless.
