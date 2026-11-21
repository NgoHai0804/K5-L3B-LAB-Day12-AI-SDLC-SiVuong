# Changelog
## Unreleased

### Breaking (Phase 3 · TICKET-03 · contract v1.2)
- **Kho đếm theo loại → kho cá thể**: file kho và `hold`/`stock` giờ là `{"items":[{id,kind,fresh}]}` (mảng cá thể). Kho rỗng `{"items":[]}`.
- Bên đọc **chọn schema theo `contract_version`**; ở **v1.2**, file kho đếm trả **mã 2**.
- `gather.hold`, `quan.stock`, `customers[].reserved`, `cook_started.data.items`, `lost` (monster_hit/faint) đổi sang **cá thể/id**; thêm event **`spoiled`**.
- Cách cập nhật fixture: thay `{kind:int}` bằng mảng `[{id,kind,fresh}]`; id `I1,I2,…` cấp theo thứ tự vào giỏ, tăng xuyên pha/Ngày.

### Added (Phase 3)
- `freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`; giá theo tươi (`base_price = floor(giá × fresh trung bình / 100)`).
- Mở rộng (nếu bật): dòng nước lũ (`current`), khách đặt trước (`reservations`).

### Docs (Phase 3)
- ADR `docs/adr/0002-kho-ca-the-do-tuoi.md` (quyết định đổi schema + thứ tự tích hợp).
- `docs/plan/phase-3.md`, mục "Phase 3" trong `TEAM.md`.

## Phase 2 (TICKET-02 · contract v1.1)
- Tuning v1.1: cá bơi/sinh, `ca_keo`/`keo_neo`, nút N5/N6, 6 món, kế hoạch D1–D5, Shop `oxygen`/`hp`, vòng ngày `--mode day`.
