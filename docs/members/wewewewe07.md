# wewewewe07 — phản tư cá nhân (Nguyễn Thanh Tùng)

- **Tôi đã làm**:
  - **Phase 1 (Lát 4 + Content Lead)**: Triển khai luật bếp/bưng/phục vụ/boa/thu tiền/hết ca trong `chonoi/sim/quan.py`, bộ test `tests/test_quan_lat4.py`, nội dung sáng tạo MR-1 lấy cảm hứng *Dave the Diver* (`chonoi/content/dave_theme.py`), `CREDITS.md` và `README.md` (commit `778d437`, PR #4).
  - **Phase 2**: Nâng cấp `quan.py` hỗ trợ 2 bếp/4 bàn, 6 món, lịch khách + lọc kế hoạch ngày (`allowed_dishes`), mở rộng cháy món (`burn`), `tests/test_quan_p2.py`, merge sạch với `main` (commit `521ddf7`, `b303a17`).
  - **Phase 3**: Hỗ trợ song song kho cá thể v1.2 + độ tươi chính xác bằng `Fraction`, `spoiled`, thử giữ lại 1 lần, giá theo độ tươi, `CHANGELOG.md`, `tests/test_quan_p3.py` (commit `ca8c112`).
  - **Phase 4**: Viết `chonoi/bench.py`, `chonoi/soak.py`, `chonoi/leaderboard.py`, phụ đề SFX & cảnh báo tương phản cao, `tests/test_phase4.py` và bằng chứng chạy thật.
- **Tôi đã hỗ trợ**: Giữ hook `_maybe_spawn_customer` sạch và chế độ song song v1.0/v1.1/v1.2 trong `quan.py` để Team Tối và Integrator ghép PR không vỡ `main`.
- **AI sai ở đâu và tôi phát hiện thế nào**: Khi chạy `test_smoke_p1.py` trên Windows, lệnh `python3` gặp `WinError 1920`; tôi kiểm tra và viết helper dùng `sys.executable` trong bộ test riêng mà không đụng vào `game.contract.json` đã khóa. Ngoài ra, dùng `Fraction` thay `float` để tránh sai số ở ngưỡng ươn `30` và `floor`.
- **Điều tôi học được**: Khóa hợp đồng kho sớm, viết test kiểm chứng từng điều kiện biên và tách nội dung sáng tạo khỏi lõi headless giúp cả nhóm chạy song song rất mượt.
