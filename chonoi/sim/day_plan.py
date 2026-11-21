"""Kế hoạch ngày D1–D5 (TICKET-02 §2) — Lát 3 Phase 2 (Quý Anh).

Dữ liệu nằm ở `tuning.day_plan` trong game.contract.json: mảng {day, dishes, ingredients}.
- `dishes`: id món -> số suất dự kiến (chỉ để tính mục tiêu thu gom).
- `ingredients`: tổng công thức × số suất, LUÔN tính lại từ menu (không tin giá trị khai).

Dùng cho `day` (Lát 4a): đầu Ngày phát event `day_plan` với `plan_for_day(...)`; dựng quán với
`QuanSim(..., allowed_dishes=allowed_dishes(...))` để lọc menu theo kế hoạch TRƯỚC khi lọc kho khả dụng.
Quán chạy riêng (`--mode quan`) không truyền allowed_dishes -> dùng cả 6 món.
"""

from ..errors import BadInput


def compute_ingredients(menu: dict, dishes: dict) -> dict:
    """Tổng công thức × số suất, khóa sắp theo id nguyên liệu, bỏ lượng 0."""
    total = {}
    for dish_id in sorted(dishes):
        if dish_id not in menu:
            raise BadInput(f"day_plan: món {dish_id!r} không có trong menu")
        n = dishes[dish_id]
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            raise BadInput(f"day_plan: số suất của {dish_id} phải là số nguyên dương")
        for kind, qty in menu[dish_id]["recipe"].items():
            total[kind] = total.get(kind, 0) + qty * n
    return {k: total[k] for k in sorted(total) if total[k] > 0}


def plan_for_day(tuning: dict, day: int, override: list = None) -> dict:
    """Kế hoạch của Ngày `day` (1-based): {"dishes", "ingredients"} đã sắp khóa.

    `override` là `day.day_plan` trong scenario (ghi đè theo số Ngày, mỗi mục có `dishes`; nếu khai
    `ingredients` thì phải khớp giá trị tính lại, sai -> BadInput / mã 2)."""
    entry = None
    for src in (override or [], tuning.get("day_plan", [])):
        entry = next((e for e in src if e.get("day") == day), None)
        if entry is not None:
            break
    if entry is None:
        raise BadInput(f"day_plan: không có kế hoạch cho Ngày {day}")
    dishes = entry.get("dishes")
    if not isinstance(dishes, dict) or not dishes:
        raise BadInput(f"day_plan Ngày {day}: dishes phải là object khác rỗng")
    ingredients = compute_ingredients(tuning["menu"], dishes)
    if "ingredients" in entry and dict(sorted(entry["ingredients"].items())) != ingredients:
        raise BadInput(f"day_plan Ngày {day}: ingredients khai {entry['ingredients']} khác tính lại {ingredients}")
    return {"dishes": {k: dishes[k] for k in sorted(dishes)}, "ingredients": ingredients}


def allowed_dishes(tuning: dict, day: int, override: list = None) -> list:
    """Id món được bán trong Ngày `day` (theo mã Unicode) — truyền vào QuanSim(allowed_dishes=...)."""
    return sorted(plan_for_day(tuning, day, override)["dishes"])


def validate_day_plan(tuning: dict):
    """Kiểm `tuning.day_plan` khi nạp contract: đủ Ngày 1..N liên tục, món có thật, ingredients khớp công thức."""
    plan = tuning.get("day_plan")
    if plan is None:
        return
    if not isinstance(plan, list) or not plan:
        raise BadInput("tuning.day_plan phải là mảng khác rỗng")
    days = [e.get("day") if isinstance(e, dict) else None for e in plan]
    if days != list(range(1, len(plan) + 1)):
        raise BadInput(f"tuning.day_plan phải liệt kê Ngày 1..{len(plan)} theo thứ tự, đang là {days}")
    for d in days:
        plan_for_day(tuning, d)
