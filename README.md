# Quán Ăn Chợ Nổi — bản của nhóm

Game 2D quản lý quán ăn miền Tây. **Sáng** Út Sen lặn sông Chín Khúc hái bông, bắt cá (mặt cắt ngang). **Tối** em nấu và bưng món trên nhà bè của Má Tư (nhìn từ trên xuống). Hai buổi nối nhau bằng **một file kho**. Vòng lặp "ngày lặn, đêm mở quán" lấy cảm hứng từ thể loại diving + restaurant; nhân vật, bối cảnh và đồ họa là bản gốc của lab.

## Chạy (macOS / Linux, chỉ cần Python 3.10+, không cài thêm gì)

> Windows: dùng `python` thay cho `python3` (trên máy này `python3` cũng trỏ về Python 3.12).

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
python3 -m chonoi.play                                   # chiến dịch 5 Ngày, mở http://127.0.0.1:8000/
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v   # toàn bộ test (1 lệnh)
```

Chơi riêng từng buổi: `python3 -m chonoi.live --mode gather --inventory-out kho.json` rồi `python3 -m chonoi.live --mode quan --inventory kho.json`.
Headless (Test Contract): `python3 -m chonoi.headless --mode gather|quan|day --seed 1 --ticks 600 --out out.jsonl [--days 1..5] [--scenario ..] [--inputs ..] [--inventory ..] [--inventory-out ..]`.

### Phase 4 — bench, soak, bảng xếp hạng (Test Contract v1.3)

```bash
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json     # bench có render (5 trường)
python3 -m chonoi.soak  --seed 7  --days 10   --out soak.json        # soak headless 10 Ngày (bot tất định)
python3 -m chonoi.headless --mode day --days 5 --seed 42 --ticks 200000 \
    --leaderboard leaderboard.json --player-name "Út Sen" --out out.jsonl   # ghi bảng xếp hạng khi đủ 5 Ngày chuẩn
