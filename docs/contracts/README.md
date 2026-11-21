# Hợp đồng tích hợp (Phase 1, contract v1.0)

## 1. File kho (gather → quan): PRD-0 mục G
```json
{"items": {"bong_sung": 2, "ca_loc": 1}}
```
- Chỉ có khóa gốc `items`: object `kind → số nguyên ≥ 0`. Kind hợp lệ: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Bên ghi bỏ các khóa có lượng 0 và sắp khóa theo tên. Kho rỗng là `{"items":{}}`.
- `gather --inventory-out` ghi **đúng một lần** khi có `gather_end` (ngất thì ghi kho rỗng). Nếu chạm `--ticks` trước khi buổi kết thúc thì không ghi. Ghi qua file tạm rồi thay thế nguyên tử.
- `quan --inventory` từ chối sai schema, kind lạ hoặc số âm (mã 2). Trần giỏ không áp lên kho quán.
- Mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json). Code: `chonoi/inventory.py`.

## 2. Giao diện sim ↔ UI
- Sim (`chonoi/sim/gather.py`, `chonoi/sim/quan.py`) nhận `InputState`: `move` (đã chuẩn hóa), cạnh lên của `interact` và `catch`. Mỗi bước trả về danh sách `(name, data)`.
- UI (`chonoi/web/index.html`) **chỉ đọc** snapshot qua `GET /state` (cùng trường với snapshot headless, thêm `meta`, `events`, `menu`, `campaign`) và gửi phím qua `POST /input`. `POST /restart` chơi lại buổi; `POST /next`, `POST /new` và `POST /buy {"id"}` (chỉ ở `chonoi.play`) dùng để sang bước kế, chơi mới và mua nâng cấp.
- Hiệu ứng ở UI (hạt, âm thanh, cá lượn) dùng RNG của trình duyệt và không đi vào sim.

## 3. Sự kiện (PRD-0 mục E)
| name | data | phát ở |
|---|---|---|
| `dive` / `surface` | `pos` sau di chuyển | gather, khi đổi phía biên mặt nước (d = 0.5) |
| `oxygen_empty` | `oxygen_ticks: 0` | gather, oxy từ dương xuống 0 |
| `choke` | `hp` sau trừ | gather, đủ 60 tick dưới nước với oxy 0 |
| `faint` | `cause:"choke"`, `lost` (LIFO), `hp:0` | gather, Máu về 0 |
| `gather` / `node_regrown` | `node_id,kind,amount` / `node_id` | gather |
| `hold_full` | `action`, `node_id`/`fish_id`, `required`, `free` | gather |
| `fish_caught` | `fish_id,kind,yield` | gather |
| `gather_end` | `reason` (time/docked/fainted), `inventory` | gather |
| `customer_arrived` / `no_dish` | `order_id,table_id,dish_id` / `{}` | quan, lịch khách |
| `cook_started` | `stove_id,order_id,dish_id,items,base_price` | quan, E ở bếp idle |
| `dish_ready` / `dish_picked` | `stove_id,order_id,dish_id` | quan |
| `served` | `order_id,table_id,dish_id,patience_ticks_left,base_price,tip` | quan, E ở bàn |
| `paid` | `order_id,table_id,base_price,tip,amount,reason` | quan |
| `customer_left` | `order_id,table_id,reason,reputation` | quan |
| `quan_end` | `reason:"time",money,earned,shift_earned,reputation` | quan |

Khi đổi hợp đồng: báo cả nhóm và ghi lý do (ADR trong `docs/adr/`).
