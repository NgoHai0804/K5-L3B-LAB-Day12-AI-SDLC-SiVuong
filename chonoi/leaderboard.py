"""Bảng xếp hạng cục bộ (mở rộng Phase 4, contract v1.3).

File store JSON: `{"entries": [{"name", "score", "days_completed", "seed"}, ...]}` đã sắp.
Quy tắc (Ticket-04 mục 3):
  - Chỉ ghi MỘT mục cho mỗi lượt chuẩn đủ 5 Ngày (headless `--mode day --days 5`, không scenario).
  - Sắp điểm giảm dần; hòa thì mục ghi TRƯỚC đứng trước (sắp ổn định) — kể cả sau khi mở lại.
  - Giữ bền vững tối đa 10 mục.
  - `name` là chuỗi Unicode khác rỗng.

File xếp hạng KHÔNG phải JSONL; soak không ghi vào đây.
"""

import json
import os
import tempfile

from .errors import BadInput

DEFAULT_STORE = "leaderboard.json"
LIMIT = 10
KEYS = ("name", "score", "days_completed", "seed")


def validate_name(name: str) -> str:
    if not isinstance(name, str) or name.strip() == "":
        raise BadInput("player-name phải là chuỗi Unicode khác rỗng")
    return name


def _entry(e) -> dict:
    if not isinstance(e, dict) or set(e) != set(KEYS):
        raise BadInput("mục xếp hạng phải có đúng name, score, days_completed, seed")
    name = validate_name(e["name"])
    out = {"name": name}
    for k in ("score", "days_completed", "seed"):
        v = e[k]
        if isinstance(v, bool) or not isinstance(v, int):
            raise BadInput(f"xếp hạng.{k} phải là số nguyên")
        out[k] = v
    return out


def sort_entries(entries) -> list:
    """Sắp điểm giảm dần, ổn định (hòa -> mục đứng trước giữ nguyên vị trí)."""
    return sorted(entries, key=lambda e: -e["score"])


def load(path: str = DEFAULT_STORE) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được bảng xếp hạng {path}: {e}")
    if not isinstance(data, dict) or set(data) != {"entries"} or not isinstance(data["entries"], list):
        raise BadInput("file bảng xếp hạng phải có đúng một khóa 'entries' (mảng)")
    return [_entry(e) for e in data["entries"]]


def _write(path: str, entries) -> None:
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".lb-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"entries": entries}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def record(path: str, name: str, score: int, days_completed: int, seed: int, limit: int = LIMIT) -> list:
    """Thêm một mục rồi sắp + cắt còn `limit`. Trả bảng mới."""
    entries = load(path)
    entries.append(_entry({"name": name, "score": int(score), "days_completed": int(days_completed), "seed": int(seed)}))
    entries = sort_entries(entries)[:limit]
    _write(path, entries)
    return entries


def export(store: str = DEFAULT_STORE, out: str = None, limit: int = LIMIT) -> list:
    """Xuất bảng đã sắp ra `out` (mặc định chính store sau khi sắp)."""
    entries = sort_entries(load(store))[:limit]
    _write(out or store, entries)
    return entries
