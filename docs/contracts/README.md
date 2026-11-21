# Hợp đồng tích hợp (gather → quan)

> Cập nhật theo **Contract v1.3** (v1.3 = v1.2 gameplay/tuning/kho/JSONL + `bench_cmd`/`soak_cmd`). Schema kho đã đổi
> ở v1.2 sang **kho cá thể + độ tươi** (breaking) — xem `docs/adr/0002-kho-ca-the-do-tuoi.md` và `CHANGELOG.md`.

## 1. File kho (gather → quan)
```json
{"items":[{"id":"I1","kind":"bong_sung","fresh":100},{"id":"I2","kind":"bong_sung","fresh":100},{"id":"I3","kind":"ca_loc","fresh":100}]}
```
- Chỉ có khóa gốc `items`; `items` là **mảng cá thể** `{id, kind, fresh}`.
  - `id`: chuỗi khác rỗng, **duy nhất** (giữa mọi nơi chứa); `I1, I2, ...` tăng **xuyên pha/Ngày** (một `IdAllocator`).
  - `kind` hợp lệ: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`.
  - `fresh`: hữu hạn trong `[0, 100]` (đơn vị tươi; 240 đơn vị = 1 điểm trong mô phỏng).
- Kho rỗng là `{"items":[]}`. Bên ghi sắp theo `id`, ghi nguyên tử (file tạm cùng thư mục rồi `os.replace`).
- **Đọc:** từ chối **kho đếm v1.0/v1.1** `{"items":{kind:int}}`, sai schema, kind lạ, id trùng, `fresh` ngoài `[0,100]`
  ⇒ **mã 2**. Bên đọc **chọn schema theo `contract_version`** (`chonoi/contract.py::SUPPORTED_VERSIONS = ("1.3","1.2")`).
- `gather --inventory-out` ghi **đúng một lần** khi có `gather_end` (ngất ⇒ `{"items":[]}`); chạm `--ticks` trước khi
  buổi kết thúc thì **không** ghi.
- Mẫu hợp lệ: [`inventory.sample.json`](inventory.sample.json). Code: `chonoi/inventory.py`.

## 2. Giao diện sim ↔ UI
- Sim (`chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/sim/day.py`) nhận `InputState`: `move` (đã chuẩn hóa),
  cạnh lên của `interact`, `catch`, `pause`, `shop_done` (và `attack`/`photo` khi bật mở rộng), cùng lệnh frame `buy`.
  Mỗi bước trả về danh sách `(name, data)`.
- UI (`chonoi/web/index.html`) **chỉ đọc** snapshot qua `GET /state` (cùng trường với snapshot headless, thêm
  `meta`, `events`, `menu`, `campaign`) và gửi phím qua `POST /input`. `POST /restart` chơi lại buổi; `POST /next`,
  `POST /new` và `POST /buy {"id"}` (chỉ ở `chonoi.play`) sang bước kế, chơi mới và mua nâng cấp.
- Hiệu ứng ở UI (hạt, âm thanh, cá lượn, chú thích cảnh báo) dùng RNG trình duyệt và **không** đi vào sim.

## 3. Sự kiện
> Tên + `data`. `spoiled` / `monster_hit` / `fish_spawned` là của v1.2–v1.3; `paused`/`resumed`/`bought`/`buy_failed`/
> `shop_end` của vòng `day` + Shop.

### gather
| name | data | phát ở |
|---|---|---|
| `dive` / `surface` | `pos` | khi đổi phía biên mặt nước (`d = surface_depth`) |
| `oxygen_empty` | `oxygen_ticks: 0` | oxy từ dương xuống 0 |
| `choke` | `hp` (sau trừ) | đủ `choke_interval_ticks` dưới nước với oxy 0 |
| `faint` | `cause`(`choke`/`monster`), `lost` (mảng cá thể theo LIFO), `hp:0` | Máu về 0 |
| `gather` / `node_regrown` | `node_id,kind,amount` / `node_id` | hái nút / nút mọc lại |
| `hold_full` | `action`(`gather`/`catch`), `node_id`\|`fish_id`, `required`, `free` | giỏ không đủ chỗ |
| `fish_caught` | `fish_id,kind,yield` | bắt đủ yield một đàn |
| `fish_spawned` | `id,kind,pos` | sinh đàn theo lịch (`fish_spawn_ticks`) |
| `monster_hit` | `monster_id,hp,lost,pos` | Cá Sấu chạm người chơi (lost LIFO) |
| `spoiled` | `item_id,kind,location` (một lần khi vượt ngưỡng, theo id) | hàng vừa ươn (`fresh < 30`) |
| `gather_end` | `reason`(`time`/`docked`/`fainted`), `inventory` (mảng cá thể) | kết thúc buổi sáng |

### quan
| name | data | phát ở |
|---|---|---|
| `customer_arrived` / `no_dish` | `order_id,table_id,dish_id` / `{}` | lịch khách / có bàn mà thiếu món |
| `cook_started` | `stove_id,order_id,dish_id,items,base_price` | E ở bếp idle |
| `dish_ready` / `dish_picked` | `stove_id,order_id,dish_id` | bếp chín / bưng đĩa |
| `served` | `order_id,table_id,dish_id,patience_ticks_left,base_price,tip` | E ở bàn |
| `paid` | `order_id,table_id,base_price,tip,amount,reason`(`finished_eating`/`closing`) | khách trả tiền |
| `customer_left` | `order_id,table_id,reason`(`patience`/`closing`), `reputation` | khách bỏ về |
| `spoiled` | `item_id,kind,location="stock"` | hàng kho quán vừa ươn |
| `quan_end` | `reason:"time",money,earned,shift_earned,reputation` | hết ca |

### day / Shop (Event vỏ mode `day` có thêm trường `day`)
| name | data |
|---|---|
| `day_start`, `phase_start` | `{}` / phase mới |
| `day_plan` | `dishes,ingredients` của Ngày đó |
| `paused`, `resumed` | `{}` |
| `bought` / `buy_failed` | `upgrade,level,price,money` / `action,reason`(`funds`/`max_level`/`unknown`) |
| `shop_end` | `reason`(`done`/`time`) |

Khi đổi hợp đồng: báo cả nhóm và ghi lý do (ADR trong `docs/adr/`).
