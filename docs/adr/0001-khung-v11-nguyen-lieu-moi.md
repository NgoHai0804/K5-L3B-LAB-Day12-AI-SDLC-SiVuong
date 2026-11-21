# ADR-0001: Mở rộng khung cho nguyên liệu v1.1 (`ca_keo`, `keo_neo`)

- Trạng thái: chấp nhận (phần **schema kho** của ADR này sau đó được ADR-0002 thay thế; **tập kind v1.1 vẫn giữ**)
- Ngày, người quyết: 2026-11-21 · Hải (Integrator) — Phase 2 Lát 1 (TICKET-02)

## Bối cảnh
Contract v1.1 (TICKET-02) thêm 2 nguyên liệu: **`ca_keo`** (cá kèo) và **`keo_neo`** (kèo nèo, hái ở nút N5/N6).
Ba file khung kiểm danh sách loại cố định nên sẽ **từ chối** dữ liệu v1.1:
`chonoi/inventory.py` (`KINDS`), `chonoi/scenario.py` (`NODE_KINDS`/`FISH_KINDS`), `chonoi/contract.py`
(kind nút hái, số đàn `fish_initial`).

## Các lựa chọn đã cân nhắc
1. **Không sửa khung**, để nguyên liệu mới lọt qua ngoài danh mục → sai hợp đồng kho §1 (kind lạ phải thoát 2),
   hỏng reader của Team Tối.
2. **Sửa khung tối thiểu** để nhận tập kind v1.1, giữ nguyên nguyên tắc "kind lạ ⇒ thoát 2".

## Quyết định
Chọn (2). Sửa khung **chỉ để mở rộng tập kind hợp lệ**, không đổi hành vi khác:
- `inventory.KINDS` += `"ca_keo"`, `"keo_neo"`.
- `scenario.NODE_KINDS` += `"keo_neo"`; `scenario.FISH_KINDS` += `"ca_keo"`.
- `contract._validate_gather`: cho phép nút kind `keo_neo`; đổi ràng buộc `fish_initial` từ "đúng 6 đàn" → số đàn v1.1 (8).
- `contract` giữ ràng buộc "phải có ít nhất một nút `bong_dien_dien` và một `bong_sung`".

## Hệ quả (bảng tác động)
| Module/file | Thay đổi | Ảnh hưởng |
|---|---|---|
| `chonoi/inventory.py` | thêm 2 kind | writer/reader kho chấp nhận `ca_keo`/`keo_neo`; kind lạ vẫn thoát 2 |
| `chonoi/scenario.py` | thêm kind nút/cá | scenario v1.1 hợp lệ; P1 không đổi |
| `chonoi/contract.py` | nới kiểm nút/`fish_initial` | preset v1.0 cũ vẫn hợp lệ; preset v1.1 mới hợp lệ |
| `tests/test_smoke_p1.py` | `len(fish)` 6 → 8 | số chuẩn v1.1; ghi lý do trong `docs/verification/phase-2.md` |
| `game.contract.json` | v1.1 | nguồn số liệu mới cho cả 2 team |

- **Không** đổi định dạng file kho ở thời điểm này (vẫn `{kind: int≥0}`) ⇒ Team Tối chỉ cần nhận thêm 2 kind khi
  nấu món mới (Lát 3).
- **Cập nhật sau (Phase 3):** định dạng file kho **đã đổi** sang **kho cá thể** `{"items":[{id,kind,fresh}]}` theo
  **ADR-0002** (contract v1.2, giữ ở v1.3). ADR-0001 vẫn còn hiệu lực cho **tập kind** (`ca_keo`, `keo_neo`).
- Test: toàn bộ suite xanh sau thay đổi (P1 + P2 Lát 1).
