# Trần Thị Nhài - 2A202603911 (chanhochust) — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm:
  - HUD gather P1 — cảnh báo hết giờ/ngạt/giỏ đầy, đánh dấu món LIFO, 3 scenario kiểm chứng ([f326f9a](https://github.com/NgoHai0804/K5-L3B-LAB-Day12-AI-SDLC/commit/f326f9a)).
  - HUD sáng P2 (chữ ≥18 px, ≤30 s đổi màu, “Hết hơi!”, gợi ý hái/cập bến) và P3 (thanh độ tươi, hàng ươn) trên nhánh `nhai` ([89864d5](https://github.com/NgoHai0804/K5-L3B-LAB-Day12-AI-SDLC/commit/89864d5), [841333b](https://github.com/NgoHai0804/K5-L3B-LAB-Day12-AI-SDLC/commit/841333b))
  - `chonoi/soak.py` — soak **headless** nhiều Ngày trong một tiến trình, mỗi Ngày đi qua gather → quan → shop bằng một **bot tất định** (không dùng đồng hồ hệ thống, không ngẫu nhiên ngoài `Streams`). Kết quả `{days, days_completed, crashes, results, duration_s}`; đạt khi `days_completed == days` và `crashes == 0`. Thêm `plan_repeat` vào `chonoi/runner.py` và `chonoi/sim/day.py` để chạy quá 5 Ngày (kế hoạch lặp modulo), khai `soak_cmd`.
- Tôi đã review: `chonoi/leaderboard.py` để chắc soak **không** ghi vào bảng xếp hạng (đó là file JSON riêng, không phải JSONL).
- AI sai ở đâu và tôi phát hiện thế nào:
  - AI viết cảnh báo “Ngạt!” trong khi Ticket-02 yêu cầu “Hết hơi!” — tôi đối chiếu ticket rồi sửa; AI đặt nhãn vùng độ sâu ra ngoài khung thước — tôi thấy khi chạy thử, nới khung.
  - AI cho rằng `DaySim` chỉ có 5 Ngày nên không thể chạy 10; lệnh `--days 10` không hoàn tất. Tôi thêm `plan_repeat` và cho `plan_today()`/`_open_quan()` lấy `plan[(day-1) % len(plan)]`, rồi kiểm `--days 10` ra 10/10.
- Điều tôi học được: soak chỉ có giá trị khi **tất định và chịu lỗi** — bot phải sống sót và *đếm* lỗi luật thay vì sập, nếu không sẽ không phân biệt được "game lỗi" với "bot đi sai".
