# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # smoke test
python3 -m chonoi.live --mode gather                                # chơi thử trên trình duyệt (tùy chọn)
```

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Sáng tạo của nhóm

- **MR-1 — Cảm hứng *Dave the Diver* phiên bản Chợ Nổi Miền Tây** (Nguyễn Thanh Tùng — Content Lead):
  - **Sổ tay Tầng nước, Thủy quái & Thực đơn 6 món** (`chonoi/content/dave_theme.py`, `docs/content/dave-the-diver-concept.md`): Phân tầng độ sâu sông Chín Khúc cho đủ 6 nguyên liệu Phase 2 (`bong_dien_dien`, `bong_sung`, `keo_neo`, `ca_linh`, `ca_loc`, `ca_keo`), sổ tay 3 sinh vật đặc biệt (`ca_sau`, `ran`, `ca_ho`), thực đơn 6 món kiểu *Bancho Sushi*, lời dặn 5 Ngày (D1–D5), mô tả Shop/Chợ Chú Sáu và hệ thống lời thoại giọng Nam Bộ phản ứng theo từng sự kiện.
  - **Chợ Nổi Review (`ServiceReviewTracker`)**: Lấy cảm hứng từ app *Cooksta* trong *Dave the Diver*, chấm chuỗi phục vụ có boa (Tip Streak), ảnh Cá Hô (`photo`), trừ điểm cháy món (`dish_burnt`) và xếp hạng 1★–5★ chỉ bằng cách đọc dòng event.
  - **Mở rộng Cháy món (`burn`)**: Hỗ trợ `burn_s` trong `chonoi/sim/quan.py` (tắt khi `burn_s: null` trong lõi, hoạt động đúng chuẩn `ready_ticks > 1200` khi bật mở rộng).
  - **Bằng chứng lõi vẫn đúng**: Toàn bộ `chonoi/content/` tách biệt khỏi `chonoi/sim/*` và tắt mặc định ở chế độ headless (`enabled=False`). Kết quả chạy `python -m unittest tests.test_quan_lat4 tests.test_quan_p2 tests.test_python_starter_units tests.test_team_check -v` đạt 28/28 test pass (xem `docs/proof/phase-2/quan-p2.md` và `docs/verification/phase-2.md`).

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
