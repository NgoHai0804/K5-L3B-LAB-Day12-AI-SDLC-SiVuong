# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | Giỏ không đủ chỗ cho cả `node_yield`/`fish_yield` thì nhận một phần hay bỏ hẳn? | **Chốt:** bỏ hẳn (all-or-nothing) — chỉ phát `hold_full`, nút/cá **không** bị tiêu. Lý do: `_try_hold` của lát 1 so `len(amounts) > free` rồi `extend` cả mảng, không có đường nhận một phần; và `hold_full` không mang số lượng đã nhận nên nhận một phần sẽ không quan sát được từ event. | Đức (PO) + Hải (Integrator) |
| 2 | 2026-11-21 | Ai sở hữu hàm thêm món vào giỏ? `TEAM.md` giao giỏ cho S1 (Hải) nhưng chỉ S2 (Đức) sinh món. | **Chốt:** dùng **một** seam `GatherSim._try_hold(action, item_id, amounts, events)` của lát 1. Lát 2 (hái, bắt cá) **gọi lại**, không tự `self.hold.append`. Đức đã bỏ helper `_try_take` trùng lặp của mình. | Hải (Integrator) |
| 3 | 2026-11-21 | Bắt cá xong đàn cá có mất khỏi bản đồ không? `fish_yield` là số món mỗi lần bắt hay cho cả đàn? | **Giả định:** bắt là lấy cả đàn ⇒ xoá cá khỏi `fish[]`, cho `fish_yield[kind]` món. Lý do: `fish_caught` có `fish_id` nên event gắn với một thực thể cụ thể; P1 cá đứng yên và không sinh thêm, nếu không xoá sẽ thành nguồn nguyên liệu vô hạn. | Đức (PO) |
| 4 | 2026-11-21 | Bắt thất bại vì giỏ đầy thì có vào hồi chiêu `catch_cd_ticks` không? | **Giả định:** không. Hồi chiêu chỉ đặt khi bắt **thành công**, để người chơi không bị phạt vì một cú bấm không có tác dụng. | Đức (PO) |
| 5 | 2026-11-21 | **Xung đột hợp đồng:** `docs/contracts/README.md` §4 đóng băng `hold_full` → `data` = `kind`, nhưng `_try_hold` của lát 1 phát `action`/`node_id`/`required`/`free` và **không có `kind`**. | **Chốt theo hợp đồng:** `hold_full` **phải** có `kind` (§4 là nguồn sự thật, test ẩn bám theo nó). Đức thêm `kind` vào payload và **giữ nguyên** các khoá chẩn đoán của lát 1 (§2: bên đọc bỏ qua trường chưa biết). **Hệ quả:** `tests/test_gather_water.py:136` dùng `assertEqual` chính xác nên đỏ — **Hải cần nới assert** (xem ghi chú dưới bảng). Không mở ADR vì đây là sửa cho **khớp** hợp đồng, không phải đổi hợp đồng. | Đức (PO), Hải xác nhận |

## Ghi chú #5 — việc Hải cần làm (1 dòng)

`tests/test_gather_water.py:136` đang khoá cứng payload cũ. Sửa thành so theo tập con để không vỡ khi thêm khoá:

```python
    def test_06_try_hold_reports_full_with_free_and_required(self):
        cap = load_contract()["tuning"]["gather"]["hold_capacity"]
        sim = self._sim(["ca_loc"] * cap)
        ev = []
        self.assertFalse(sim._try_hold("gather", "N3", ["bong_sung"], ev))
        self.assertEqual(len(ev), 1)
        name, data = ev[0]
        self.assertEqual(name, "hold_full")
        self.assertEqual(data["kind"], "bong_sung")          # hợp đồng §4
        self.assertEqual(data["action"], "gather")
        self.assertEqual(data["node_id"], "N3")
        self.assertEqual((data["required"], data["free"]), (1, 0))
```
