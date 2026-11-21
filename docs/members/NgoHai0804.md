# NgoHai0804 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm: giữ hợp đồng và phần tích hợp xuyên phase. Phase 4: `chonoi/leaderboard.py`, cổng ghi trong `chonoi/headless.py` (`--leaderboard`/`--player-name`), cập nhật `game.contract.json` lên v1.3 (`bench_cmd`, `soak_cmd`, `extensions`) và `chonoi/contract.py` (`SUPPORTED_VERSIONS`). Điền/gắn tag `phase-4` và chuẩn bị Release `v1.0.0`.
- Tôi đã review: `chonoi/bench.py`, `chonoi/soak.py` của Sơn/Nhài; đối chiếu `tests/test_phase4.py` với điều kiện ghi bảng xếp hạng trước khi gộp.
- AI sai ở đâu và tôi phát hiện thế nào: AI định ghi bảng xếp hạng cho **mọi** lượt `--mode day`; tôi soát lại yêu cầu và chặn bằng điều kiện đủ 5 Ngày chuẩn, không scenario, `reason == "days_complete"`, rồi thêm test cho cả trường hợp bị loại (chạy 1 Ngày / có scenario đều không ghi).
- Điều tôi học được: một mở rộng "nhìn nhỏ" như bảng xếp hạng vẫn cần điều kiện biên rõ ràng (khi nào ghi, giữ bao nhiêu, tên hợp lệ) và test cho các trường hợp **không** ghi mới là phần khó.
