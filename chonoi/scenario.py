"""Nạp và kiểm scenario (Contract D, v1.2). Trả về dict của đúng khối theo mode (day: cả dict).

Kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ, schema cá thể (hold/stock),
thủy quái, khối day. Mâu thuẫn mức luật cần cả fixture (giữ chỗ trỏ id lạ / đã ươn / dùng chung, đơn assigned
thiếu món...) được kiểm khi dựng sim — vẫn TRƯỚC khi ghi đầu ra (mã 2) với gather/quan.
"""

import json

from .contract import FISH_KINDS, NODE_KINDS, plan_ingredients
from .errors import BadInput
from .inventory import validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
QUAN_PLAYER_KEYS = {"pos", "vel"}
STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
STOVE_STATES = ("idle", "cooking", "ready")
TABLE_KEYS = {"id", "pos"}
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip"}
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
DISH_KEYS = {"order_id", "dish_id", "base_price"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict):
        raise BadInput("scenario phải là object")
    if mode == "day":
        if not set(data) <= {"gather", "quan", "day"}:
            raise BadInput("scenario day chỉ có khối 'day', 'gather', 'quan'")
        for k in data:
            if not isinstance(data[k], dict):
                raise BadInput(f"khối {k} phải là object")
        _check_block(data.get("gather", {}), "gather", tuning)
        q = data.get("quan", {})
        if "stock" in q or "reputation" in q:
            raise BadInput("chạy day không nhận quan.stock / quan.reputation (dùng gather.hold)")
        _check_block(q, "quan", tuning)
        _validate_day(data.get("day", {}), tuning)
        return data
    if not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    _check_block(block, mode, tuning)
    return block


