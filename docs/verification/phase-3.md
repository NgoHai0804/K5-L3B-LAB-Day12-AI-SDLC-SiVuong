# Ma trận truy vết Phase 3 (contract v1.2 · TICKET-03)

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-3/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P3-01 | Kho cá thể + chọn schema theo `contract_version`; v1.2 từ chối kho đếm — `test_gather_freshness.py::InventoryAdapter` | [`lat1-verification.md`](../proof/phase-3/lat1-verification.md) | Đạt (adapter); **chưa bật v1.2** |
| AC-P3-02 | Hao tươi giỏ −2 đv/tick, `spoiled` theo id, LIFO, bàn giao cá thể — `::GatherFreshness` | [`lat1-verification.md`](../proof/phase-3/lat1-verification.md) | Đạt (unit); smoke file chờ bật v1.2 |
| AC-P3-03..04 | Quán: hao tươi kho, giữ theo id, giá theo tươi (Quý Anh/Tùng) | — | Chưa (chờ) |
| AC-P3-05 | HUD độ tươi/ươn (Nhài/Sơn) | — | Chưa (chờ) |
| AC-P3-06 | Manifest v1.2 + scenario + JSONL (Sơn/Hải) | [`lat1-verification.md`](../proof/phase-3/lat1-verification.md) | Một phần (freshness + adapter); `jsonl.py`/scenario chờ |
| AC-P3-07 | Migration + regression P1–P2 | — | Chưa (chờ bật v1.2) |
| AC-P3-EX-01..02 | `current` · `reservations` (Tùng/Quý Anh) | — | Chưa |

## Thay đổi test / fixture (có lý do)
- Chưa đổi fixture P1–P2 (giữ v1.1 để main xanh). **Khi bật v1.2** sẽ thay `{kind:int}` bằng mảng `[{id,kind,fresh}]` và ghi lý do ở đây.

## Đánh giá ngắn
- Đạt: **Lát 0 adapter** + **Lát 1 Lặn** (Hải) ở mức unit; suite **137/137 xanh**; headless v1.1 không đổi.
- Chưa: Quán/HUD/`day`/mở rộng; **bật v1.2 + regression + tag**.
- Cần chỉnh: chốt thứ tự bật v1.2 với Sơn; cập nhật `jsonl.py` snapshot sang cá thể.
