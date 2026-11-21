# Nguyễn Thanh Tùng ([wewewewe07](https://github.com/wewewewe07)) — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm**:
  - Phase 1 (`778d437`, PR #4 merge `6b7239e`): triển khai luật Lát 4 `chonoi/sim/quan.py` (bếp nấu, bưng, phục vụ, boa, thu tiền, đóng ca), bộ test quán, và `CREDITS.md`/`README.md`.
  - Phase 2 (`521ddf7`): nâng cấp `quan.py` cho 2 bếp/4 bàn, 6 món, lọc `day_plan`.
  - Phase 3–4 (`ca8c112`, `52e6658`, tag `tung-phase-1..4`): triển khai độ tươi v1.2 bằng `Fraction`, thêm `chonoi/bench.py`, `chonoi/soak.py`, `chonoi/leaderboard.py` và đối chiếu kiểm thử trên `main`.
- **Tôi đã hỗ trợ**: giữ hook `_maybe_spawn_customer` sạch và hỗ trợ song song v1.0/v1.1/v1.2 trong `quan.py` để Team Tối và Integrator ghép PR không vỡ `main`.
- **AI sai ở đâu và tôi phát hiện thế nào**: trên Windows lệnh `python3` gặp `WinError 1920`, tôi giữ nguyên `game.contract.json` và dùng `sys.executable` trong test riêng; đồng thời đổi `float` sang `fractions.Fraction` để tránh sai số ở ngưỡng ươn `30` và phép `floor`.
- **Điều tôi học được**: khóa hợp đồng sớm, kiểm chứng biên bằng test tự động và tách sáng tạo khỏi lõi headless giúp cả nhóm tích hợp an toàn.
