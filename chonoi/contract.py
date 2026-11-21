"""Đọc game.contract.json và kiểm tuning theo Test Contract v1.2 (Ticket-02 số chuẩn + Ticket-03 độ tươi)."""

import json
import os

from .errors import BadInput

FIXED_RECIPES = {
    "ca_loc_nuong_trui": {"ca_loc": 1},
    "goi_bong_sung": {"bong_sung": 2},
    "lau_ca_linh_dien_dien": {"ca_linh": 3, "bong_dien_dien": 1},
    "canh_chua_ca_loc": {"ca_loc": 1, "bong_dien_dien": 1},
    "ca_keo_nuong": {"ca_keo": 2},
    "lau_mam": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1},
}
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
SUPPORTED_VERSIONS = ("1.2",)

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _range(name, r, lo, hi):
    if not (isinstance(r, list) and len(r) == 2 and all(_num(c) for c in r) and lo <= r[0] <= r[1] <= hi):
        raise BadInput(f"tuning.{name} phải là [a, b] với {lo} <= a <= b <= {hi}")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    if c.get("contract_version") not in SUPPORTED_VERSIONS:
        raise BadInput(f"contract_version phải là một trong {SUPPORTED_VERSIONS}")
    validate_tuning(c.get("tuning"))
    return c


def _validate_gather(g):
    _between("gather.duration_s", g.get("duration_s"), 1, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    for k in ("dock_radius", "interact_radius", "catch_radius"):
        _between(f"gather.{k}", g.get(k), 0.5, 10)
    _between("gather.swim_speed", g.get("swim_speed"), 0.5, 20)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 1, 600)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 1, 60)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or set(fy) != set(FISH_KINDS):
        raise BadInput(f"tuning.gather.fish_yield phải có đúng {FISH_KINDS}")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen = set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind phải thuộc {NODE_KINDS}")
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    _int_between("gather.fish_initial", g.get("fish_initial"), 0, 100)
    _between("gather.fish_speed", g.get("fish_speed"), 0, 20)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 100_000)
    _int_between("gather.fish_max", g.get("fish_max"), 0, 100)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 100_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0, 100)
    _range("gather.fish_x", g.get("fish_x"), b["x"][0], b["x"][1])
    for key in ("fish_depths", "fish_spawn_depths", "fish_weights"):
        m = g.get(key)
        if not isinstance(m, dict) or set(m) != set(FISH_KINDS):
            raise BadInput(f"tuning.gather.{key} phải có đúng {FISH_KINDS}")
    for k in FISH_KINDS:
        _range(f"gather.fish_depths.{k}", g["fish_depths"][k], 0, b["d"][1])
        _between(f"gather.fish_weights.{k}", g["fish_weights"][k], 0, 1e9)
        ds = g["fish_spawn_depths"][k]
        if not isinstance(ds, list) or not ds or not all(_num(c) for c in ds):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là mảng số")
    xs = g.get("fish_spawn_x")
    if not isinstance(xs, list) or not xs or not all(_num(c) for c in xs):
        raise BadInput("tuning.gather.fish_spawn_x phải là mảng số")
    mon = g.get("monsters")
    if not isinstance(mon, dict) or not isinstance(mon.get("species"), dict) or not isinstance(mon.get("spawns"), list):
        raise BadInput("tuning.gather.monsters phải có species và spawns")
    for name, sp in mon["species"].items():
        for k in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            _between(f"gather.monsters.species.{name}.{k}", sp.get(k), 0, 100)
        _int_between(f"gather.monsters.species.{name}.recoil_ticks", sp.get("recoil_ticks"), 1, 10_000)
        _range(f"gather.monsters.species.{name}.depths", sp.get("depths"), 0, b["d"][1])
    for m in mon["spawns"]:
        if m.get("kind") not in mon["species"]:
            raise BadInput(f"tuning.gather.monsters.spawns.{m.get('id')}: kind lạ")
        _pos_in(f"gather.monsters.{m['id']}.pos", m.get("pos"), b, ("x", "d"))
        wps = m.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"tuning.gather.monsters.{m['id']}: cần đúng 2 waypoint")
        _int_between(f"gather.monsters.{m['id']}.from_day", m.get("from_day"), 1, 99)
    _int_between("gather.monsters.invuln_ticks", mon.get("invuln_ticks"), 0, 10_000)
    _between("gather.monsters.loss_ratio", mon.get("loss_ratio"), 0, 1)


