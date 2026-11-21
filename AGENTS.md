# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless (contract v1.3): `python3 -m chonoi.headless --mode gather|quan|day [--days 1-5] --seed 1 --ticks 600 --out out.jsonl`
- Bảng xếp hạng (chỉ `--mode day` đủ 5 Ngày chuẩn, không scenario): `python3 -m chonoi.headless --mode day --days 5 --seed 42 --ticks 200000 --leaderboard leaderboard.json --player-name "Út Sen" --out out.jsonl`
- Bench có render: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` (5 trường: avg_fps, p1_low_fps, frames, measured_s, load_ms)
- Soak nhiều Ngày: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` (đạt khi days_completed == days và crashes == 0)
- Chơi trọn 5 Ngày: `python3 -m chonoi.play` (WASD, Shift sprint, E, Space, Esc/P, Enter, 1–7, R, M, H tương phản cao, Q thả đồ, C đóng quán sớm, minigame sơ chế S/↓ · Space/E · A↔D)
- Xuất bảng xếp hạng: `python3 -m chonoi.play --export-leaderboard bang-xep-hang.json`
- Chơi thử từng buổi: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)
- PRD/ticket theo phase: `docs/prd/` · hợp đồng kho + sự kiện: `docs/contracts/README.md`

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do. Phase 4 thêm module của nhóm `chonoi/bench.py`, `chonoi/soak.py`, `chonoi/leaderboard.py`; sửa nhỏ `contract.py` (v1.3), `runner.py` + `sim/day.py` (`plan_repeat`), `headless.py`/`play.py` (cờ bảng xếp hạng) — tất cả đã có test.
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
- `.agents/skills/rule-check/`: đối chiếu thay đổi luật với PRD/ticket trước khi code (khi nhận ticket mới hoặc change request).
- `.agents/skills/headless-smoke/`: chạy toàn bộ test, smoke hai tiến trình và kiểm tất định trước khi commit hoặc gắn tag.
- `.agents/skills/pause-contract-smoke/`: kiểm pause đóng băng `sim_tick`/`phase_tick`/`time_left_ticks` và resume chạy gameplay ngay cùng bước (`scripts/run_smoke.py`).
