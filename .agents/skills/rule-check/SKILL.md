---
name: rule-check
description: Đối chiếu một thay đổi luật (sim/gather.py, sim/quan.py, scenario.py) với PRD/ticket đúng phase trước khi code. Dùng khi nhận ticket mới hoặc change request.
---

# rule-check

1. Đọc PRD/ticket của phase hiện tại trong `docs/prd/`. Đọc `docs/contracts/README.md` và `game.contract.json`.
2. Với mỗi câu luật bị ảnh hưởng, ghi: câu PRD → hàm sẽ sửa → event/field snapshot bị đổi → test sẽ thêm hoặc sửa.
3. Kiểm các bất biến:
   - Số liệu chỉ đọc từ `game.contract.json`. Đổi giây sang tick bằng `int(round(s * 60))`.
   - Ngẫu nhiên chỉ qua `Streams` (mỗi mục đích một luồng riêng). Không dùng `random` toàn cục, không dùng đồng hồ.
   - Thứ tự xử lý trong một bước đúng PRD mục F. Event ghi theo thứ tự xử lý. Danh sách thực thể sắp bằng `ids.sort_by_id`.
   - Dữ liệu sai hoặc mâu thuẫn bị phát hiện lúc dựng (trước khi ghi đầu ra) thì thoát mã 2.
   - Phần sáng tạo tắt ở headless.
4. Chỗ PRD mơ hồ hoặc mâu thuẫn với phase trước: ghi vào `docs/clarify.md` (câu hỏi, giả định, ai quyết). Nếu đổi hợp đồng thì viết ADR.
5. Viết test hộp đen trong `tests/test_rules_p<n>.py` trước, sửa luật sau, rồi chạy skill `headless-smoke`.
