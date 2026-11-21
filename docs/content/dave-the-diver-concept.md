# Đề xuất Nội dung & Sáng tạo MR-1 — Cảm hứng *Dave the Diver* (Content Lead: Nguyễn Thanh Tùng)

## 1. Tầm nhìn sáng tạo
*Quán Ăn Chợ Nổi* chia sẻ cùng vòng lặp cốt lõi cực kỳ cuốn hút của ***Dave the Diver***:
- **Buổi sáng (Lặn sông Chín Khúc ↔ Blue Hole)**: Khám phá mặt cắt 2D theo từng tầng độ sâu, canh thanh oxy, săn cá và hái rau mùa nước nổi.
- **Buổi tối (Nhà bè Má Tư ↔ Bancho Sushi)**: Dùng chính nguyên liệu vừa đánh bắt để nấu bếp, bưng ra bàn phục vụ thực khách trước khi họ mất kiên nhẫn, nhận tiền boa và nâng hạng uy tín quán.

## 2. Những gì đã triển khai cho MR-1 (`chonoi/content/dave_theme.py`)
Tất cả nằm hoàn toàn ở tầng **content/client**, **tắt mặc định ở chế độ headless** (`ServiceReviewTracker(enabled=False)`), bảo đảm 100% không làm thay đổi tick, sự kiện, tiền, uy tín hay snapshot của Test Contract v1.0:

1. **Sổ tay Tầng nước & Nguyên liệu (`INGREDIENT_GUIDE`)**: Phân tầng độ sâu (Tầng mặt 0m → Tầng nông 5m → Tầng trung 10m → Tầng sâu 16m) và mẹo săn bắt cho 4 nguyên liệu (`bong_dien_dien`, `bong_sung`, `ca_linh`, `ca_loc`).
2. **Thực đơn nhà bè kiểu Bancho (`DISH_LORE`)**: Mô tả hương vị, ghi chú của Má Tư và vai trò chiến thuật của 3 món ăn (`ca_loc_nuong_trui`, `goi_bong_sung`, `lau_ca_linh_dien_dien`).
3. **Thoại giọng Nam Bộ phản ứng theo sự kiện (`EVENT_DIALOGUES` & `dialogue_for_event`)**: Út Sen, Má Tư và khách chợ nổi đối đáp ngắn gọn khi nổi lửa bếp, món chín, bưng món, khách boa, khách bỏ đi, đóng quán.
4. **Chợ Nổi Review (`ServiceReviewTracker`, cảm hứng từ app *Cooksta*)**: Theo dõi chuỗi phục vụ nhận boa (Tip Streak), điểm yêu thích (`review_likes`) và xếp hạng 1★–5★ (*Quán Mới Mở Bến* → *Huyền Thoại Sông Chín Khúc*) chỉ bằng cách **đọc** dòng event, không ghi ngược vào mô phỏng.

## 3. Đề xuất mở rộng cho Phase 2–4 (khi có ADR mở rộng contract)
- **Sinh vật & nguyên liệu mới**: Cá kèo (`ca_keo`, tầng đáy 18m), kèo nèo (`keo_neo`, tầng mặt) để làm món *Cá kèo kho tộ* & *Lẩu mắm miền Tây*.
- **Mini-game rót nước mía / trà đá** (lấy cảm hứng từ cơ chế rót trà xanh trong Bancho Sushi) cho khách đang chờ để giữ kiên nhẫn.
- **Khách VIP Chợ Nổi** (như thực khách đặc biệt trong Dave the Diver) đặt món đặc sản theo mùa nước nổi.
