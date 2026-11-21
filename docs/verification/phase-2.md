# Ma trận truy vết Phase 2 (Team Tối — `quan` & Content MR-1)

| AC | Nội dung yêu cầu (TICKET-02 / Contract v1.1) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| `AC-P2-Q1` | 2 bếp (`B1 [2,8]`, `B2 [5,8]`), 4 bàn (`T1–T4`), nấu song song đúng thứ tự đơn `reserved` cũ nhất theo `(order_tick, id bàn)` | Unit test `tests/test_quan_p2.py` (`test_two_stoves_cook_in_order_and_lau_mam_price_tip`) | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-Q2` | Đủ 6 món & 6 nguyên liệu chuẩn Phase 2 (`canh_chua_ca_loc`, `ca_keo_nuong`, `lau_mam`, `ca_keo`, `keo_neo`), giá/thời gian nấu/boa `floor(price × 0.2)` | Unit test `tests/test_quan_p2.py` | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-Q3` | Lịch khách `120 + 900·k`, bàn trống id nhỏ nhất (`T1→T4`), lọc menu theo kế hoạch ngày (`allowed_dishes` D1–D5) trước khi lọc kho khả dụng, phát `no_dish` khi thiếu món | Unit test `tests/test_quan_p2.py` (`TestQuanPhase2ScheduleAndDayPlan`) | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-Q4` | Mở rộng Cháy món (`burn_s: 20` -> 1200 tick): đúng 1200 tick vẫn bưng được; `ready_ticks > 1200` phát `dish_burnt`, bếp rảnh, thử giữ lại (`reserved`/`unfulfillable`) | Unit test `tests/test_quan_p2.py` (`TestQuanPhase2BurnExtension`) | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-REG` | Regression Phase 1 (Lát 4: `AC-P1-12..14`, `test_python_starter_units`, `test_team_check`) giữ nguyên 100% pass | Chạy chung bộ test P1 + P2 | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |
| `AC-P2-MR1` | Nội dung sáng tạo cảm hứng *Dave the Diver* (`chonoi/content/dave_theme.py`) phủ đủ 6 nguyên liệu, 6 món, 3 sinh vật, 5 ngày, Shop & Chợ Nổi Review (`photo`/`dish_burnt`), tắt mặc định ở headless | Unit test `tests/test_quan_p2.py` (`TestMR1Phase2DaveContent`) | [quan-p2.md](../proof/phase-2/quan-p2.md) | Đạt |

## Ghi chú tích hợp
- Phần `chonoi/sim/quan.py` đã sẵn sàng cho `contract_version: "1.1"` (đọc động `stoves`, `tables`, `menu`, `burn_s` từ `tuning` và nhận `allowed_dishes` từ chế độ `day`).
- Chưa sửa `game.contract.json` để tránh xung đột với Integrator/Team Sáng khi nâng cấp manifest v1.1 toàn repo.
- Lý do cập nhật 1 assertion ở `tests/test_quan_lat4.py`: `INGREDIENT_GUIDE` và `DISH_LORE` mở rộng từ 4→6 nguyên liệu và 3→6 món theo Phase 2 nên đổi so sánh `assertEqual` thành `issubset` (mọi mục Phase 1 đều được giữ nguyên).
