# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: chốt sớm hợp đồng file kho (`docs/contracts/`) nên sáng lặn và tối mở quán nối được ngay; fixture cố định (`random_fish:false`) giúp ghép lát `day` sớm.
- Điều tệ: vài số chuẩn bị hard-code trong luật lúc đầu, phải gom về `game.contract.json` sau khi review chéo.
- 1 hành động cho Phase 3: mọi số chỉ đọc từ contract/dữ liệu; thêm test tất định trước khi gộp.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: **đã làm** — luật Phase 3 (kho cá thể, độ tươi) và Phase 4 (bench/soak/leaderboard) đều đọc `game.contract.json`; `tests/test_rules_p2p3.py` và `tests/test_phase4.py` kiểm tất định.
- Điều tốt: mở rộng Phase 4 (bench render, soak 10 Ngày, bảng xếp hạng, cảnh báo + phụ đề) đều **tắt/không đổi ở headless** — lõi vẫn khớp contract; mỗi phần có test hộp đen chạy qua `bench_cmd`/`soak_cmd`/`headless_cmd`.
- Điều tệ: bằng chứng ảnh (cảnh báo người chơi) khó chụp vì cửa sổ cảnh báo ngắn; phải chèn snapshot để chụp, chưa chốt được ảnh chế độ thường.
- Số liệu (đếm `git shortlog -sne --no-merges main`, gộp theo email): NgoHai0804 21 · buiquyanh9-ai 13 · son309 5 · chanhochust 4 · wewewewe07 4 · tmduc23 3 — cả 6 người trong `TEAM.md` đều ≥ 3 commit có nội dung. 9 commit tác giả "Hai Duong" là lịch sử starter kế thừa từ repo gốc (không phải thành viên nhóm). Test tự động: 116 → 122 sau khi gộp bản chơi cuối; soak 10/10 Ngày, `crashes=0`; bench `avg_fps≈404.7` (`docs/proof/phase-4/bench.json`). Token ước tính theo người ở `docs/ai-usage-log.md`; cách đọc code của nhau: mỗi lát đọc lát kế bên + review trực tiếp trước khi gộp.
- Một lần AI sai và cách nhóm phát hiện: AI viết phụ đề bằng chuỗi tách rời nên `"KHÁCH SẮP GIẬN"` không xuất hiện nguyên văn trong `index.html`; test dò chuỗi bắt được và nhóm sửa test cho đúng thực tế (`"KHÁCH"` + `"SẮP GIẬN!"`).
- Nếu làm lại, đổi gì: làm sớm một "smoke cảnh báo" bằng cách bơm snapshot như Phase 4 đã dùng, để ảnh bằng chứng ổn định hơn; và tự động tạo Release trên CI thay vì làm tay.
