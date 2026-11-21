# Kế hoạch Phase 2 — Một ngày ở chợ nổi (≤ 1 trang)

> Ticket TICKET-02 · Contract **v1.1** · 55 phút · hạn tag `phase-2` **1:55**. Chi tiết số liệu chuẩn + chia lát: `docs/prd/ticket-02.md`.
> Ghi chú: tên người trong bảng lát là kế hoạch **ban đầu**; bảng thành viên chốt cuối là 6 người, xem `TEAM.md`.

## Mục tiêu
- Thay số Phase 1 bằng **tuning chuẩn v1.1**; thêm **6 nguyên liệu / 6 món** dữ liệu, **cá bơi/sinh**, **Cá Sấu**, **Máu/ngất**, **2 bếp/4 bàn**.
- Chơi trọn **vòng ngày**: `DayIntro → gather → EveningIntro → quan → DayResult → Shop` (hoặc tổng kết sau Ngày 5).
- **Shop** mua `oxygen`/`hp` (hiệu lực Ngày kế); **menu, pause, HUD** sáng/tối; `--mode day --days 1..5`.
- Giữ **regression P1** xanh với số chuẩn và **smoke tích hợp** có bằng chứng.

## Việc / người / phụ thuộc

| Lát | Nội dung | Người | AC | Phụ thuộc |
|---|---|---|---|---|
| 1 | Số chuẩn + cá bơi/sinh (`sim/gather.py`) | Hải | AC-P2-01,02 | P1 gather phải còn xanh; cá kèo cần dữ liệu menu (lát 3) |
| 2 | Cá Sấu + Máu/ngất (`sim/gather.py`) | Đức | AC-P2-03,04 | Dùng chung `faint`/timer Máu với lát 1 → pair với Hải |
| 3 | 2 bếp/4 bàn + 6 món + kế hoạch ngày (`sim/quan.py`, dữ liệu) | Quý Anh | AC-P2-05..07 | Cần fixture kho để QA sớm |
| 4 | `day` + Shop (`sim/day.py`) | Tùng | AC-P2-08,09 | Cần hợp đồng kho in-memory + số chuẩn (lát 1) |
| 4 | Contract v1.1 + pause + HUD quán (`game.contract.json`, `headless.py`, `ui`) | Sơn | AC-P2-10..12 | Chốt manifest trước khi các lát đọc cờ nút |
| QA | HUD sáng + QA + smoke + mốc | Nhài | AC-P2-11,13 | Fixture cố định để tích hợp sớm |
| Mở rộng | weapon/net/snake/burn/vendor/ca_ho/settings (≥2 mục) | Tùng/Sơn/Nhài | AC-P2-EX-01..07 | **Sau khi lõi đúng**; tắt ở headless |

- Hợp đồng mới cần chốt sớm: **event vỏ mode `day` có thêm `day`**, snapshot `day/day_plan/upgrades/active_upgrades/paused`, `random_fish`, scenario khối `day`, `--days`.
- Điểm giao duy nhất Sáng↔Tối vẫn là **file kho** (§G); trong `day`, bàn giao kho **trong bộ nhớ**.

## Bằng chứng bắt buộc
- Smoke tích hợp `gather --inventory-out → quan --inventory` → `docs/proof/phase-2/` (đối chiếu `stock` tick 0).
- `day --days 1` và nhiều Ngày (kiểm cấp `oxygen`/`hp` áp từ Ngày kế) → `docs/proof/phase-2/`.
- Regression P1 với số chuẩn (ghi lý do nếu test đổi).
- `docs/verification/phase-2.md` (ma trận AC → cách kiểm → bằng chứng → kết quả), khớp **commit gắn tag**.

## Rủi ro
- **Đổi số chuẩn phá P1**: chạy regression ngay sau khi cập nhật tuning v1.1.
- **Manifest v1.1 đổi chậm** → các lát đọc cờ/nút bị trễ; chốt `game.contract.json` + `docs/contracts/` ở phút 5–20.
- **`faint` dùng chung** ở lát 1 và 2 (ngạt vs monster) → pair và thống nhất `cause`.
- **Đồng hồ `day` ≤ 22.200 tick** có thể vượt 20 s headless → đo sớm, tránh vòng lặp nặng.
- Nhóm trễ tiến độ → người dự phòng (Hải↔Đức, Quý Anh↔Tùng) nhận việc, ưu tiên lõi trước mở rộng.
