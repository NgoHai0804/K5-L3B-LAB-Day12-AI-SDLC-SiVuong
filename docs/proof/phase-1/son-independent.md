# Bằng chứng phần độc lập của Sơn — Phase 1

- Ngày kiểm tra: 2026-11-21
- Branch: `son`
- Commit HUD: `47c7dae`
- Commit skills/harness: `7b21933`

## Phạm vi

- HUD quán đọc snapshot và hiển thị kho, món gọi, kiên nhẫn, bếp, món trên tay, tiền, thu nhập ca, uy tín và điểm.
- HUD bỏ qua an toàn các danh sách hoặc vị trí chưa có trong snapshot.
- Hai skill nhóm: `inventory-handoff-smoke` và `verify-phase-change`.

## Kết quả kiểm chứng

### Smoke bàn giao kho

```powershell
python .agents\skills\inventory-handoff-smoke\scripts\run_smoke.py
```

Kết quả: **PASS**.

```text
PASS inventory handoff: gather -> catch.json -> quan stock
{"bong_sung":2,"ca_loc":1}
```

### Cú pháp HUD

Đã trích nội dung `<script>` của `chonoi/web/index.html` và chạy `node --check -`.

Kết quả: **PASS**, mã thoát 0.

### Toàn bộ test

Lệnh chuẩn dùng `python3` chạy được 12 test trực tiếp nhưng 20 test gọi tiến trình con bị `WinError 1920` vì Windows App Execution Alias của `python3.exe` không truy cập được. Không sửa `game.contract.json` hoặc test.

Chạy lại đúng cùng test suite, chỉ override tạm `tests.helpers.headless_cmd` thành `[sys.executable, '-m', 'chonoi.headless']`:

```text
Ran 32 tests in 44.369s
OK
```

### Giới hạn còn lại

- Công cụ xem trình duyệt báo `browser access host is unavailable`, vì vậy chưa ghi nhận ảnh/clip HUD trong lần kiểm tra này.
- `quick_validate.py` của skill-creator chưa chạy được vì Python hệ thống thiếu `PyYAML`; hai skill đã được kiểm tra thủ công về frontmatter/cấu trúc, script smoke được biên dịch và chạy thành công.
- Smoke kho độc lập đã PASS; chơi quán đầy đủ vẫn phụ thuộc luật Lát 3/Lát 4 được merge vào `main`.
