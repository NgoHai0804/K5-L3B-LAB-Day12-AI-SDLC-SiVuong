"""Soak test headless nhiều Ngày cho Phase 4 (TICKET-04 · Contract v1.3).

Chạy:
    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy liên tục N Ngày (mặc định 10) trong một tiến trình headless bằng bot tất định:
mỗi Ngày đi qua gather → quan → shop; kế hoạch D1–D5 lặp cho Ngày 6–10;
tiền, tổng thu (`earned`), uy tín, cấp nâng cấp và id cá thể liên tục xuyên suốt.
"""

import argparse
import json
import math
import os
import sys
import time

from .contract import load_contract
from .ids import IdAllocator
from .inputs import InputState
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim

DEFAULT_DAY_PLANS = (
    {"day": 1, "dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}},
    {"day": 2, "dishes": {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2}},
    {"day": 3, "dishes": {"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2}},
    {"day": 4, "dishes": {"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1}},
    {"day": 5, "dishes": {"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1}},
)

UPGRADE_PRICES = {
    "oxygen": (200, 400),
    "hp": (250, 500),
}


def _move_toward(pos, target):
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return (0.0, 0.0)
    return (dx / dist, dy / dist)


def _run_gather_bot(tuning, streams, ids, upgrades) -> dict:
    # Áp dụng nâng cấp oxygen/hp đang có hiệu lực cho Ngày hiện tại.
    t = json.loads(json.dumps(tuning))
    ox_lvl = upgrades.get("oxygen", 0)
    hp_lvl = upgrades.get("hp", 0)
    if ox_lvl == 1:
        t["gather"]["oxygen_max_s"] = 45
    elif ox_lvl >= 2:
        t["gather"]["oxygen_max_s"] = 60
    if hp_lvl == 1:
        t["gather"]["hp_max"] = 4
    elif hp_lvl >= 2:
        t["gather"]["hp_max"] = 5

    sim = GatherSim(t, {}, streams, ids)
    # Bot tất định: bơi đến nút N3/N4 (bong_sung) hái 2 bông rồi quay về bến cập bến nhanh.
    target_node = next((n for n in sim.nodes if n["kind"] == "bong_sung"), sim.nodes[0])
    dock_pos = t["gather"]["dock_pos"]
    phase = "harvest"
    for _ in range(min(3000, sim.time_left_ticks)):
        if sim.done:
            break
        if phase == "harvest":
            if len(sim.hold) >= 2:
                phase = "dock"
            else:
                mv = _move_toward(sim.pos, target_node["pos"])
                near = math.dist(sim.pos, target_node["pos"]) <= t["gather"]["interact_radius"]
                edges = {"interact"} if near else set()
                sim.step(InputState(mv, {"interact": near, "catch": False}, edges))
                continue
        mv = _move_toward(sim.pos, dock_pos)
        in_dock = math.dist(sim.pos, dock_pos) <= t["gather"]["dock_radius"]
        edges = {"interact"} if in_dock else set()
        sim.step(InputState(mv, {"interact": in_dock, "catch": False}, edges))
    if not sim.done:
        # Chốt ca nếu chưa về kịp
        sim.time_left_ticks = 1
        sim.step(InputState((0.0, 0.0), {"interact": False, "catch": False}, set()))
    return sim.inventory_items()


def _run_quan_bot(tuning, streams, ids, stock, reputation, allowed_dishes, money, earned):
    # Bot tất định cho buổi tối: nấu -> bưng -> phục vụ khi có khách, tối đa 1800 tick rút gọn hoặc đủ ca.
    sim = QuanSim(
        tuning,
        {"reputation": reputation, "time_left_ticks": 1800},
        streams,
        ids,
        inventory=stock,
        allowed_dishes=allowed_dishes,
    )
    sim.money = money
    sim.earned = earned
    stove = sim.stoves[0]
    for _ in range(1805):
        if sim.done:
            break
        target_pos = None
        want_interact = False
        if sim.hand is not None:
            cust = next((c for c in sim.customers if c["id"] == sim.hand["order_id"]), None)
            if cust is not None:
                tb = next(tb for tb in sim.tables if tb["id"] == cust["table_id"])
                target_pos = tb["pos"]
                want_interact = math.dist(sim.pos, target_pos) <= sim.t["interact_radius"]
        elif stove["state"] == "ready":
            target_pos = stove["pos"]
            want_interact = math.dist(sim.pos, target_pos) <= sim.t["interact_radius"]
        elif stove["state"] == "idle" and any(c["order_status"] == "reserved" for c in sim.customers):
            target_pos = stove["pos"]
            want_interact = math.dist(sim.pos, target_pos) <= sim.t["interact_radius"]

        mv = _move_toward(sim.pos, target_pos) if target_pos is not None else (0.0, 0.0)
        edges = {"interact"} if want_interact else set()
        sim.step(InputState(mv, {"interact": want_interact, "catch": False}, edges))
    return sim.money, sim.earned, sim.reputation


def _run_shop_bot(money: int, upgrades: dict) -> tuple:
    """Mua nâng cấp tiếp theo nếu đủ tiền (trừ money, giữ earned, hiệu lực từ Ngày kế)."""
    bought = dict(upgrades)
    for key in ("oxygen", "hp"):
        lvl = bought.get(key, 0)
        prices = UPGRADE_PRICES[key]
        if lvl < len(prices) and money >= prices[lvl]:
            money -= prices[lvl]
            bought[key] = lvl + 1
            break
    return money, bought


def run_soak(seed: int, days: int) -> dict:
    t0 = time.perf_counter()
    tuning = load_contract()["tuning"]
    streams = Streams(seed)
    ids = IdAllocator()
    mult = tuning["score"]["reputation_multiplier"]

    money = 0
    earned = 0
    reputation = float(tuning["quan"]["reputation_initial"])
    active_upgrades = {"oxygen": 0, "hp": 0}
    bought_upgrades = {"oxygen": 0, "hp": 0}
    results = []
    crashes = 0
    days_completed = 0

    for day_idx in range(1, days + 1):
        try:
            plan = DEFAULT_DAY_PLANS[(day_idx - 1) % len(DEFAULT_DAY_PLANS)]
            # Lọc chỉ giữ các món tồn tại trong menu hiện tại (tương thích v1.1 và v1.2/v1.3).
            plan_dishes = [d for d in plan["dishes"] if d in tuning["menu"]]
            allowed = set(plan_dishes) if plan_dishes else set(tuning["menu"].keys())

            stock = _run_gather_bot(tuning, streams, ids, active_upgrades)
            money, earned, reputation = _run_quan_bot(
                tuning, streams, ids, stock, reputation, allowed, money, earned
            )
            money, bought_upgrades = _run_shop_bot(money, bought_upgrades)
            score = earned + mult * math.floor(reputation)
            days_completed += 1
            results.append({
                "day": day_idx,
                "earned": earned,
                "reputation": round(reputation, 3),
                "score": score,
            })
            # Chỉ khi dựng Ngày mới mới sao cấp đã mua sang active_upgrades.
            active_upgrades = dict(bought_upgrades)
        except Exception:
            crashes += 1
            break

    return {
        "days": days,
        "days_completed": days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": round(time.perf_counter() - t0, 4),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak", description="Soak headless nhiều Ngày (Contract v1.3).")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--days", type=int, default=10)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.days < 1:
        sys.stderr.write("days phải >= 1\n")
        return 2
    res = run_soak(a.seed, a.days)
    out_dir = os.path.dirname(os.path.abspath(a.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
