# TEAM

**Tên nhóm:** cho-noi-5  **Số người:** 5  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Ngô Ngọc Hải | NgoHai0804 | `sim/day` · `sim/quan` | Integrator (giữ `docs/contracts/`, gắn tag + Release) | sim/gather |
| Bùi Quý Anh | buiquyanh9-ai | `web` · `client/ui` | QA lead | sim/quan |
| Giang Sơn | son309 | `sim/gather` | PO (giữ `docs/clarify.md`, hỏi giảng viên) | client/ui |
| Chấn Hồ | chanhochust | `headless` · `contract` | Scrum/Release | sim/day |
| Tùng | wewewewe07 | `qa` · `docs/proof` | QA phụ · ghi bằng chứng | web/ui |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: nhóm chat Messenger + bảng lab board cho từng phase.
- Khi bất đồng về thiết kế: nói 2 phút; không xong thì Integrator (NgoHai0804) quyết và ghi lý do vào `docs/clarify.md`.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh; người dự phòng ở cột cuối nhận việc.
- Giờ standup giữa phase: 2–3 phút đầu mỗi phase, mỗi người một dòng vào `docs/standup.md`.
- Cách đọc code của nhau: mỗi người đọc lát kế bên; luật/hợp đồng đổi thì mở PR hoặc xem trực tiếp trước khi gộp.
- Cách làm việc với Git: mỗi lát một nhánh ngắn (hoặc push thẳng nhánh chính khi đã xanh test); Integrator giữ quyền gắn tag `phase-1`…`phase-4` và Release `v1.0.0`.

---

## Ghi chú lịch sử (từ nhánh `main` trước khi gộp)

Bản `TEAM.md` cũ trên `main` mô tả kế hoạch 6 người chia 2 team / 4 lát cho Phase 1–3. Nội dung đó **được thay bằng bảng 5 người ở trên để khớp `team_size:5` và contract v1.3**; kế hoạch chi tiết từng phase vẫn còn trong lịch sử git, `docs/prd/` và `docs/plan/phase-3.md`.
