# ADR-0002: Kho cá thể + độ tươi (migration sang contract v1.2)

- Trạng thái: **chấp nhận** (đã áp dụng ở Phase 3 — contract v1.2, giữ ở v1.3) — thay thế phần schema kho của ADR-0001 (vẫn giữ tập kind v1.1)
- Ngày, người quyết: 2026-11-21 · Change Request “Mùa Nước Nổi” (TICKET-03) — đề xuất bởi Sơn (AI/Contracts lead) + Hải (Integrator)

## Bối cảnh
TICKET-03 **[THAY THẾ]** kho đếm theo loại `{<kind>: int≥0}` bằng **kho cá thể** `{"items":[{id,kind,fresh}]}` để theo dõi
**độ tươi** từng nguyên liệu. Đây là **thay đổi phá vỡ** định dạng file kho — điểm giao duy nhất Sáng↔Tối — nên phải
chọn cách chuyển để **main vẫn chạy được** trong lúc tích hợp và để bên đọc biết chọn schema theo `contract_version`.

## Các lựa chọn đã cân nhắc
1. **Đổi thẳng sang v1.2**: sửa `inventory.py`/`scenario.py`/`contract.py`/`jsonl.py` cùng lúc, bỏ schema đếm. Rủi ro: mọi test/fixture P1–P2 vỡ ngay, không có đường lùi nếu một đầu chưa bàn giao.
2. **Adapter hai schema nội bộ**: đọc/ghi theo `contract_version`; hỗ trợ **cả** kho đếm (v1.0/v1.1) **và** kho cá thể (v1.2) trong thời gian chuyển; **bật v1.2** làm mặc định khi cả hai đầu sẵn sàng. Ở v1.2, **kho đếm trả mã 2**.
3. **Giữ kho đếm, thêm trường `fresh` song song**: không khớp yêu cầu [THAY THẾ] (giá theo tươi, giữ theo id, LIFO theo cá thể) → loại.

## Quyết định
Chọn **(2)**. Cụ thể:
- `chonoi/inventory.py`: thêm schema cá thể `{"items":[{id,kind,fresh}]}`; `id` khác rỗng & duy nhất, `kind` trong danh mục, `fresh` hữu hạn `[0,100]`; kho rỗng `{"items":[]}`; **chọn schema theo `contract_version`**; v1.2 từ chối kho đếm / sai schema / kind lạ / id trùng / fresh ngoài miền ⇒ **mã 2**.
- `chonoi/jsonl.py`: snapshot `hold`, `stock`, `customers[].reserved`; `cook_started.data.items` sắp **theo kind rồi id**; `lost` theo thứ tự bỏ **LIFO**; event **`spoiled`** `{item_id,kind,location}`; dung sai quan sát **±0.01**.
- `chonoi/contract.py`, `chonoi/scenario.py`: `gather.hold`/`quan.stock`/`customers[].reserved` là **mảng cá thể/id**; trong `day` Ngày đầu giữ id mẫu, Ngày kế cấp id mới; **id vật lý duy nhất** giữa các nơi chứa; `reserved` phải trỏ cá thể **chưa ươn, đủ công thức, không dùng chung**; sai ⇒ mã 2.
- `game.contract.json`: `contract_version:"1.2"` + `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`.
- Cấp id bằng **một `IdAllocator` chung** (`I1,I2,…`), tăng **xuyên pha và Ngày**; LIFO theo thứ tự vào giỏ.

## Hệ quả (bảng tác động)
| Module/file | Thay đổi | Ảnh hưởng |
|---|---|---|
| `chonoi/inventory.py` | schema cá thể + chọn theo version + mã 2 | writer/reader; file kho đếm ⇒ mã 2 ở v1.2 |
| `chonoi/jsonl.py` | `hold`/`stock`/`reserved`/`items`/`lost`/`spoiled` | test JSONL; ±0.01 |
| `chonoi/contract.py`, `scenario.py` | mảng cá thể/id, id duy nhất, `reserved` hợp lệ | test scenario/schema; sai ⇒ mã 2 |
| `chonoi/sim/gather.py` | hao tươi giỏ, `spoiled`, LIFO | `tests/test_gather_*` |
| `chonoi/sim/quan.py` | hao tươi kho, giữ theo id, giá theo tươi | `tests/test_quan_*` |
| `chonoi/sim/day.py` | bàn giao cùng tick, không hao thêm, id xuyên Ngày | test `day` |
| `game.contract.json` | v1.2 + `freshness` | nguồn số liệu mới |
| `tests/test_smoke_p1.py` | fixture kho cá thể, `hold`/`stock` mảng | cập nhật có lý do trong `docs/verification/phase-3.md` |

- **Breaking change**: ghi vào `CHANGELOG.md`. **Regression P1–P2** phải còn hiệu lực; bật v1.2 khi cả hai đầu bàn giao sẵn sàng.
- **Thứ tự tích hợp**: schema/adapter + test migration **trước** → Lặn/Quán/HUD **song song** → hai phiên bản nội bộ → **bật v1.2** (kho đếm ⇒ mã 2).
