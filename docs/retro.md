# Retro nhóm

## Phase 2 (nhanh)
- **Điều tốt**: Chia ranh giới file rõ giữa Team Sáng (`gather.py`) và Team Tối (`quan.py`), merge PR vào `main` ít xung đột; regression Phase 1 được giữ xanh khi chuyển sang tuning v1.1.
- **Điều tệ**: Nâng cấp manifest `game.contract.json` lên v1.1 chậm giữa các lát nên Team Tối phải viết fixture v1.1 riêng trước khi ghép.
- **1 hành động cho Phase 3**: Khi đổi schema (v1.2 kho cá thể + độ tươi), hỗ trợ song song hai schema nội bộ và viết bảng phân tích tác động + `CHANGELOG.md` trước khi bật cờ chung để `main` không bao giờ đỏ.

## Phase 4 (cuối)
- **Rà lại hành động Phase 2**: Đã thực hiện tốt ở Phase 3 — `chonoi/sim/quan.py` hỗ trợ song song v1.0/v1.1 và v1.2, có bảng tác động ở `docs/verification/phase-3.md` và ghi breaking change ở `CHANGELOG.md`, nhờ đó regression P1–P3 đều xanh 40/40 test.
- **Điều tốt / điều tệ**:
  - *Tốt*: Mỗi người có nhánh và commit riêng rõ ràng; bộ test tự động bao phủ từ P1→P4; nội dung sáng tạo MR-1 cảm hứng *Dave the Diver* tách khỏi lõi headless hoàn toàn.
  - *Cần cải thiện*: Khác biệt môi trường Windows (`python3` alias `WinError 1920`) so với Linux/CI làm việc chạy `test_smoke_p1.py` cục bộ mất thêm thời gian chẩn đoán.
- **Một lần AI sai và cách nhóm phát hiện**:
  - AI từng gợi ý hard-code hằng số (`1200`, `30` tick) ở Lát 2 và dùng số thực `float` cho ngưỡng độ tươi `30` (dễ lệch `29.999999999999996` khi tính `floor`). Nhóm phát hiện khi đối chiếu `AGENTS.md` và test biên ngưỡng `30 → < 30`, chuyển sang đọc từ `tuning` và dùng `fractions.Fraction` chính xác.
- **Nếu làm lại, đổi gì**: Chốt manifest nâng cấp (`game.contract.json`) ngay trong 5 phút đầu mỗi phase để cả hai team cùng chạy trên một bộ số chuẩn sớm hơn.
