# Credits

## Ý tưởng & Nội dung gốc
- **Bối cảnh & nhân vật gốc**: Út Sen, Má Tư, Chợ Nổi Rạch Sen, Sông Chín Khúc — thuộc đề bài Day 12 AI SDLC (*Quán Ăn Chợ Nổi*).
- **Cảm hứng thiết kế (MR-1)**: Lấy cảm hứng từ vòng lặp *lặn biển ban ngày — mở quán ban đêm* và tính năng đánh giá quán kiểu *Cooksta* trong **Dave the Diver** (MINTROCKET), chuyển thể hoàn toàn sang văn hóa sông nước miền Tây Nam Bộ (không sử dụng bất kỳ hình ảnh, âm thanh hay tài sản bản quyền nào từ trò chơi gốc).
- **Nội dung văn bản, sổ tay sinh vật/món ăn & lời thoại Nam Bộ**: Tự sáng tác bởi Nguyễn Thanh Tùng (Content Lead) trong `chonoi/content/dave_theme.py` và `docs/content/dave-the-diver-concept.md` (giấy phép MIT theo repo dự án).

## Asset ngoài
- Hiện tại Phase 1 sử dụng đồ họa hình khối 2D vẽ bằng HTML5 Canvas trong `chonoi/web/index.html` (tự tạo / khung starter), chưa dùng asset ảnh hoặc âm thanh từ bên thứ ba.
- Khi bổ sung sprite/âm thanh ở các phase sau, chỉ dùng nguồn **CC0 / CC-BY / MIT** hoặc tự vẽ và cập nhật đầy đủ tên tác giả, đường dẫn, giấy phép tại mục này.

## Công cụ AI đã dùng
- **Antigravity (Google DeepMind)** — hỗ trợ triển khai luật Lát 4 (`chonoi/sim/quan.py`), bộ test tự động (`tests/test_quan_lat4.py`), nội dung sáng tạo MR-1 (`chonoi/content/dave_theme.py`) và tài liệu kiểm chứng.