python3 -m chonoi.play --export-leaderboard bang-xep-hang.json       # xuất bảng đã sắp ra file
```

- `bench_cmd` / `soak_cmd` khai ở `game.contract.json`; đầu ra `bench.json` có `avg_fps, p1_low_fps, frames, measured_s, load_ms`; `soak.json` có `days, days_completed, crashes, results, duration_s` (đạt khi `days_completed == days` và `crashes == 0`).
- Bảng xếp hạng là **file JSON riêng** (`{"entries":[{name,score,days_completed,seed}]}`), sắp điểm giảm dần, giữ tối đa 10 mục, ghi **một** mục cho mỗi lượt day đủ 5 Ngày chuẩn (không scenario). Thiếu một trong `--leaderboard`/`--player-name` hoặc dùng với mode ≠ `day` → mã thoát 2.

## Điều khiển

| Phím | Sáng (lặn) | Tối (quán) |
|---|---|---|
| WASD / mũi tên | bơi (S = lặn xuống) | đi lại |
| E | hái bông ở mặt nước · cập bến (kết thúc buổi) | nấu ở bếp · bưng món · phục vụ ở bàn |
| Space | bắt đàn cá (khi ở dưới nước) | — |
| Enter / E (lúc hết buổi) | sang buổi tối | ra chợ sắm đồ |
| 1–6 (ở chợ) | mua nâng cấp | |
| N (màn tiêu đề) | chơi mới từ ngày 1 | |
| R / M | chơi lại buổi · tắt/bật tiếng (phụ đề vẫn hiện) | |
| H | bật/tắt **tương phản cao** | bật/tắt **tương phản cao** |

## Luật chính và cách tính điểm

- **Sáng:** oxy 30 s, chỉ giảm khi ở dưới nước (d > 0.5 m) và hồi rất nhanh khi lên mặt nước. Hết oxy thì cứ đủ 60 tick lại mất 1 Máu (có 3 Máu). Hết Máu thì **ngất**: mất cả giỏ, kho rỗng. Giỏ chứa 12 ô. Bông điên điển, bông súng, kèo nèo hái ở mặt nước, mọc lại sau 20 s. Một đàn cá linh cho 3 con, cá lóc 1 con, cá kèo 2 con; hồi chiêu bắt 0.5 s. Cập bến hoặc hết 3 phút thì giỏ được ghi ra file kho (schema **kho cá thể** `{"items":[{id,kind,fresh}]}`).
- **Tối:** khách đầu tiên đến ở tick 120, sau đó mỗi 15 s một khách nếu bàn T1 còn trống. Khách gọi ngẫu nhiên (theo seed) một món nấu được từ kho, và **giữ chỗ** nguyên liệu ngay lúc gọi. Quy trình: nấu ở B1 → bưng → phục vụ trước khi khách hết kiên nhẫn (60 s). Khách ăn 10 s rồi trả tiền. Phục vụ khi khách còn ≥ 50% kiên nhẫn thì được boa `floor(giá × 0.2)` và +0.2 uy tín. Khách bỏ về làm uy tín −0.5. Tất cả số lấy từ `game.contract.json`.
- **Điểm** = `earned + 100 × floor(uy tín)` (tiền tính bằng nghìn đồng).

| Món | Công thức | Nấu | Giá |
|---|---|---|---|
| Cá lóc nướng trui | cá lóc ×1 | 6 s | 60k |
| Gỏi bông súng | bông súng ×2 | 4 s | 40k |
| Lẩu cá linh bông điên điển | cá linh ×3 + bông điên điển ×1 | 10 s | 120k |
| Canh chua cá lóc | cá lóc ×1 + bông điên điển ×1 | 8 s | 90k |
| Cá kèo nướng muối ớt | cá kèo ×2 | 6 s | 70k |
| Lẩu mắm miền Tây | cá linh ×2 + cá kèo ×1 + kèo nèo ×1 + bông điên điển ×1 | 12 s | 200k |

Giá bán theo **độ tươi**: `base_price = floor(giá × trung bình fresh / 100)`; hàng để lâu bị **ươn** (`fresh < 30`, event `spoiled`) và không bán được.

Hợp đồng file kho và danh sách sự kiện: [`docs/contracts/README.md`](docs/contracts/README.md). PRD: [`docs/prd/PRD-0.md`](docs/prd/PRD-0.md).

## Sáng tạo của nhóm

Lõi chạy theo **Test Contract v1.3** (Phase 2 số chuẩn + vòng Ngày, Phase 3 kho cá thể và độ tươi, Phase 4 bench/soak/bảng xếp hạng). Mọi phần dưới đây chỉ nằm ở cửa sổ chơi (`chonoi/play.py`, `chonoi/web/index.html`, `extras` của `GatherSim`). Headless **không** bật chúng, nên tick, sự kiện, tiền, uy tín và snapshot vẫn đúng contract.

- **Mùa nước nổi 5 Ngày** (`python3 -m chonoi.play`): chạy đúng `DaySim` của `--mode day`. Menu (Chơi / Thoát) → DayIntro (Má Tư đọc món và nguyên liệu, tự chuyển sau 4 s) → sáng lặn → EveningIntro (nhập kho, món nấu được) → tối mở quán → DayResult → Shop → Ngày kế → Tổng kết (tổng tiền, điểm, uy tín, món bán chạy). Esc/P tạm dừng bằng `pause` của sim (dừng mọi timer, kể cả Shop). Mỗi Ngày có tên và thoại riêng, mục tiêu 1500k tiền thuốc cho Má Tư. Tiến trình lưu ở ranh giới Ngày (`saves/campaign.json`).
- **Sprint** (giữ Shift khi lặn): bơi ×1.5, oxy dưới nước tốn ×1.5, tiêu thanh **Sức** (đủ khoảng 3 s); hết Sức thì phải hồi tới 30% mới sprint lại. Chỉ bật qua `LiveGame.EXTRAS`; `tests/test_play.py` kiểm headless không có sprint.
- **Đồ nghề ở Shop** (ngoài oxygen/hp lõi): giỏ lưới, chân vịt, vợt, bếp lò, ghế đẩu. Chỉ sửa một bản sao tuning từ Ngày kế và vẫn qua `validate_tuning`.
- **Đồ họa vẽ bằng code ở độ phân giải gốc** (không dùng asset ngoài, không còn lớp pixel): sông nước xanh trong có tia nắng, gợn sáng, hạt lơ lửng, đáy cát/đá/san hô/rong; cá linh, cá lóc, cá kèo có vây, vảy, mắt; Cá Sấu Năm Chèo có vảy lưng, hàm há khi đuổi; Út Sen có bình oxy, kính lặn, ống thở, chân vịt. Buổi tối là **quán dạng quầy bar**: tường gỗ, cửa sổ nhìn ra sông đêm, kệ nguyên liệu (thanh độ tươi), mái lá dừa, đèn lồng, 2 bếp đất, 4 quầy có ghế đẩu, khách ngồi quầy với bong bóng gọi món, phiếu order treo trên thanh ray.
- **HUD**: Máu, Oxy (đỏ nhấp nháy dưới 25%), Sức, đồng hồ (đỏ khi còn ≤ 30 s), độ sâu theo vùng, giỏ theo ô có thanh độ tươi và nhãn "ươn", danh sách Má Tư dặn (đã lấy/cần), "Thủy quái!" + viền tím, "Hết hơi!". Quán: phiếu order có kiên nhẫn, kho theo loại (khả dụng / giữ / ươn / độ tươi tốt nhất), bếp, món trên tay và giá đã chốt, thực đơn hôm nay. Chữ ≥ 16–18 px.
- **Trợ năng & phụ đề (Phase 4):** ba cảnh báo người chơi — sáng "THỦY QUÁI GẦN ĐÂY!", "SẮP HẾT OXY"; tối "KHÁCH SẮP GIẬN!" (khách còn < 25% kiên nhẫn); phím **H** bật **chế độ tương phản cao** (banner đen/viền trắng, giảm hiệu ứng nhấp nháy, có huy hiệu "TƯƠNG PHẢN CAO"); **phụ đề SFX** (`say`/`drawCaptions`) hiện chữ cho mọi tiếng kể cả khi tắt tiếng (M).
- **Bằng chứng lõi vẫn đúng:** `tests/test_rules_p1.py`, `tests/test_smoke_p1.py` (regression, đã chuyển sang kho cá thể), `tests/test_rules_p2p3.py` (độ tươi, giữ lại khi ươn, giá theo tươi, cá bơi/sinh, Cá Sấu, Shop, pause, vòng Ngày, tất định) chạy hộp đen qua headless; `tests/test_play.py` chạy trọn 5 Ngày, Shop, lưu/tải, pause, sprint; `tests/test_phase4.py` kiểm v1.3, bench, soak, bảng xếp hạng và dấu vết trợ năng trong `index.html`.

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
