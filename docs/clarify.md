# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 04:30 | Fork của nhóm điền `TEAM.md` với handle nào, `team_size` bao nhiêu? | Chốt cuối: **6** thành viên — `NgoHai0804`, `tmduc23`, `buiquyanh9-ai`, `son309`, `chanhochust`, `wewewewe07`; `team_size = 6` (khớp `game.contract.json` và `TEAM.md`). Bảng mẫu trong `tests/test_team_check.py` chuyển sang chuỗi inline để `TEAM.md` thật không bị coi là mẫu. | Integrator (NgoHai0804) |
| 2 | 2026-11-21 04:40 | Contract v1.3 có được đổi gameplay/tuning/kho/JSONL không? | Không. v1.3 chỉ thêm `contract_version`, `bench_cmd`, `soak_cmd`, `extensions`; giữ nguyên v1.2. | PO (son309) |
| 3 | 2026-11-21 04:50 | Bảng xếp hạng ghi khi nào, giữ bao nhiêu mục? | Chỉ lượt `--mode day` đủ **5 Ngày chuẩn**, **không** scenario, `reason:"days_complete"`; sắp điểm giảm dần (hòa ổn định), giữ tối đa **10** mục; tên Unicode khác rỗng. | Integrator (NgoHai0804) |
| 4 | 2026-11-21 05:00 | Phụ đề SFX có cần hiện khi đang tắt tiếng (M) không? | Có — phụ đề là phần nhìn, vẽ độc lập với âm thanh nên vẫn hiện khi tắt tiếng. | QA lead (buiquyanh9-ai) |
| 5 | 2026-11-21 05:10 | Ảnh bằng chứng cảnh báo chế độ thường lấy sao? | Cửa sổ cảnh báo ngắn nên khó chụp live; nhóm bơm snapshot để chụp. Ảnh chế độ thường chưa chốt nội dung — ghi trung thực ở `docs/verification/phase-4.md` (AC-P4-06). | QA (wewewewe07) |
