"""File kho v1.2 (Ticket-03): kho CÁ THỂ {"items": [{"id", "kind", "fresh"}, ...]}.

Đọc: từ chối kho đếm v1.0, sai schema, kind lạ, id trùng, fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: sắp theo id, qua file tạm cùng thư mục rồi thay thế nguyên tử.

Bên trong mô phỏng, độ tươi giữ bằng `Fraction` (chính xác tuyệt đối ở ngưỡng 30 và phép floor);
chỉ đổi sang float khi xuất. Khi xuất, giữ đúng phía của ngưỡng ươn (không để 29.999… thành 30.0).
"""

import json
import math
import os
import tempfile
from fractions import Fraction

from .errors import BadInput
from .ids import id_key

KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS_P1 = KINDS  # tên cũ, giữ cho mã dùng lại
SPOILED_BELOW = Fraction(30)


def to_fraction(v) -> Fraction:
    return Fraction(repr(v)) if isinstance(v, float) else Fraction(v)


def fresh_out(fr: Fraction, threshold=SPOILED_BELOW) -> float:
    """Fraction -> float để xuất, giữ đúng phía ngưỡng."""
    f = float(fr)
    th = float(threshold)
    if fr < threshold and f >= th:
        f = math.nextafter(th, -math.inf)
    if f == 0:
        f = 0.0
    if float(int(f)) == f and abs(f) < 1e15:
        return float(f)
    return f


def item_out(it) -> dict:
    return {"id": it["id"], "kind": it["kind"], "fresh": fresh_out(it["fresh"])}


def validate_items(items, kinds=KINDS, seen=None) -> list:
    """Mảng cá thể -> danh sách {id, kind, fresh: Fraction}. `seen` gom id để kiểm trùng giữa nhiều nơi chứa."""
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể {id, kind, fresh} (kho đếm v1.0 không còn hợp lệ ở contract v1.2)")
    seen = set() if seen is None else seen
    out = []
    for i, e in enumerate(items):
        if not isinstance(e, dict) or set(e) != {"id", "kind", "fresh"}:
            raise BadInput(f"items[{i}] phải có đúng khóa id, kind, fresh")
        iid, kind, fresh = e["id"], e["kind"], e["fresh"]
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"items[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"id cá thể trùng: {iid}")
        seen.add(iid)
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind!r}")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not math.isfinite(fresh) \
                or not (0 <= fresh <= 100):
            raise BadInput(f"items[{i}].fresh phải hữu hạn trong [0, 100]")
        out.append({"id": iid, "kind": kind, "fresh": to_fraction(fresh)})
    return out


def read_inventory(path: str, kinds=KINDS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(data["items"], kinds)


def items_sorted(items) -> list:
    return sorted(items, key=lambda it: id_key(it["id"]))


def hold_to_items(hold: list) -> list:
    """Giỏ (cá thể theo thứ tự vào giỏ) -> mảng xuất, sắp theo id."""
    return [item_out(it) for it in items_sorted(hold)]


def write_inventory(path: str, items: list):
    """`items`: cá thể nội bộ (fresh Fraction) hoặc đã xuất (fresh float)."""
    rows = []
    for it in items_sorted(items):
        fr = it["fresh"]
        rows.append({"id": it["id"], "kind": it["kind"],
                     "fresh": fresh_out(fr) if isinstance(fr, Fraction) else fr})
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            # repr(float) đọc lại đúng từng bit -> giữ giá trị và nhánh ở ngưỡng 30
            json.dump({"items": rows}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
