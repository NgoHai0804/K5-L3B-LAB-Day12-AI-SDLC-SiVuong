# Kế hoạch Phase 1 (≤ 1 trang)

> PRD-0 · Contract **v1.0** (sau này lên v1.3) · 60 phút · hạn tag `phase-1` **1:00**. Chi tiết chia lát: `TEAM.md`, `docs/prd/PRD-0.md` mục 6.2.

## Mục tiêu
- Dựng repo chung: `TEAM.md`, `team_size` khớp, `check_team.py` báo `OK`.
- Chốt hợp đồng tích hợp: schema file kho (§G) + danh sách sự kiện/giao diện sim↔UI (`docs/contracts/`).
- Làm lõi **gather** (bơi/oxy/ngạt/giỏ, hái/bắt cá/cập bến) và **quan** (khách/bếp/phục vụ/tiền/uy tín).
- Ghi bằng chứng, ma trận truy vết, gắn tag `phase-1` trên commit chạy được.

## Việc / người / phụ thuộc (link issue)
| Lát | Nội dung | Người | AC | Phụ thuộc |
|---|---|---|---|---|
| 1 | Bơi/ramp/biên/oxy/ngạt/giỏ LIFO (`sim/gather.py`) | Hải | AC-P1-01..04 | — |
| 2 | Hái/bắt cá/cập bến/ghi kho (`sim/gather.py`) | Đức | AC-P1-05..07 | seam `_try_hold` lát 1 |
| 3 | Khách/giữ chỗ/kiên nhẫn (`sim/quan.py`) | Quý Anh | AC-P1-08 | file kho mẫu |
| 4 | Bếp/bưng/phục vụ/tiền (`sim/quan.py`) | Tùng | AC-P1-09 | lát 3 |
| QA | HUD tối thiểu + smoke hai tiến trình + mốc | Nhài | AC-P1-10 | fixture cố định |

- **Chốt sớm (phút 0–15):** schema kho + danh sách sự kiện trong `docs/contracts/`; dùng kho mẫu để làm quán song song.

## Bằng chứng bắt buộc
- `python -m unittest discover -s tests -v` xanh (smoke `test_smoke_p1.py`).
- Headless `--mode gather` chạy sạch; cùng `--seed` ⇒ output byte-giống.
- Smoke hai tiến trình `gather --inventory-out → quan --inventory` → `docs/proof/phase-1/`.
- `docs/verification/phase-1.md` (AC → cách kiểm → bằng chứng → kết quả).

## Rủi ro
- Đổi số chuẩn/schema phá P1 → giữ hợp đồng kho, chạy regression sau mỗi thay đổi.
- Trần giỏ vs đàn cá (`hold_full`) dễ lệch giữa 2 lát → pair và thống nhất seam `_try_hold`.
- Tiến độ trễ → người dự phòng nhận việc, ưu tiên lõi trước HUD.
