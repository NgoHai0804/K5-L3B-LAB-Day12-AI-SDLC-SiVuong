# Credits

## Asset ngoài
Không dùng asset ngoài. Toàn bộ nhân vật, bối cảnh, cá, thủy quái, món ăn và giao diện là **đồ họa vẽ bằng code** (`chonoi/web/index.html`, Canvas 2D) — bản gốc của lab, không có giấy phép bên thứ ba.

## Công cụ AI đã dùng
- **Claude / agent CLI** (Anthropic): hỗ trợ viết luật, test và tài liệu qua bốn phase. Chi tiết theo người ở `docs/ai-usage-log.md`.
- Mọi số liệu và luật vẫn đọc từ `game.contract.json`; nhóm tự review và chạy test trước khi gộp.

## Thư viện
- Chỉ dùng **thư viện chuẩn Python 3.10+** (không phụ thuộc ngoài).
- Test dùng `unittest` (chuẩn).