def _check_block(block, mode, tuning):
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_day(b, tuning):
    extra = set(b) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ trong day: {sorted(extra)}")
    for k in ("money", "earned"):
        if k in b:
            _nonneg_int(f"day.{k}", b[k])
    if ("money" in b) != ("earned" in b) and b.get("money", 0) > 0:
        raise BadInput("day: khai cả money và earned khi có tiền đầu kỳ")
    if b.get("money", 0) > b.get("earned", 0):
        raise BadInput("day: cần 0 <= money <= earned")
    q = tuning["quan"]
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput("day.reputation ngoài miền")
    ups = b.get("upgrades", {})
    if not isinstance(ups, dict):
        raise BadInput("day.upgrades phải là object")
    for k, lv in ups.items():
        levels = tuning["shop"]["upgrades"].get(k)
        if levels is None or k not in ("oxygen", "hp"):
            raise BadInput(f"day.upgrades: nâng cấp lạ {k}")
        if isinstance(lv, bool) or not isinstance(lv, int) or not (0 <= lv <= len(levels)):
            raise BadInput(f"day.upgrades.{k} phải là cấp trong [0, {len(levels)}]")
    plan = b.get("day_plan", [])
    if not isinstance(plan, list):
        raise BadInput("day.day_plan phải là mảng")
    seen = set()
    for o in plan:
        if not isinstance(o, dict) or set(o) - {"day", "dishes", "ingredients"} or "dishes" not in o:
            raise BadInput("day.day_plan: mỗi mục là {day, dishes[, ingredients]}")
        d = o.get("day")
        if isinstance(d, bool) or not isinstance(d, int) or not (1 <= d <= len(tuning["day_plan"])) or d in seen:
            raise BadInput("day.day_plan.day phải là Ngày hợp lệ, không trùng")
        seen.add(d)
        dishes = o["dishes"]
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput("day.day_plan.dishes phải là map món -> số suất")
        for k, n in dishes.items():
            if k not in tuning["menu"] or isinstance(n, bool) or not isinstance(n, int) or n <= 0:
                raise BadInput(f"day.day_plan.dishes: {k} phải là món có thật với số suất nguyên dương")
        if "ingredients" in o and o["ingredients"] != plan_ingredients(dishes, tuning["menu"]):
            raise BadInput("day.day_plan.ingredients khác tổng công thức × số suất")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        validate_items(b["hold"])
        if len(b["hold"]) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    if "invuln_ticks" in p and p["invuln_ticks"] > g["monsters"]["invuln_ticks"]:
        raise BadInput("player.invuln_ticks vượt thời gian bất tử")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", 1)
        if p["zero_oxy_ticks"] > g["choke_interval_ticks"] - 1:
            raise BadInput("player.zero_oxy_ticks vượt nhịp ngạt")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    cd_max = int(round(g["catch_cooldown_s"] * 60))
    if "catch_cd_ticks" in p and p["catch_cd_ticks"] > cd_max:
        raise BadInput("player.catch_cd_ticks vượt hồi chiêu tối đa")
    regrow_max = int(round(g["regrow_s"] * 60))
    for n in b.get("nodes", []):
        if set(n) - {"id", "kind", "pos", "regrow_ticks"}:
            raise BadInput(f"nodes.{n['id']}: trường lạ")
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
            if n["regrow_ticks"] > regrow_max:
                raise BadInput(f"nodes.{n['id']}: regrow_ticks vượt thời gian mọc lại")
    for f in b.get("fish", []):
        if set(f) - {"id", "kind", "pos", "heading_deg", "age_ticks"}:
            raise BadInput(f"fish.{f['id']}: trường lạ")
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    species = g["monsters"]["species"]
    for m in b.get("monsters", []):
        mid = m["id"]
        if set(m) - MONSTER_KEYS or not {"kind", "pos", "waypoints"} <= set(m):
            raise BadInput(f"monsters.{mid}: cần kind, pos, waypoints và không có trường lạ")
        if m["kind"] not in species:
            raise BadInput(f"monsters.{mid}: kind lạ")
        _pos(f"monsters.{mid}.pos", m["pos"], bounds)
        wps = m["waypoints"]
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"monsters.{mid}: cần đúng hai waypoint")
        for w in wps:
            _pos(f"monsters.{mid}.waypoints", w, bounds)
        if m.get("target_idx", 1) not in (0, 1) or isinstance(m.get("target_idx", 1), bool):
            raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
        st = m.get("state", "patrol")
        if st not in ("patrol", "chase", "recoil"):
            raise BadInput(f"monsters.{mid}.state lạ")
        if "state_ticks_left" in m:
            _nonneg_int(f"monsters.{mid}.state_ticks_left", m["state_ticks_left"])
        rd = m.get("recoil_dir")
        if st == "recoil":
            if m.get("state_ticks_left", 0) <= 0 or m["state_ticks_left"] > species[m["kind"]]["recoil_ticks"]:
                raise BadInput(f"monsters.{mid}: recoil cần timer dương trong giới hạn")
            if not (isinstance(rd, list) and len(rd) == 2 and all(_num(c) for c in rd)
                    and abs((rd[0] ** 2 + rd[1] ** 2) - 1) < 1e-6):
                raise BadInput(f"monsters.{mid}.recoil_dir phải là vector đơn vị")
        elif rd is not None or m.get("state_ticks_left", 0) != 0:
            raise BadInput(f"monsters.{mid}: chỉ recoil mới có recoil_dir / state_ticks_left")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    q = tuning["quan"]
    if "reputation" in b:
        r = b["reputation"]
        if not _num(r) or not (q["reputation_min"] <= r <= q["reputation_max"]):
            raise BadInput(f"reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    if "hand" in b and b["hand"] is not None:
        _dish_payload("hand", b["hand"], tuning)
    for t in b.get("tables", []):
        if set(t) - TABLE_KEYS:
            raise BadInput(f"tables.{t['id']}: trường lạ")
        if "pos" in t:
            _pos(f"tables.{t['id']}.pos", t["pos"], qb, axes=("x", "z"))
    for st in b.get("stoves", []):
        if set(st) - STOVE_KEYS:
            raise BadInput(f"stoves.{st['id']}: trường lạ")
        if "pos" in st:
            _pos(f"stoves.{st['id']}.pos", st["pos"], qb, axes=("x", "z"))
        if "state" in st and st["state"] not in STOVE_STATES:
            raise BadInput(f"stoves.{st['id']}.state phải là một trong {STOVE_STATES}")
        for key in ("cook_ticks_left", "ready_ticks"):
            if key in st:
                _nonneg_int(f"stoves.{st['id']}.{key}", st[key])
        if st.get("dish") is not None:
            _dish_payload(f"stoves.{st['id']}.dish", st["dish"], tuning)
        if st.get("state") == "cooking" and st.get("dish") is not None:
            cook_max = int(round(tuning["menu"][st["dish"]["dish_id"]]["cook_s"] * 60))
            if st.get("cook_ticks_left", 0) > cook_max:
                raise BadInput(f"stoves.{st['id']}.cook_ticks_left vượt thời gian nấu")
    menu = tuning["menu"]
    for c in b.get("customers", []):
        cid = c["id"]
        if set(c) - CUSTOMER_KEYS:
            raise BadInput(f"customers.{cid}: trường lạ")
        if c.get("dish_id") not in menu:
            raise BadInput(f"customers.{cid}: dish_id phải là món có trong menu")
        if "state" in c and c["state"] not in CUSTOMER_STATES:
            raise BadInput(f"customers.{cid}.state phải là một trong {CUSTOMER_STATES}")
        if "order_status" in c and c["order_status"] not in ORDER_STATUSES:
            raise BadInput(f"customers.{cid}.order_status phải là một trong {ORDER_STATUSES}")
        for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
            if key in c:
                _nonneg_int(f"customers.{cid}.{key}", c[key])
        for key in ("base_price", "tip"):
            if key in c and c[key] is not None:
                _nonneg_int(f"customers.{cid}.{key}", c[key])
        if "reserved" in c:
            r = c["reserved"]
            if not isinstance(r, list) or not all(isinstance(x, str) and x for x in r) or len(set(r)) != len(r):
                raise BadInput(f"customers.{cid}.reserved phải là mảng id cá thể không trùng")


def _dish_payload(name, d, tuning):
    if not isinstance(d, dict) or set(d) != DISH_KEYS:
        raise BadInput(f"{name} phải là {{order_id, dish_id, base_price}} hoặc null")
    if not isinstance(d["order_id"], str) or not d["order_id"]:
        raise BadInput(f"{name}.order_id phải là chuỗi")
    if d["dish_id"] not in tuning["menu"]:
        raise BadInput(f"{name}.dish_id phải là món có trong menu")
    bp = d["base_price"]
    if isinstance(bp, bool) or not isinstance(bp, int) or bp <= 0:
        raise BadInput(f"{name}.base_price phải là số nguyên dương")
