# Ma trận truy vết Phase 3 (TICKET-03 · Contract v1.2 → nay v1.3)

> Change request "Mùa Nước Nổi": **kho cá thể + độ tươi** (breaking). Trạng thái cuối: v1.2 đã **bật** và nằm trong v1.3
> (`contract_version:"1.3"`, tương thích ngược v1.2). Quyết định schema: `docs/adr/0002-kho-ca-the-do-tuoi.md`.
> Test hiện hành ở `tests/test_rules_p2p3.py::Freshness` và `tests/test_smoke_p1.py::Integration`.

| AC | Nội dung (TICKET-03 / Contract v1.2) | Cách kiểm chứng (test hiện hành) | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P3-01 | Kho **cá thể** `{"items":[{id,kind,fresh}]}`; chọn schema theo `contract_version`; v1.2 **từ chối kho đếm** / kind lạ / id trùng / fresh ngoài `[0,100]` ⇒ mã 2 | `tests/test_rules_p2p3.py::Freshness::test_bad_item_fixtures_exit_2`; `tests/test_smoke_p1.py::Integration::test_inv_bad_schema_exit_2`; `chonoi/inventory.py` | [`quyanh-upload.txt`](../proof/phase-3/quyanh-upload.txt) | Đạt |
| AC-P3-02 | Hao tươi **giỏ −0.5/s** (−2 đơn vị/tick), `spoiled` **một lần** theo id khi `fresh < 30`, LIFO khi ngất, hàng mới `fresh=100` | `tests/test_rules_p2p3.py::Freshness` (`test_gather_decay_half_per_second`, `test_spoiled_once_and_by_id`, `test_spoiled_on_first_step_from_30`) | [`out-gather.jsonl`](../proof/phase-3/out-gather.jsonl) | Đạt |
| AC-P3-03 | Quán: hao tươi kho **−0.25/s**, giữ/tiêu theo **id tươi nhất** (hòa id), cá thể vừa ươn ⇒ nhả và giữ lại một lần, thiếu ⇒ `unfulfillable` | `tests/test_rules_p2p3.py::Freshness` (`test_quan_decay_quarter_per_second_and_price`, `test_spoiled_stock_not_cooked_and_rereserve`, `test_freshest_reserved_first`, `test_spoiled_not_available_for_customers`) | `tests/test_rules_p2p3.py::Freshness` | Đạt |
| AC-P3-04 | **Giá theo tươi**: `base_price = floor(giá × trung bình fresh / 100)`; boa `floor(base_price × tip_rate)` | `tests/test_rules_p2p3.py::Freshness::test_quan_decay_quarter_per_second_and_price` | `tests/test_rules_p2p3.py::Freshness` | Đạt |
| AC-P3-05 | HUD hiển thị độ tươi/ươn (sáng: thanh độ tươi + nhãn "ươn"; tối: kho theo loại/độ tươi, giá đã chốt) | Dấu vết trong `chonoi/web/index.html`; `tests/test_phase4.py::FrontendMarkers::test_index_html_has_warnings_subtitles_and_high_contrast` | `chonoi/web/index.html` | Đạt |
| AC-P3-06 | Manifest v1.2: khối `tuning.freshness {initial, gather_decay_per_s, quan_decay_per_s, spoiled_below}`; `contract.py` kiểm dải; snapshot `hold`/`stock`/`reserved`/`items` là **cá thể** | `tests/test_phase4.py::ContractV13::test_v12_gameplay_kept`; `chonoi/contract.py` | `game.contract.json` (`tuning.freshness`) | Đạt |
| AC-P3-07 | Migration + regression P1–P2 sau khi bật v1.2: fixture `{kind:int}` → `[{id,kind,fresh}]`, `reserved` theo id; P1–P2 còn hiệu lực | `tests/test_smoke_p1.py` (đã chuyển sang kho cá thể), `tests/test_rules_p1.py`, `tests/test_rules_p2p3.py::Determinism::test_day_same_seed_same_bytes` | [`out-gather.jsonl`](../proof/phase-3/out-gather.jsonl) · [`quyanh-upload.txt`](../proof/phase-3/quyanh-upload.txt) | Đạt |
| AC-P3-EX-01..02 | Mở rộng: dòng nước lũ (`current`) · khách đặt trước (`reservations`) | **Không làm ở lõi** (mở rộng, không bật ở headless) | — | Không làm (đúng nguyên tắc "lõi trước, mở rộng sau") |

## Thay đổi test / fixture (có lý do)
- `tests/test_smoke_p1.py`: fixture kho chuyển từ **kho đếm** `{"items":{kind:int}}` sang **kho cá thể** `{"items":[{id,kind,fresh}]}`; `hold`/`stock`/`reserved` theo cá thể — lý do: contract v1.2 (breaking, ghi ở `CHANGELOG.md`).
- `tests/test_rules_p1.py`: cập nhật theo schema cá thể và giá chốt theo độ tươi (không nới test cho xanh — sửa cho khớp luật mới).

## Đánh giá ngắn
- Đạt: **Lát 0** adapter hai schema + chọn theo version (AC-P3-01,06) · **Lát 1** Lặn: hao tươi/`spoiled`/LIFO (AC-P3-02) · **Quán** hao tươi/giữ theo id/giá theo tươi (AC-P3-03,04) · HUD độ tươi (AC-P3-05) · migration + regression (AC-P3-07). Toàn bộ suite hiện hành **116/116 xanh**.
- Chưa làm: mở rộng `current`/`reservations` (AC-P3-EX-01..02) — chủ đích bỏ, không ảnh hưởng Test Contract.
- Vấn đề đã xử lý: ngưỡng ươn 30 và phép `floor` dùng **đơn vị tươi nguyên** (240 đơn vị/điểm; −2/tick gather, −1/tick quán; so ngưỡng **trước** làm tròn) để tránh sai số `float`.
- Ghi chú kèm theo: tag `phase-3` và bản `docs/verification/phase-3.md` này cần khớp **commit bàn giao** trên `main`.
