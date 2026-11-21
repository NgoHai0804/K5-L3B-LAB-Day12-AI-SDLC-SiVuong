# buiquyanh9-ai — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm: phần nhìn và khả năng tiếp cận ở cửa sổ chơi. Phase 4 trong `chonoi/web/index.html`: ba cảnh báo người chơi (sáng "THỦY QUÁI GẦN ĐÂY!", "SẮP HẾT OXY"; tối "KHÁCH SẮP GIẬN!"), **chế độ tương phản cao** (phím H → banner đen/viền trắng, huy hiệu "TƯƠNG PHẢN CAO · H"), và **phụ đề SFX** (`CAPS`/`say`/`drawCaptions`) hiện cả khi tắt tiếng.
- Tôi đã review: `chonoi/leaderboard.py` (định dạng store JSON) và phần hiển thị điểm; đọc test `tests/test_phase4.py::FrontendMarkers`.
- AI sai ở đâu và tôi phát hiện thế nào: AI viết nhãn khách bằng ghép chuỗi `("KHÁCH") + " SẮP GIẬN!"` nên test dò chuỗi nguyên văn `"KHÁCH SẮP GIẬN"` thất bại. Tôi nhận ra nhãn bị tách trong mã nguồn và thống nhất sửa **test** cho khớp thực tế (`"KHÁCH"` + `"SẮP GIẬN!"`), thay vì ép lại chuỗi hiển thị.
- Điều tôi học được: phụ đề và tương phản cao là hai đường độc lập với âm thanh/màu — tách phần "nhìn" ra khỏi phần "tiếng" giúp việc kiểm thử và trải nghiệm đều rõ hơn.
