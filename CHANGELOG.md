# Changelog

## Unreleased

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
