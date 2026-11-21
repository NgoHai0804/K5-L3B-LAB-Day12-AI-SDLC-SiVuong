# Kế hoạch Phase 3 — Change Request “Mùa Nước Nổi” (≤ 1 trang)

> Ticket TICKET-03 · Contract **v1.2** · 35 phút · hạn tag `phase-3` **2:30**. Chi tiết số liệu + chia lát: `TEAM.md` · quyết định schema: `docs/adr/0002-kho-ca-the-do-tuoi.md`.
> Ghi chú: tên người trong bảng lát là kế hoạch **ban đầu**; bảng thành viên chốt cuối là 6 người, xem `TEAM.md`.

## Mục tiêu (change request)
- **[THAY THẾ]** Kho đếm theo loại → **kho cá thể** `{"items":[{id,kind,fresh}]}`; id `I1,I2,…` tăng **xuyên pha/Ngày**; LIFO theo thứ tự vào giỏ.
- **Độ tươi**: hàng mới `fresh=100` (hao từ bước sau); giỏ **−0.5/s**, kho quán **−0.25/s** (kể cả hàng giữ chỗ); kẹp 0; **pause dừng hao**; món chín không hao. `fresh<30` = **ươn**, phát `spoiled` **một lần** khi vượt ngưỡng, **theo id**.
- **[THAY THẾ]** Giữ/tiêu theo **id** (tươi nhất, hòa id); giữ chỗ có cá thể vừa ươn ⇒ **nhả toàn bộ phần giữ của đơn + thử giữ lại một lần**.
- **[THAY THẾ]** **Giá theo tươi**: `base_price = floor(giá niêm yết × trung bình fresh dùng / 100)`; boa `floor(tiền món × 0.2)` trên giá đã chốt.
- **HUD** hiển thị độ tươi/ươn. **Bên đọc chọn schema theo `contract_version`**; v1.2 **từ chối kho đếm (mã 2)**.
- **Mở rộng**: dòng nước lũ (`current`) · khách đặt trước (`reservations`) — chọn **sau khi lõi ổn**.

## Việc / người / phụ thuộc

| Lát | Nội dung | Người | AC | Phụ thuộc |
|---|---|---|---|---|
| 0 | Schema/adapter kho cá thể + chọn schema theo version + migration + manifest v1.2 | Sơn, Hải | AC-P3-01,06,07 | **Chốt trước** để Lặn/Quán/HUD chạy song song |
| 1 | Lặn: hao tươi giỏ, `spoiled`, LIFO, bàn giao file/day | Đức, Hải | AC-P3-02 | schema (lát 0) |
| 2 | Quán: hao tươi kho, giữ theo id (nhả + thử lại khi ươn), giá theo tươi | Quý Anh, Tùng | AC-P3-03,04 | schema (lát 0) |
| 3 | HUD độ tươi/ươn (sáng + tối) + tích hợp `day` | Nhài, Sơn, Tùng | AC-P3-05 | schema (lát 0) |
| MR | Dòng nước lũ (`current`) · Khách đặt trước (`reservations`) | Tùng · Quý Anh | AC-P3-EX-01,02 | lõi + bàn giao kho ổn |

- **Thứ tự tích hợp**: schema/adapter + test migration **trước** → Lặn/Quán/HUD **song song** → hỗ trợ **hai phiên bản nội bộ** khi chuyển → **bật v1.2** khi cả hai đầu sẵn sàng (kho đếm ⇒ mã 2).
- Quyết định đổi schema + thứ tự ghi ở **ADR-0002**; ghi breaking change ở **CHANGELOG.md**.

## Bằng chứng bắt buộc
- Fixture ngưỡng: `hold` `fresh:30`, một bước không input ⇒ `spoiled` tick 1 (`I1`, `hold`).
- Smoke **file** (fresh 100 + `interact:true` frame 0) → `quan --inventory --ticks 0`: so **chính xác** id/kind/fresh sau lần hao.
- Smoke `day` bàn giao trong **cùng tick chuyển pha**; kho đếm ⇒ **mã 2**; **regression P1–P2** (ghi lý do nếu test đổi).
- `docs/verification/phase-3.md` (AC → cách kiểm → bằng chứng → kết quả), khớp **commit gắn tag**; `docs/proof/phase-3/`.

## Rủi ro
- **Đổi schema phá P1–P2**: giữ schema sau adapter, bật v1.2 khi cả hai đầu xong; chạy regression ngay.
- **Ngưỡng 30 & `floor`**: sai số làm lệch nhánh ươn — dùng đơn vị tươi nguyên (240/điểm, −2/tick gather, −1/tick quán) và so ngưỡng **trước** làm tròn.
- **Id xuyên pha/Ngày**: dễ trùng/đứt khi bàn giao — một `IdAllocator` chung, id duy nhất giữa các nơi chứa.
- **`reserved` trỏ cá thể**: phải tươi, không dùng chung với đơn khác; sai ⇒ mã 2.
- **Hai hệ (file + day) lệch**: kiểm cả file và `day` trên main trước khi gắn tag.
- Trễ tiến độ: người dự phòng (Hải↔Đức, Quý Anh↔Tùng) nhận việc; ưu tiên lõi trước mở rộng.
