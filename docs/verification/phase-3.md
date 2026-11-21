# Ma trận truy vết & Phân tích tác động Phase 3 ("Mùa Nước Nổi" · Contract v1.2)

## 1. Phân tích tác động & thứ tự tích hợp (TICKET-03 §3)
| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Quán (`quan`) | `chonoi/sim/quan.py` (hỗ trợ song song v1.0/v1.1 kho đếm và v1.2 kho cá thể + độ tươi `Fraction`) | Giữ `test_quan_lat4.py`, `test_quan_p2.py`; thêm `test_quan_p3.py` | Nguyễn Thanh Tùng |
| Nội dung / HUD | `chonoi/content/dave_theme.py` (`freshness_badge`, lời thoại `spoiled`/`current_*`/`reservation_*`) | `test_quan_p3.py::TestMR1Phase3FreshnessContent` | Nguyễn Thanh Tùng |
| Adapter / Manifest v1.2 | `chonoi/inventory.py`, `chonoi/scenario.py`, `game.contract.json` | Smoke kho v1.2 (kho đếm → mã 2) | Sơn / Hải (bật khi hai đầu bàn giao sẵn sàng) |
| Lặn (`gather`) | `chonoi/sim/gather.py` (giỏ cá thể, hao tươi 0.5/s, `spoiled`) | Test gather v1.2 | Hải / Đức |
| Tài liệu thay đổi | `CHANGELOG.md`, `docs/verification/phase-3.md`, `docs/proof/phase-3/quan-p3.md` | — | Nguyễn Thanh Tùng |

**Quyết định chuyển đổi giữ `main` luôn chạy được**: `chonoi/sim/quan.py` hỗ trợ song song v1.0/v1.1 (kho đếm) và v1.2 (khi có khối `freshness` trong tuning hoặc `stock` là mảng cá thể `[{id, kind, fresh}]`). Khi Team Sáng và Adapter cùng bật `contract_version: "1.2"`, hai đầu khớp ngay mà không phá regression P1–P2 trong lúc chuyển.

## 2. Ma trận truy vết AC (phần `quan` & MR-1)
| AC | Nội dung kiểm chứng | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| `AC-P3-01` | Kho cá thể `[{id, kind, fresh}]`, hao tươi quán `0.25/s` (`1/240` mỗi tick, dùng `Fraction` chính xác ở ngưỡng 30), phát `spoiled` đúng 1 lần theo id, hàng ươn vẫn nằm trong kho | `tests/test_quan_p3.py::TestQuanPhase3FreshnessAndSpoilage` | [`quan-p3.md`](../proof/phase-3/quan-p3.md) | Đạt |
| `AC-P3-02` | Giữ chỗ theo mảng id cá thể tươi nhất hòa theo id nhỏ; khi cá thể giữ vừa ươn, phát hết `spoiled` theo id rồi nhả toàn bộ và thử giữ lại đúng 1 lần theo `(order_tick, id bàn)` → `reserved` hoặc `unfulfillable` | `tests/test_quan_p3.py::TestQuanPhase3FreshnessAndSpoilage` | [`quan-p3.md`](../proof/phase-3/quan-p3.md) | Đạt |
| `AC-P3-03` | Chốt `base_price = floor(giá × avg_fresh / 100)` lúc `cook_started`, `cook_started.data.items` là mảng cá thể sắp theo `(kind, id)`, boa `floor(base_price × 0.2)` áp trên giá đã chốt, món chín không hao tươi | `tests/test_quan_p3.py::TestQuanPhase3FreshPricingAndCooking` | [`quan-p3.md`](../proof/phase-3/quan-p3.md) | Đạt |
| `AC-P3-04` | Validate v1.2 (id trùng, `fresh` ngoài `[0,100]`, giữ hàng ươn → `BadInput`), mở rộng `burn` giữ lại cá thể tươi nhất | `tests/test_quan_p3.py::TestQuanPhase3FreshPricingAndCooking` | [`quan-p3.md`](../proof/phase-3/quan-p3.md) | Đạt |
| `AC-P3-REG` | Regression Phase 1 & Phase 2 (`test_quan_lat4`, `test_quan_p2`, `test_python_starter_units`, `test_team_check`) giữ nguyên 100% pass | Chạy chung toàn bộ bộ test P1–P3 | [`quan-p3.md`](../proof/phase-3/quan-p3.md) | Đạt |
| `AC-P3-MR1` | Nhãn độ tươi `freshness_badge`, lời thoại Mùa Nước Nổi và `ServiceReviewTracker` (tắt mặc định ở headless) | `tests/test_quan_p3.py::TestMR1Phase3FreshnessContent` | [`quan-p3.md`](../proof/phase-3/quan-p3.md) | Đạt |
