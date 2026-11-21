# tmduc23 — phản tư cá nhân (≤ 200 từ)

**Trần Minh Đức** · Team Sáng (`gather`) · lát S2 + vai PO

- **Tôi đã làm** (kèm link commit): lát 2 buổi sáng (AC-P1-05..08) trong `chonoi/sim/gather.py` — hái nút `ready` gần nhất ở mặt nước (tie-break id nhỏ, `regrow_s` → `node_regrown`), bắt đàn cá dưới nước theo `fish_yield` + hồi chiêu `catch_cooldown_s`, và hợp đồng file kho. Viết `tests/test_gather_s2.py` (27 test) + bằng chứng chạy thật `docs/proof/phase-1/`. Vai PO: chốt 5 mục trong `docs/clarify.md`. — commit `<sha1>` hái · `<sha2>` bắt cá · `<sha3>` kho + bằng chứng.

- **Tôi đã review** (kèm link): lát 1 của Hải (`_water`, `_try_hold`) — `<link PR của Hải>`.

- **AI sai ở đâu và tôi phát hiện thế nào:** AI tự sinh helper `_try_take()` riêng cho giỏ dù lát 1 đã có seam `_try_hold()`; tôi phát hiện khi đọc `docs/verification/phase-1.md` ("nối `_try_hold()` vào hái/catch") nên xoá bản trùng và gọi lại seam của Hải. AI còn gợi ý hard-code `1200`/`30` tick thay vì đọc `regrow_s`/`catch_cooldown_s` từ contract, và đặt hồi chiêu cả khi bắt thất bại vì giỏ đầy.

- **Điều tôi học được:** phải `git pull` rồi đọc hợp đồng ở **bản đang nằm trên nhánh chính**. Tôi đọc `docs/contracts/README.md` ở checkout cũ, tưởng §4 buộc `hold_full` có `kind`, nên thêm trường thừa vào `_try_hold` rồi còn nới `assertEqual` của Hải cho khớp cái sai đó. Hải phát hiện; `git show a474352:docs/contracts/README.md` chứng minh hợp đồng luôn là `action`/`node_id`|`fish_id`/`required`/`free`. Đã hoàn nguyên hết. Bài học thật: **test của người khác đỏ là tín hiệu kiểm lại tiền đề của mình**, không phải thứ cần nới cho qua — `assertEqual` toàn payload của Hải đúng và nên giữ, vì §4 đóng băng khoá `data` thì khoá lạ *phải* làm test đỏ.
