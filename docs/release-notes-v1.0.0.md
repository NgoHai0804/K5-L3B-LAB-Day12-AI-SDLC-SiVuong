# Release Notes — Quán Ăn Chợ Nổi `v1.0.0`

## Điểm nổi bật
- **Vòng lặp Sáng Lặn & Hái — Tối Mở Quán** lấy cảm hứng từ *Dave the Diver* mang bản sắc miền Tây Nam Bộ (Út Sen & nhà bè Má Tư trên sông Chín Khúc).
- **Phase 1–3 lõi đầy đủ**:
  - Buổi sáng (`gather`): bơi có tăng/giảm tốc, oxy/ngạt/ngất, hái rau mọc lại, bắt cá theo đàn, cá bơi/sinh theo seed, cập bến và bàn giao file kho nguyên tử.
  - Buổi tối (`quan`): hỗ trợ 2 bếp / 4 bàn, 6 món ăn & 6 nguyên liệu, lịch khách, lọc kế hoạch ngày (`D1–D5`), ưu tiên tương tác, tính boa, uy tín và đóng ca.
  - Độ tươi & kho cá thể (v1.2): tính chính xác bằng `Fraction` ở ngưỡng 30, phát `spoiled`, tự thử giữ lại 1 lần khi hàng ươn, chốt giá theo độ tươi trung bình.
- **Mở rộng & Sáng tạo (MR-1)**:
  - Cháy món (`burn`), Bảng xếp hạng cục bộ Top 10 (`chonoi/leaderboard.py`), Phụ đề SFX & cảnh báo tương phản cao, Sổ tay tầng nước & *Chợ Nổi Review* (`chonoi/content/dave_theme.py`, tắt mặc định ở headless).
- **Công cụ kiểm chứng phát hành (Phase 4)**:
  - Benchmark 1280×720 (`python3 -m chonoi.bench`), Soak 10 Ngày (`python3 -m chonoi.soak`), 40/40 test tự động xanh.

## Cách chạy từ clone sạch (≤ 3 lệnh, macOS/Linux)
```bash
git clone https://github.com/NgoHai0804/K5-L3B-LAB-Day12-AI-SDLC-SiVuong.git && cd K5-L3B-LAB-Day12-AI-SDLC-SiVuong
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather
```

### Lệnh headless, benchmark & soak
```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 600 --out gather.jsonl
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
```

## Giới hạn đã biết
- Trên Windows, cần dùng `python` thay vì `python3` nếu alias Microsoft Store gây `WinError 1920`.
- Các khóa mở rộng v1.3 (`bench_cmd`, `soak_cmd`, `contract_version: "1.3"`) được giữ đồng bộ khi Integrator gộp nhánh vào `main` trước khi gắn tag `phase-4` và `v1.0.0`.
