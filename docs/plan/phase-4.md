# Kế hoạch Phase 4 — Bench + đóng gói + Release v1.0.0 (≤ 1 trang)

> Contract **v1.3** · 30 phút · hạn tag `phase-4` + Release `v1.0.0` **3:00**. Chi tiết: `docs/release/v1.0.0.md`, `docs/verification/phase-4.md`.

## Mục tiêu
- Chạy toàn bộ test + headless cả ba mode (`gather`/`quan`/`day`) xanh; cùng `--seed` ⇒ output byte-giống.
- Hoàn tất **Test Contract v1.3** (tương thích ngược v1.2): `bench_cmd` (bench **có render**), `soak_cmd` (soak **headless nhiều Ngày**), `extensions: ["leaderboard", "subtitles"]`.
- **Bảng xếp hạng cục bộ** (`leaderboard.json`, chỉ ghi khi đủ 5 Ngày chuẩn, không scenario).
- **Cửa sổ chơi**: ba cảnh báo người chơi, chế độ tương phản cao (`H`), phụ đề SFX (hiện cả khi tắt tiếng `M`) — tất cả **tắt ở headless**.
- `CHANGELOG.md` v1.0.0; **tag `phase-4`** + **Release `v1.0.0`**; README mục "Sáng tạo của nhóm"; `CREDITS.md`; retro cuối; 6 phản tư `docs/members/<handle>.md`.

## Việc / người
| Việc | Người | AC | Phụ thuộc |
|---|---|---|---|
| `bench.py` (rasterizer CPU, 5 trường) + `bench_cmd` | son309 | AC-P4-02 | tuning `gather` |
| `soak.py` + `plan_repeat` (`sim/day`, `runner`) | chanhochust | AC-P4-03 | vòng `day` |
| `leaderboard.py` + cổng ghi/`--leaderboard`/`--player-name` trong `headless.py` | NgoHai0804 | AC-P4-04,05 | `day` đủ 5 Ngày |
| Trợ năng: 3 cảnh báo + tương phản cao + phụ đề SFX (`web/index.html`) | buiquyanh9-ai | AC-P4-06,07 | snapshot sáng/tối |
| `tests/test_phase4.py`, proof ảnh `docs/proof/phase-4/`, `TEAM.md` | wewewewe07 | AC-P4-08 | các mục trên |
| Contract v1.3 + tag `phase-4` + Release `v1.0.0` | NgoHai0804 | AC-P4-01,08 | tất cả |
| Gộp bản chơi cuối (extras: drop/early_close/prep/collide, món phụ, nhiệm vụ) — chỉ cửa sổ chơi | buiquyanh9-ai | AC-P4-09 | các mục trên |

## Bằng chứng bắt buộc
- `docs/proof/phase-4/bench.json` (5 trường), `soak.json` (`days_completed == days`, `crashes == 0`), ảnh `warn_*`/`subtitle_soundoff.png`.
- `docs/verification/phase-4.md` (ma trận AC), `docs/release/v1.0.0.md`, `CHANGELOG.md` (bỏ "Unreleased").

## Rủi ro
- **Sáng tạo lọt vào headless**: regression `tests/test_rules_p1.py` / `test_smoke_p1.py` phải còn xanh (tính tất định giữ nguyên).
- **Release phụ thuộc quyền/`gh`**: xác nhận trước 3:00; nếu không tạo được thì ghi trung thực trong bằng chứng (AC-P4-08).
- **Ảnh cảnh báo chế độ thường khó chụp** (cửa sổ ngắn): bơm snapshot để chụp, ghi rõ ở AC-P4-06.
