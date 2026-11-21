# Changelog

## v1.0.0 — Phase 4 (Phát hành & Kiểm chứng hiệu năng · Contract v1.3)
### Tính năng & Công cụ mới
- **Benchmark có render (`chonoi/bench.py`)**: Chạy `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` ở 1280×720 (làm nóng 3 s, đo 30 s), xuất đủ 5 trường `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`.
- **Soak headless 10 Ngày (`chonoi/soak.py`)**: Chạy `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` với bot tất định đi qua 10 chu kỳ `gather → quan → shop`, lặp kế hoạch D1–D5, 0 crash.
- **Mở rộng Bảng xếp hạng cục bộ (`chonoi/leaderboard.py`)**: Top 10 bền vững, hòa điểm giữ thứ tự ghi trước, hỗ trợ xuất `--export-leaderboard`.
- **Cảnh báo tương phản cao & Phụ đề SFX (`chonoi/content/dave_theme.py`)**: 3 cảnh báo rõ ràng (thủy quái gần, cạn oxy, khách sắp giận) và phụ đề SFX tiếng Việt cho chế độ tắt tiếng.
- **Hoàn thiện tài liệu phát hành**: `docs/release-notes-v1.0.0.md`, `docs/retro.md`, `docs/ai-usage-log.md`, `docs/members/wewewewe07.md`, `docs/verification/phase-4.md`.

## Phase 3 — Contract v1.2 ("Mùa Nước Nổi" — Độ tươi & Kho cá thể)
### Breaking Changes
- **Schema kho đếm → kho cá thể**: `{"items": {"ca_loc": 1}}` chuyển sang `{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}` (mảng cá thể duy nhất theo `id`, độ tươi `fresh ∈ [0, 100]`, xuất theo `id`). Ở `contract_version: "1.2"`, file kho đếm cũ trả mã thoát `2`.
- **`customers[].reserved`**: chuyển từ map `{kind: int}` sang mảng `id` cá thể `["I1", "I2"]`.
- **`cook_started.data.items`**: chuyển từ mảng `kind` sang mảng cá thể `{id, kind, fresh}` sắp theo `(kind, id)`.
- **Giá món theo độ tươi**: `base_price = floor(giá_niêm_yết × trung_bình_fresh / 100)` chốt lúc bắt đầu nấu; boa `floor(base_price × 0.2)` áp trên giá đã chốt.
- **Sự kiện mới `spoiled`**: `{"item_id", "kind", "location"}` (`hold`/`stock`) phát đúng 1 lần khi `fresh` đi từ `≥ 30` xuống `< 30`.

### Cách cập nhật fixture (v1.0/v1.1 → v1.2)
- Đổi `gather.hold: ["ca_loc"]` → `gather.hold: [{"id": "I1", "kind": "ca_loc", "fresh": 100}]`.
- Đổi `quan.stock: {"ca_loc": 1}` → `quan.stock: [{"id": "I1", "kind": "ca_loc", "fresh": 100}]`.
- Đổi `quan.customers[].reserved: {"ca_loc": 1}` → `quan.customers[].reserved: ["I1"]` (hoặc bỏ trống để sim tự cấp theo tươi nhất rồi `id` nhỏ).
- **Lộ trình chuyển đổi không vỡ `main`**: `chonoi/sim/quan.py` hỗ trợ song song v1.0/v1.1 (kho đếm) và v1.2 (khi có khối `freshness` trong tuning hoặc `stock` là mảng cá thể) để giữ regression P1/P2 xanh cho tới khi cả hai đầu bàn giao bật `contract_version: "1.2"`.
