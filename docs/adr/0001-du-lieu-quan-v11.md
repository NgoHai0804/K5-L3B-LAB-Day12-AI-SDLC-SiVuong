# ADR-0001: Đưa dữ liệu quán v1.1 (bếp/bàn, 6 món, 2 nguyên liệu, kế hoạch ngày) vào contract

- Trạng thái: đề xuất (chờ Integrator Hải + Sơn duyệt PR)
- Ngày, người quyết: Phase 2, Bùi Đình Quý Anh (Lát 3)

## Bối cảnh
TICKET-02 §1.3 và §2 yêu cầu B2, T2–T4, 3 món mới, 2 nguyên liệu mới (`ca_keo`, `keo_neo`) và kế hoạch D1–D5
**dưới dạng dữ liệu**. `chonoi/sim/quan.py` (Tùng) đã đọc động bếp/bàn/menu và nhận `allowed_dishes`, nhưng
`game.contract.json` vẫn là bản v1.0 nên test P2 phải tự dựng tuning v1.1 trong code.

## Các lựa chọn đã cân nhắc
1. Chờ Sơn nâng toàn bộ manifest v1.1 một lần — chặn Lát 3 và Lát 4a đến cuối phase.
2. Chỉ thêm các khóa thuộc Lát 3, không đụng khối gather / monsters / shop / `contract_version`.

## Quyết định
Chọn (2). Thay đổi:
- `game.contract.json`: `tuning.quan.stoves` (B1, B2), `tuning.quan.tables` (T1–T4), `tuning.menu` (6 món), `tuning.day_plan` (D1–D5).
- `chonoi/inventory.py`: `KINDS = KINDS_P1 + ("ca_keo", "keo_neo")`, bên đọc/ghi kho mặc định dùng `KINDS` (giữ `KINDS_P1`).
- `chonoi/scenario.py`: `gather.hold` nhận đủ 6 nguyên liệu (một dòng import).
- `chonoi/contract.py`: kiểm bếp/bàn (id duy nhất, vị trí trong phòng), công thức chỉ dùng nguyên liệu hợp lệ, `day_plan` khớp công thức.
- Mới `chonoi/sim/day_plan.py`: `plan_for_day`, `allowed_dishes`, `compute_ingredients` cho `day` (Tùng) dùng.

## Hệ quả
| Module / file | Ảnh hưởng |
|---|---|
| `quan` chạy riêng | 4 bàn, khách đầu ngồi T1, lượt sau T2…; khách chọn trong 6 món |
| `tests/test_quan_lat3.py` | 3 test đổi theo 4 bàn / 6 món (ghi lý do trong commit) |
| `tests/test_smoke_p1.py`, Lát 4 | không đổi, vẫn xanh |
| Team Sáng | `gather` chưa sinh `ca_keo`/`keo_neo` — việc của Lát 1 (Hải, N5/N6 + cá kèo) |
| `day` (Tùng) | gọi `plan_for_day(tuning, n)` cho event `day_plan`, `QuanSim(..., allowed_dishes=allowed_dishes(tuning, n))` |
