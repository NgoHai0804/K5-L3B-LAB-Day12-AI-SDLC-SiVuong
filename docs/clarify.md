# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | Giỏ không đủ chỗ cho cả `node_yield`/`fish_yield` thì nhận một phần hay bỏ hẳn? | **Chốt:** bỏ hẳn (all-or-nothing) — chỉ phát `hold_full`, nút/cá **không** bị tiêu. Lý do: `_try_hold` của lát 1 so `len(amounts) > free` rồi `extend` cả mảng, không có đường nhận một phần; và `hold_full` không mang số lượng đã nhận nên nhận một phần sẽ không quan sát được từ event. | Đức (PO) + Hải (Integrator) |
| 2 | 2026-11-21 | Ai sở hữu hàm thêm món vào giỏ? `TEAM.md` giao giỏ cho S1 (Hải) nhưng chỉ S2 (Đức) sinh món. | **Chốt:** dùng **một** seam `GatherSim._try_hold(action, item_id, amounts, events)` của lát 1. Lát 2 (hái, bắt cá) **gọi lại**, không tự `self.hold.append`. Đức đã bỏ helper `_try_take` trùng lặp của mình. | Hải (Integrator) |
| 3 | 2026-11-21 | Bắt cá xong đàn cá có mất khỏi bản đồ không? `fish_yield` là số món mỗi lần bắt hay cho cả đàn? | **Giả định:** bắt là lấy cả đàn ⇒ xoá cá khỏi `fish[]`, cho `fish_yield[kind]` món. Lý do: `fish_caught` có `fish_id` nên event gắn với một thực thể cụ thể; P1 cá đứng yên và không sinh thêm, nếu không xoá sẽ thành nguồn nguyên liệu vô hạn. | Đức (PO) |
| 4 | 2026-11-21 | Bắt thất bại vì giỏ đầy thì có vào hồi chiêu `catch_cd_ticks` không? | **Giả định:** không. Hồi chiêu chỉ đặt khi bắt **thành công**, để người chơi không bị phạt vì một cú bấm không có tác dụng. | Đức (PO) |
| 5 | 2026-11-21 | ~~**Xung đột hợp đồng:** §4 đóng băng `hold_full` → `data` = `kind`, nhưng `_try_hold` của lát 1 không có `kind`.~~ | 🔴 **THU HỒI — tiền đề SAI, không có xung đột nào.** Hợp đồng §4 ghi `hold_full` → `action`(`gather`/`catch`), `node_id` **hoặc** `fish_id`, `required`, `free` — **chưa bao giờ** có `kind` (đã kiểm `git show a474352:docs/contracts/README.md`, giống hiện tại). `TEAM.md` §Giỏ cũng ghi y vậy. `_try_hold` của lát 1 **đúng từ đầu**; `kind` là **trường thừa** và §4 đóng băng cả khoá `data` nên thêm khoá chính là vi phạm. Đã hoàn nguyên: bỏ `kind` khỏi `_try_hold`, trả `tests/test_gather_water.py` về `assertEqual` gốc của Hải, sửa 2 test lát 2 sang kiểm đúng 4 khoá. | Đức (PO) — tự nhận sai |
| 6 | 2026-11-21 | Phase 2: "đầu ca 8 đàn ở 8 điểm khác nhau" — sinh bằng seed hay danh sách tường minh? | **Giả định:** khai tường minh `fish_initial` = 8 đàn trong `game.contract.json` (8 điểm khác nhau trong dải loài), không sinh đầu ca bằng RNG. Lý do: giữ tất định, dễ đọc, và khung đã đọc `fish_initial`. Sinh thêm vẫn dùng `Streams` lúc `phase_tick=360k`. | Hải (Integrator) |
| 7 | 2026-11-21 | Phase 2: cá do scenario đặt **ngoài** dải độ sâu (dữ liệu P1, ví dụ `ca_loc` ở `d=5`) thì bơi thế nào? | **Giả định:** mở rộng biên dải để chứa vị trí đầu (không dịch chuyển đột ngột) ⇒ giữ regression P1 xanh. Cá do `fish_initial`/sinh luôn nằm trong dải chuẩn. | Hải (Integrator) |

## Ghi chú #5 — bài học: đọc hợp đồng từ bản ĐANG ở nhánh chính

Mục #5 là một **kết luận sai do đọc hợp đồng ở checkout cũ**. Trình tự đã xảy ra:

1. Đọc `docs/contracts/README.md` ở bản cũ → tưởng §4 quy định `hold_full` → `kind`.
2. Kết luận "lát 1 vi phạm hợp đồng", thêm `kind` vào `_try_hold`.
3. Việc đó làm `tests/test_gather_water.py` của Hải đỏ → lại đi nới assert của Hải cho khớp cái sai.
4. Hải phát hiện "`hold_full` thừa trường `kind`" → kiểm `git show a474352:docs/contracts/README.md`
   thì thấy hợp đồng **luôn** là `action`/`node_id`|`fish_id`/`required`/`free`.

**Rút ra:**
- Trước khi kết luận ai vi phạm hợp đồng, phải `git pull` rồi đọc lại bản **đang ở nhánh chính**, không đọc bản trong working copy cũ.
- Test của người khác đỏ là **tín hiệu cần xác minh lại tiền đề của mình**, không phải việc cần nới assert cho qua.
- `assertEqual` toàn payload của Hải thực ra **đúng và nên giữ**: §4 đóng băng khoá `data`, nên khoá lạ *phải* làm test đỏ.
