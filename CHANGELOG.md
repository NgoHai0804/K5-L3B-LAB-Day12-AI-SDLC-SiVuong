# Changelog
## Unreleased

### Contract v1.2 (Phase 3 — "Mùa Nước Nổi") — BREAKING
- Kho đếm `{"items": {kind: n}}` → kho cá thể `{"items": [{"id", "kind", "fresh"}]}`. File kho đếm hoặc sai schema/kind lạ/id trùng/fresh ngoài [0,100] → mã 2.
- `gather.hold`, `quan.stock` là mảng cá thể; `customers[].reserved` là mảng id cá thể; `lost`, `cook_started.items`, `gather_end.inventory` theo cùng schema.
- Độ tươi: giỏ −0.5/s, kho quán −0.25/s, ươn khi < 30 (event `spoiled`); giữ chỗ theo id tươi nhất; phần giữ vừa ươn thì nhả và giữ lại một lần, thiếu → `unfulfillable`; `base_price = floor(giá × trung bình fresh / 100)`.
- Cập nhật fixture: đổi `["ca_loc", ...]` thành `[{"id": "I1", "kind": "ca_loc", "fresh": 100}, ...]`; `reserved: {"ca_loc": 1}` thành `reserved: ["I1"]`.

### Contract v1.1 (Phase 2 — "Một ngày ở chợ nổi")
- Số chuẩn, 6 nguyên liệu / 6 món, 2 bếp / 4 bàn, cá bơi và sinh theo lịch (`fish_spawned`), Cá Sấu Năm Chèo (`monster_hit`, bất tử, recoil, ngất do quái), `--mode day --days N` (DaySim: gather → quan → shop, `day_plan`, `bought` / `buy_failed`, `shop_end`), `pause` / `resumed`, `sim_tick` tách tick ngoài.
- Test P1 đổi có lý do (ghi đầu `tests/test_rules_p1.py`): schema kho mới, giá chốt theo độ tươi, `fish_initial` là số đàn, cá fixture dùng `random_fish:false` vì cá bơi.