def _validate_quan(q):
    _between("quan.duration_s", q.get("duration_s"), 1, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 1, 600)
    _between("quan.walk_speed", q.get("walk_speed"), 0.5, 20)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null trong lõi (mở rộng Cháy món chưa bật)")
    for name, items in (("stoves", q.get("stoves")), ("tables", q.get("tables"))):
        if not isinstance(items, list) or not items:
            raise BadInput(f"quan.{name} phải là mảng không rỗng")
        for it in items:
            _pos_in(f"quan.{name}.{it.get('id')}.pos", it.get("pos"), q["bounds"], ("x", "z"))
    _pos_in("quan.start_pos", q.get("start_pos"), q["bounds"], ("x", "z"))
    if q.get("carry_limit") != 1:
        raise BadInput("quan.carry_limit phải là 1")
    lo, hi, r0 = q.get("reputation_min"), q.get("reputation_max"), q.get("reputation_initial")
    if not (_num(lo) and _num(hi) and _num(r0) and lo <= r0 <= hi):
        raise BadInput("quan.reputation_min <= reputation_initial <= reputation_max")


def _validate_plan(t):
    menu = t["menu"]
    plan = t.get("day_plan")
    if not isinstance(plan, list) or len(plan) != 5:
        raise BadInput("tuning.day_plan phải là mảng 5 Ngày")
    for i, d in enumerate(plan):
        if not isinstance(d, dict) or d.get("day") != i + 1:
            raise BadInput(f"tuning.day_plan[{i}].day phải là {i + 1}")
        dishes = d.get("dishes")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"tuning.day_plan[{i}].dishes phải là map món -> số suất")
        for k, n in dishes.items():
            if k not in menu:
                raise BadInput(f"tuning.day_plan[{i}]: món lạ {k}")
            _int_between(f"day_plan[{i}].dishes.{k}", n, 1, 99)
        if d.get("ingredients") != plan_ingredients(dishes, menu):
            raise BadInput(f"tuning.day_plan[{i}].ingredients khác tổng công thức × số suất")


def plan_ingredients(dishes, menu) -> dict:
    out = {}
    for dish, n in dishes.items():
        for k, c in menu[dish]["recipe"].items():
            out[k] = out.get(k, 0) + c * n
    return out


def _validate_shop(s):
    if not isinstance(s, dict):
        raise BadInput("tuning.shop phải là object")
    _int_between("shop.max_ticks", s.get("max_ticks"), 1, 100_000)
    ups = s.get("upgrades")
    if not isinstance(ups, dict) or not {"oxygen", "hp"} <= set(ups):
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    field = {"oxygen": "oxygen_max_s", "hp": "hp_max"}
    for kind, levels in ups.items():
        if not isinstance(levels, list) or not levels:
            raise BadInput(f"tuning.shop.upgrades.{kind} phải là mảng cấp")
        for i, lv in enumerate(levels):
            if lv.get("level") != i + 1:
                raise BadInput(f"tuning.shop.upgrades.{kind}[{i}].level phải là {i + 1}")
            _int_between(f"shop.upgrades.{kind}[{i}].price", lv.get("price"), 0, 10 ** 9)
            if kind in field and not _num(lv.get(field[kind])):
                raise BadInput(f"tuning.shop.upgrades.{kind}[{i}] thiếu {field[kind]}")


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    fr = t.get("freshness")
    if not isinstance(fr, dict) or fr.get("initial") != 100 or not _num(fr.get("gather_decay_per_s")) \
            or not _num(fr.get("quan_decay_per_s")) or not _num(fr.get("spoiled_below")):
        raise BadInput("tuning.freshness phải có initial=100, gather_decay_per_s, quan_decay_per_s, spoiled_below")
    _validate_gather(g)
    _validate_quan(q)
    if {k: v.get("recipe") for k, v in menu.items()} != FIXED_RECIPES:
        raise BadInput("menu phải đúng 6 món và công thức chuẩn của Ticket-02")
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
    _validate_plan(t)
    _validate_shop(t.get("shop"))
    if not _num(t.get("score", {}).get("reputation_multiplier")):
        raise BadInput("score.reputation_multiplier phải là số")
