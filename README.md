# Quán Ăn Chợ Nổi — bản của nhóm

Game 2D quản lý quán ăn miền Tây. **Sáng** Út Sen lặn sông Chín Khúc hái bông, bắt cá (mặt cắt ngang). **Tối** em nấu và bưng món trên nhà bè của Má Tư (nhìn từ trên xuống). Hai buổi nối nhau bằng **một file kho**. Vòng lặp "ngày lặn, đêm mở quán" lấy cảm hứng từ thể loại diving + restaurant; nhân vật, bối cảnh và đồ họa là bản gốc của lab.

## Chạy (macOS / Linux, chỉ cần Python 3.10+, không cài thêm gì)

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
python3 -m chonoi.play                                   # chiến dịch 10 ngày, mở http://127.0.0.1:8000/
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v   # toàn bộ test (1 lệnh)
```

Chơi riêng từng buổi: `python3 -m chonoi.live --mode gather --inventory-out kho.json` rồi `python3 -m chonoi.live --mode quan --inventory kho.json`.
Headless (Test Contract v1.0): `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl [--scenario ..] [--inputs ..] [--inventory ..] [--inventory-out ..]`.

## Điều khiển

| Phím | Sáng (lặn) | Tối (quán) |
|---|---|---|
| WASD / mũi tên | bơi (S = lặn xuống) | đi lại |
| E | hái bông ở mặt nước · cập bến (kết thúc buổi) | nấu ở bếp · bưng món · phục vụ ở bàn |
| Space | bắt đàn cá (khi ở dưới nước) | — |
| Enter / E (lúc hết buổi) | sang buổi tối | ra chợ sắm đồ |
| 1–6 (ở chợ) | mua nâng cấp | |
| N (màn tiêu đề) | chơi mới từ ngày 1 | |
| R / M | chơi lại buổi · tắt/bật tiếng | |

## Luật chính và cách tính điểm

- **Sáng:** oxy 30 s, chỉ giảm khi ở dưới nước (d > 0.5 m) và hồi rất nhanh khi lên mặt nước. Hết oxy thì cứ đủ 60 tick lại mất 1 Máu (có 3 Máu). Hết Máu thì **ngất**: mất cả giỏ, kho rỗng. Giỏ chứa 12 ô. Bông điên điển và bông súng hái ở mặt nước, mọc lại sau 20 s. Một đàn cá linh cho 3 con, một đàn cá lóc cho 1 con, hồi chiêu bắt 0.5 s. Cập bến hoặc hết 3 phút thì giỏ được ghi ra file kho.
- **Tối:** khách đầu tiên đến ở tick 120, sau đó mỗi 15 s một khách nếu bàn T1 còn trống. Khách gọi ngẫu nhiên (theo seed) một món nấu được từ kho, và **giữ chỗ** nguyên liệu ngay lúc gọi. Quy trình: nấu ở B1 → bưng → phục vụ trước khi khách hết kiên nhẫn (60 s). Khách ăn 10 s rồi trả tiền. Phục vụ khi khách còn ≥ 50% kiên nhẫn thì được boa `floor(giá × 0.2)` và +0.2 uy tín. Khách bỏ về làm uy tín −0.5. Tất cả số lấy từ `game.contract.json`.
- **Điểm** = `earned + 100 × floor(uy tín)` (tiền tính bằng nghìn đồng).

| Món | Công thức | Nấu | Giá |
|---|---|---|---|
| Cá lóc nướng trui | cá lóc ×1 | 6 s | 60k |
| Gỏi bông súng | bông súng ×2 | 4 s | 40k |
| Lẩu cá linh bông điên điển | cá linh ×3 + bông điên điển ×1 | 10 s | 120k |

Hợp đồng file kho và danh sách sự kiện: [`docs/contracts/README.md`](docs/contracts/README.md). PRD: [`docs/prd/PRD-0.md`](docs/prd/PRD-0.md).

## Sáng tạo của nhóm

Mọi phần dưới đây chỉ nằm ở cửa sổ chơi (`chonoi/play.py`, `chonoi/web/index.html`). Headless **không** dùng chúng, nên tick, sự kiện, tiền, uy tín và snapshot vẫn đúng contract.

- **Chiến dịch 10 ngày** (`python3 -m chonoi.play`): màn tiêu đề → mỗi ngày gồm buổi sáng lặn, buổi tối mở quán và ghé chợ sắm đồ → kết thúc sau ngày 10. Mục tiêu là đủ 2000k tiền thuốc cho Má Tư, có 3 kết thúc tùy tổng thu và uy tín. Mỗi ngày có tên và thoại riêng.
  - Kho chuyển sang quán qua đúng file kho (`saves/kho.json`, Contract G). Uy tín mang sang ngày sau qua `scenario.quan.reputation`.
  - Mỗi ngày bố trí cá và bông khác nhau (tất định theo seed, vẫn qua kiểm scenario). Khách tới dày hơn và mau sốt ruột hơn.
  - Chợ có 6 nâng cấp, mỗi món 3 cấp: bình oxy, giỏ lưới, chân vịt, vợt, bếp lò, ghế đẩu. Nâng cấp chỉ sửa một bản sao tuning và vẫn phải qua `validate_tuning`.
  - Tiến trình được lưu trong `saves/campaign.json`; mở lại sẽ chơi tiếp được.
- **Đồ họa pixel-art vẽ bằng code, không dùng asset ngoài:** thế giới được vẽ ở 1/3 độ phân giải rồi phóng to không làm mịn, HUD giữ sắc nét. Vùng sâu tối dần và có đèn đội đầu soi đường. Có ghe chợ nổi treo cây bẹo, khạp sành và xuồng chìm dưới đáy. Bình minh chuyển dần sang trưa, nước phù sa có tia nắng, bờ dừa nước và nhà sàn trôi parallax, lục bình trôi, đàn cá lượn. Út Sen mặc áo bà ba, quấn khăn rằn, đeo kính lặn tự chế. Nhà bè buổi tối có đèn dây vàng, đèn lồng, bếp than có khói.
- **HUD đầy đủ:** bình oxy, tim Máu, thước độ sâu, giỏ có icon, gợi ý phím theo ngữ cảnh, cảnh báo đỏ khi sắp hết oxy. Bên quán có phiếu gọi món kèm thanh kiên nhẫn, kho khả dụng / đang giữ, trạng thái bếp, món trên tay, thực đơn, sao uy tín.
- Thoại giọng Nam Bộ của Má Tư, chữ bay, tiền rơi, âm thanh tự tạo bằng WebAudio.
- **Bằng chứng lõi vẫn đúng:** `tests/test_smoke_p1.py` và `tests/test_rules_p1.py` chạy hộp đen qua headless. `tests/test_play.py` chạy đủ 10 ngày, kiểm chợ, lưu/tải, tuning và bố trí từng ngày đều hợp lệ, kho đi qua đúng file kho.

---

# Day 12 — AI SDLC: Quán Ăn Chợ Nổi (đề lab)

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
