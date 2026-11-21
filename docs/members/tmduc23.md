# tmduc23 — phản tư cá nhân (≤ 200 từ)

**Trần Minh Đức** · Team Sáng (`gather`) · lát 2 + vai PO

- **Tôi đã làm** (kèm link commit): lát 2 buổi sáng (AC-P1-05..08) trong `chonoi/sim/gather.py` — hái nút `ready` gần nhất ở mặt nước (tie-break id nhỏ, `regrow_s` → `node_regrown`), bắt đàn cá dưới nước theo `fish_yield` + hồi chiêu `catch_cooldown_s`, và hợp đồng file kho. Test hộp đen cho lát 2 nằm trong `tests/test_rules_p1.py::Harvest`/`::Catch` và `tests/test_smoke_p1.py::Integration`; bằng chứng chạy thật để ở `docs/proof/phase-1/`. Vai PO: chốt các mục trong `docs/clarify.md`. — commit `c7a25c6` (hái/bắt cá + bằng chứng) · `46f0536` (nới assert theo hợp đồng §4, điền handle).
- **Tôi đã review** (kèm link): lát 1 của Hải (`_move`, seam `_try_hold`) — đọc trực tiếp trước khi gộp.
- **AI sai ở đâu và tôi phát hiện thế nào:** AI tự sinh helper `_try_take()` riêng cho giỏ dù lát 1 đã có seam `_try_hold()`; tôi phát hiện khi đọc ma trận phase 1 nên xoá bản trùng và nối lại vào seam của Hải. AI còn gợi ý hard-code `1200`/`30` tick thay vì đọc `regrow_s`/`catch_cooldown_s` từ contract, và đặt hồi chiêu cả khi bắt thất bại vì giỏ đầy.
- **Điều tôi học được:** đọc hợp đồng trước khi code. Nhờ đối chiếu §4 mới thấy `hold_full` của lát 1 thiếu khoá `kind`; cũng phát hiện `.gitignore` chặn `*.jsonl` làm link bằng chứng `.jsonl` bị chết.
