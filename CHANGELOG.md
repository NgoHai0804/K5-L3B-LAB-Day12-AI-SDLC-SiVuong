# Changelog

## v1.0.0 — bổ sung cửa sổ chơi (2026-11-21)
- Sáng tạo (chỉ `chonoi.play`, headless không đổi): thả đồ nhặt nhầm (Q), đóng quán sớm khi vắng (C), minigame sơ chế giảm thời gian nấu, va chạm với bếp/quầy, 6 món phụ, 3 nhiệm vụ phụ mỗi Ngày, thoại khách.
- Gộp hai đường tương phản cao trong `index.html` về một biến `hiC` (phím H, menu tạm dừng, lưu `localStorage`); bong bóng thoại khách đổi tên `custSay` để không đè `say()` của phụ đề SFX.
- Test: `tests/test_play.py` thêm 7 test (thả đồ, đóng sớm, sơ chế, va chạm, món phụ, nhiệm vụ, headless không có extras). Toàn bộ 122 test xanh.

## v1.0.0 — Phase 4 (2026-11-21) 🎉

### Contract v1.3 (Phase 4 — "Bench + đóng gói + Release") — tương thích ngược
- Thêm `bench_cmd` (benchmark **có render**, cảnh sáng `gather`, xuất `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`), `soak_cmd` (soak **headless nhiều Ngày**, bot tất định, `days_completed`/`crashes`), và `extensions: ["leaderboard", "subtitles"]`.
- Phần gameplay/tuning/kho cá thể/JSONL của v1.2 **giữ nguyên**; `contract_version:"1.3"`, vẫn đọc được `"1.2"` (`chonoi/contract.py`).
- **Bảng xếp hạng cục bộ** (`leaderboard.json`, file JSON riêng — không phải JSONL): ghi **một** mục cho lượt `--mode day` đủ **5 Ngày chuẩn**, không scenario, `reason:"days_complete"`; sắp điểm giảm dần (hòa ổn định), giữ tối đa **10** mục, tên Unicode khác rỗng. `headless --leaderboard <file> --player-name <tên>`; xuất bằng `play --export-leaderboard <file>`. Thiếu một trong hai cờ hoặc sai mode → mã 2.
- **Cửa sổ chơi:** ba cảnh báo người chơi (sáng "THỦY QUÁI GẦN ĐÂY!", "SẮP HẾT OXY"; tối "KHÁCH SẮP GIẬN!"), **chế độ tương phản cao** (phím `H`), và **phụ đề SFX** hiện cả khi tắt tiếng (`M`). Tất cả **tắt ở headless** — lõi không đổi.

### Contract v1.2 (Phase 3 — "Mùa Nước Nổi") — BREAKING
- Kho đếm `{"items": {kind: n}}` → kho cá thể `{"items": [{"id", "kind", "fresh"}]}`. File kho đếm hoặc sai schema/kind lạ/id trùng/fresh ngoài [0,100] → mã 2.
- `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là mảng id cá thể; `lost`, `cook_started.items`, `gather_end.inventory` theo cùng schema.
- Độ tươi: giỏ −0.5/s, kho quán −0.25/s, ươn khi < 30 (event `spoiled`); giữ chỗ theo id tươi nhất; phần giữ vừa ươn thì nhả và giữ lại một lần, thiếu → `unfulfillable`; `base_price = floor(giá × trung bình fresh / 100)`.
- Cập nhật fixture: đổi `["ca_loc", ...]` thành `[{"id": "I1", "kind": "ca_loc", "fresh": 100}, ...]`; `reserved: {"ca_loc": 1}` thành `reserved: ["I1"]`.
- ADR `docs/adr/0002-kho-ca-the-do-tuoi.md` (schema kho cá thể + thứ tự tích hợp); `docs/plan/phase-3.md`.

### Contract v1.1 (Phase 2 — "Một ngày ở chợ nổi")
- Số chuẩn, 6 nguyên liệu / 6 món, 2 bếp / 4 bàn, cá bơi và sinh theo lịch (`fish_spawned`), Cá Sấu Năm Chèo (`monster_hit`, bất tử, recoil, ngất do quái), `--mode day --days N` (DaySim: gather → quan → shop, `day_plan`, `bought` / `buy_failed`, `shop_end`), `pause` / `resumed`, `sim_tick` tách tick ngoài.
- ADR `docs/adr/0001-khung-v11-nguyen-lieu-moi.md` (mở rộng tập kind v1.1 `ca_keo`, `keo_neo`).
- Test P1 đổi có lý do (ghi đầu `tests/test_rules_p1.py`): schema kho mới, giá chốt theo độ tươi, `fish_initial` là số đàn, cá fixture dùng `random_fish:false` vì cá bơi.
