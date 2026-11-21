"""Mở rộng Phase 4 — Bảng xếp hạng cục bộ Top 10 (`leaderboard`).

Luật TICKET-04 §3:
- Lưu bền vững top 10 cục bộ dạng `{"entries":[{"name","score","days_completed","seed"}]}`.
- Sắp điểm giảm dần; hòa điểm thì mục ghi trước đứng trước (kể cả sau khi đọc lại từ đĩa).
- Chỉ ghi một mục cho mỗi lượt chuẩn đủ 5 Ngày (`days_completed == 5`, không scenario, `reason == "days_complete"`).
- Tên Unicode khác rỗng; không làm đổi JSONL; soak không ghi xếp hạng.
"""

import argparse
import json
import os
import sys
import tempfile

from .errors import BadInput

MAX_ENTRIES = 10
DEFAULT_STORE = os.path.join(os.path.expanduser("~"), ".chonoi_leaderboard.json")


def _sort_entries(entries: list) -> list:
    # Python sort ổn định (Timsort) -> hòa điểm giữ nguyên thứ tự ghi trước đứng trước.
    return sorted(entries, key=lambda e: -int(e["score"]))[:MAX_ENTRIES]


def load_leaderboard(store_path: str = DEFAULT_STORE) -> list:
    if not os.path.exists(store_path):
        return []
    try:
        with open(store_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được leaderboard {store_path}: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise BadInput("file leaderboard sai định dạng (cần khóa 'entries')")
    return list(data["entries"])


def _atomic_write_json(path: str, payload: dict):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".lb-", suffix=".tmp", dir=d or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def record_entry(store_path: str, name: str, score: int, days_completed: int, seed: int) -> list:
    if not isinstance(name, str) or not name.strip():
        raise BadInput("tên người chơi trên leaderboard phải là chuỗi Unicode khác rỗng")
    entries = load_leaderboard(store_path)
    entries.append({
        "name": name,
        "score": int(score),
        "days_completed": int(days_completed),
        "seed": int(seed),
    })
    ranked = _sort_entries(entries)
    _atomic_write_json(store_path, {"entries": ranked})
    return ranked


def export_leaderboard(out_path: str, store_path: str = DEFAULT_STORE) -> dict:
    ranked = _sort_entries(load_leaderboard(store_path))
    payload = {"entries": ranked}
    _atomic_write_json(out_path, payload)
    return payload


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.leaderboard", description="Xuất bảng xếp hạng cục bộ Top 10.")
    p.add_argument("--export-leaderboard", required=True, dest="out")
    p.add_argument("--leaderboard", default=DEFAULT_STORE, dest="store")
    a = p.parse_args(argv)
    try:
        export_leaderboard(a.out, a.store)
    except BadInput as e:
        sys.stderr.write(f"lỗi leaderboard: {e}\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
