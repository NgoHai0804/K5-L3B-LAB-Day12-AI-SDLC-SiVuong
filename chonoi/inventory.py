"""File kho — adapter hai schema (ADR-0002).

- **v1.0/v1.1** (schema đếm): `{"items": {"<kind>": <số nguyên ≥ 0>}}`.
- **v1.2** (schema cá thể + độ tươi): `{"items": [{"id": <str>, "kind": <kind>, "fresh": <0..100>}, ...]}`.

Bên đọc chọn schema **theo `contract_version`**; không ràng buộc version thì tự nhận dạng
(dict → đếm, list → cá thể). Ở v1.2, kho đếm bị **từ chối (mã 2)**.

Độ tươi lưu nội bộ bằng **đơn vị nguyên** (240 đơn vị = 1 điểm) để so ngưỡng và `floor` chính xác;
xuất ra `fresh` làm tròn 3 chữ số (đủ để đọc lại giữ đúng nhánh ở ngưỡng 30).
"""

import json
import os
import tempfile

from .errors import BadInput

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
# v1.1 (TICKET-02 §1.3, ADR-0001): thêm ca_keo (cá kèo) và keo_neo (bông kèo nèo).
KINDS = KINDS_P1 + ("ca_keo", "keo_neo")

FRESH_MAX = 100.0
FRESH_UNITS = 240                                   # 240 đơn vị = 1 điểm tươi
UNITS_MAX = int(FRESH_MAX * FRESH_UNITS)            # 24000


def version_tuple(v):
    """'1.2' -> (1, 2). Không đọc được -> (0, 0)."""
    try:
        parts = [int(x) for x in str(v).split(".")[:2]]
        return tuple((parts + [0, 0])[:2])
    except (TypeError, ValueError):
        return (0, 0)


def fresh_to_units(fresh) -> int:
    return int(round(float(fresh) * FRESH_UNITS))


def units_to_fresh(u: int) -> float:
    return u / FRESH_UNITS


# --- schema ĐẾM (v1.0/v1.1) -------------------------------------------------
def validate_items(items, kinds=KINDS):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


# --- schema CÁ THỂ + độ tươi (v1.2) ----------------------------------------
def validate_carried(items, kinds=KINDS):
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể")
    seen, out = set(), []
    for it in items:
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput("mỗi cá thể phải có đúng khóa {id, kind, fresh}")
        i = it["id"]
        if not isinstance(i, str) or not i:
            raise BadInput("id cá thể phải là chuỗi khác rỗng")
        if i in seen:
            raise BadInput(f"id cá thể trùng: {i}")
        seen.add(i)
        if it["kind"] not in kinds:
            raise BadInput(f"nguyên liệu lạ: {it['kind']}")
        f = it["fresh"]
        if isinstance(f, bool) or not isinstance(f, (int, float)) or not (0 <= f <= FRESH_MAX):
            raise BadInput(f"fresh không hợp lệ: {f!r}")
        out.append({"id": i, "kind": it["kind"], "fresh": f})
    return out


def read_inventory(path: str, kinds=KINDS, version=None) -> object:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    items = data["items"]
    if version is not None and version_tuple(version) >= (1, 2):
        if isinstance(items, dict):
            raise BadInput("contract v1.2 không nhận kho đếm (cần mảng cá thể)")
        return validate_carried(items, kinds)
    if isinstance(items, list):          # tự nhận dạng khi không ràng buộc version
        return validate_carried(items, kinds)
    return validate_items(items, kinds)


def hold_to_items(hold: list) -> dict:
    """Giỏ (mảng id/kind theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu (schema đếm)."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items, version=None):
    """Ghi kho nguyên tử. `items` là dict (đếm) hoặc list cá thể (v1.2)."""
    if isinstance(items, list):
        payload = {"items": [{"id": it["id"], "kind": it["kind"],
                              "fresh": round(float(it["fresh"]), 3)} for it in items]}
    else:
        clean = {k: items[k] for k in sorted(items) if items[k] > 0}
        payload = {"items": clean}
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
