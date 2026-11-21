# chanhochust — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm: `chonoi/soak.py` — soak **headless** nhiều Ngày trong một tiến trình, mỗi Ngày đi qua gather → quan → shop bằng một **bot tất định** (không dùng đồng hồ hệ thống, không ngẫu nhiên ngoài `Streams`). Kết quả `{days, days_completed, crashes, results, duration_s}`; đạt khi `days_completed == days` và `crashes == 0`. Thêm `plan_repeat` vào `chonoi/runner.py` và `chonoi/sim/day.py` để chạy quá 5 Ngày (kế hoạch lặp modulo), khai `soak_cmd`.
- Tôi đã review: `chonoi/leaderboard.py` để chắc soak **không** ghi vào bảng xếp hạng (đó là file JSON riêng, không phải JSONL).
- AI sai ở đâu và tôi phát hiện thế nào: AI cho rằng `DaySim` chỉ có 5 Ngày nên không thể chạy 10; lệnh `--days 10` không hoàn tất. Tôi thêm `plan_repeat` và cho `plan_today()`/`_open_quan()` lấy `plan[(day-1) % len(plan)]`, rồi kiểm `--days 10` ra 10/10.
- Điều tôi học được: soak chỉ có giá trị khi **tất định và chịu lỗi** — bot phải sống sót và *đếm* lỗi luật thay vì sập, nếu không sẽ không phân biệt được "game lỗi" với "bot đi sai".
