# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`; vòng ngày dùng `--mode day --days 1..5`.
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` hoặc `--mode day --days 1`; WASD, E, Space, P/Esc, R.

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `inventory-handoff-smoke`: dùng khi kiểm tra bàn giao `gather → kho.json → quan`; chạy script độc lập, không sửa contract hay fixture khóa.
  - Lệnh: `python3 .agents/skills/inventory-handoff-smoke/scripts/run_smoke.py`
- `verify-phase-change`: dùng trước commit/push hoặc khi thu bằng chứng cho một phase; đọc diff, chạy toàn bộ test và ghi kết quả trung thực vào `docs/proof/`.
  - Lệnh test chuẩn: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- `pause-contract-smoke`: dùng khi sửa input, tick loop, pause hoặc Shop để kiểm tra đóng băng và resume đúng Contract v1.1.
  - Lệnh: `python3 .agents/skills/pause-contract-smoke/scripts/run_smoke.py`
