"""Bộ test Phase 2 cho Lát 3 (Quý Anh): 2 bếp/4 bàn + 6 món + kế hoạch ngày, đọc số từ game.contract.json v1.1.

Bao phủ:
- AC-P2-05: B1[2,8], B2[5,8]; T1[9,2], T2[13,2], T3[9,6], T4[13,6]; thứ tự tương tác (khoảng cách, bếp trước bàn, id);
            hai bếp nấu song song, mỗi bếp lấy đơn reserved cũ nhất theo (order_tick, id bàn).
- AC-P2-06: đủ 6 món + 2 nguyên liệu mới (ca_keo, keo_neo) dưới dạng dữ liệu; nấu đúng thời gian, chốt đúng giá;
            file kho nhận nguyên liệu mới, vẫn từ chối kind lạ; contract từ chối công thức có nguyên liệu lạ.
- AC-P2-07: kế hoạch D1–D5 đúng ticket (ingredients = Σ công thức × suất); lọc menu theo kế hoạch TRƯỚC kho khả dụng;
            món ngoài kế hoạch không được gọi dù đủ kho; thiếu món trong kế hoạch -> no_dish; khai ingredients sai -> mã 2.
"""

import copy
import os
import subprocess
import sys
import unittest

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.day_plan import allowed_dishes, compute_ingredients, plan_for_day
from chonoi.sim.quan import QuanSim
from helpers import Workdir, read_jsonl, snapshots, write_json

TUNING = load_contract()["tuning"]
Q, MENU = TUNING["quan"], TUNING["menu"]
FIRST = int(Q["first_customer_tick"])


def _run_py_headless(*args):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = subprocess.run([sys.executable, "-m", "chonoi.headless", *args], cwd=root, capture_output=True, text=True)
    return p.returncode, p.stderr


def make_sim(scenario=None, allowed=None, seed=1):
    return QuanSim(TUNING, scenario or {}, Streams(seed), IdAllocator(), allowed_dishes=allowed)


IDLE = InputState((0.0, 0.0), {"interact": False, "catch": False}, set())
PRESS = InputState((0.0, 0.0), {"interact": True, "catch": False}, {"interact"})


def run_until(sim, tick):
    evs = []
    while sim.phase_tick < tick and not sim.done:
        evs += sim.step(IDLE)
    return evs


class TestP2Lat3StovesTables(unittest.TestCase):
    """AC-P2-05."""

    def test_ac_p2_05_layout_from_contract(self):
        self.assertEqual([(s["id"], s["pos"]) for s in Q["stoves"]], [("B1", [2, 8]), ("B2", [5, 8])])
        self.assertEqual([(t["id"], t["pos"]) for t in Q["tables"]],
                         [("T1", [9, 2]), ("T2", [13, 2]), ("T3", [9, 6]), ("T4", [13, 6])])
        snap = make_sim().snapshot()
        self.assertEqual([s["id"] for s in snap["stoves"]], ["B1", "B2"])
        self.assertEqual([t["id"] for t in snap["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertTrue(all(t["customer_id"] is None for t in snap["tables"]))

    def test_ac_p2_05_two_stoves_cook_in_parallel_oldest_first(self):
        sc = {"player": {"pos": [2, 8]}, "random_customers": False,
              "stock": {"ca_loc": 2, "bong_sung": 2},
              "customers": [
                  {"id": "C1", "table_id": "T3", "dish_id": "goi_bong_sung", "order_tick": 0},
                  {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 0},
                  {"id": "C3", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 5}]}
        sim = make_sim(sc)
        ev1 = sim.step(PRESS)  # ở B1: cùng order_tick 0 -> id bàn nhỏ hơn (T1 / C2) trước
        self.assertEqual([(n, d["stove_id"], d["order_id"]) for n, d in ev1 if n == "cook_started"], [("cook_started", "B1", "C2")])
        sim.pos = [5.0, 8.0]
        sim.step(IDLE)
        ev2 = sim.step(PRESS)  # ở B2: đơn còn lại cũ nhất là C1 (T3, order_tick 0)
        self.assertEqual([(d["stove_id"], d["order_id"]) for n, d in ev2 if n == "cook_started"], [("B2", "C1")])
        states = {s["id"]: s["state"] for s in sim.snapshot()["stoves"]}
        self.assertEqual(states, {"B1": "cooking", "B2": "cooking"})

    def test_ac_p2_05_stove_wins_tie_with_table(self):
        sc = {"player": {"pos": [5.0, 7.25]}, "random_customers": False, "stock": {"ca_loc": 1},
              "tables": [{"id": "T3", "pos": [5.0, 6.5]}],
              "customers": [{"id": "C1", "table_id": "T3", "dish_id": "ca_loc_nuong_trui"}]}
        ev = make_sim(sc).step(PRESS)  # cách B2 và T3 đều 0.75 m -> bếp trước bàn
        self.assertEqual([(n, d.get("stove_id")) for n, d in ev], [("cook_started", "B2")])

    def test_ac_p2_05_customers_fill_t1_to_t4(self):
        sim = make_sim({"stock": {"ca_loc": 9}})
        interval = int(round(Q["customer_interval_s"] * 60))
        evs = run_until(sim, FIRST + 4 * interval)
        arr = [d for n, d in evs if n == "customer_arrived"]
        # Lượt 5 (tick 120 + 4·900 = 3720) trùng tick C1 hết kiên nhẫn (120 + 3600): khách rời ở bước 4
        # trước khi xét lượt mới ở bước 5, nên T1 trống lại và được cấp cho C5.
        self.assertEqual([d["table_id"] for d in arr], ["T1", "T2", "T3", "T4", "T1"])
        self.assertEqual([d["order_id"] for d in arr], ["C1", "C2", "C3", "C4", "C5"])
        left = [d for n, d in evs if n == "customer_left"]
        self.assertEqual([(d["order_id"], d["reason"]) for d in left], [("C1", "patience")])


class TestP2Lat3Menu(unittest.TestCase):
    """AC-P2-06."""

    EXPECTED = {
        "ca_loc_nuong_trui": ({"ca_loc": 1}, 6, 60),
        "goi_bong_sung": ({"bong_sung": 2}, 4, 40),
        "lau_ca_linh_dien_dien": ({"ca_linh": 3, "bong_dien_dien": 1}, 10, 120),
        "canh_chua_ca_loc": ({"ca_loc": 1, "bong_dien_dien": 1}, 8, 90),
        "ca_keo_nuong": ({"ca_keo": 2}, 6, 70),
        "lau_mam": ({"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, 12, 200),
    }

    def test_ac_p2_06_menu_data_matches_ticket(self):
        self.assertEqual({k: (v["recipe"], v["cook_s"], v["price"]) for k, v in MENU.items()}, self.EXPECTED)

    def test_ac_p2_06_each_dish_cooks_with_its_time_and_price(self):
        stock = {"ca_loc": 2, "ca_linh": 5, "bong_dien_dien": 3, "bong_sung": 2, "ca_keo": 3, "keo_neo": 1}
        for dish_id, (_, cook_s, price) in self.EXPECTED.items():
            sc = {"player": {"pos": [2, 8]}, "random_customers": False, "stock": stock,
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish_id}]}
            sim = make_sim(sc)
            ev = dict(sim.step(PRESS))["cook_started"]
            self.assertEqual(ev["base_price"], price, dish_id)
            self.assertEqual(sorted(ev["items"]), ev["items"], "items sắp theo kind")
            self.assertEqual(sim.snapshot()["stoves"][0]["cook_ticks_left"], int(round(cook_s * 60)), dish_id)
            ready_at = None
            while ready_at is None and sim.phase_tick < 2000:
                for n, _ in sim.step(IDLE):
                    if n == "dish_ready":
                        ready_at = sim.phase_tick
            self.assertEqual(ready_at, 1 + int(round(cook_s * 60)), dish_id)

    def test_ac_p2_06_inventory_file_accepts_new_kinds(self):
        with Workdir() as w:
            inv = write_json(w.path("kho.json"), {"items": {"ca_keo": 2, "keo_neo": 1, "ca_linh": 2, "bong_dien_dien": 1}})
            code, err = _run_py_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                         "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"],
                             {"bong_dien_dien": 1, "ca_keo": 2, "ca_linh": 2, "keo_neo": 1})
            bad = write_json(w.path("bad.json"), {"items": {"ca_hô": 1}})
            self.assertEqual(_run_py_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", bad,
                                              "--out", w.path("q2.jsonl"))[0], 2)

    def test_ac_p2_06_contract_rejects_unknown_recipe_kind(self):
        t = copy.deepcopy(TUNING)
        t["menu"]["lau_mam"]["recipe"]["mam_ca_sac"] = 1
        with self.assertRaises(BadInput):
            validate_tuning(t)


class TestP2Lat3DayPlan(unittest.TestCase):
    """AC-P2-07."""

    TICKET = {
        1: ({"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}, {"ca_loc": 3, "bong_sung": 6}),
        2: ({"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2}, {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2}),
        3: ({"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2},
            {"bong_sung": 4, "ca_loc": 2, "bong_dien_dien": 2, "ca_keo": 4}),
        4: ({"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1},
            {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1, "ca_loc": 2, "bong_sung": 2}),
        5: ({"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1},
            {"ca_linh": 5, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 2, "ca_loc": 1}),
    }

    def test_ac_p2_07_plan_d1_to_d5_matches_ticket(self):
        self.assertEqual([e["day"] for e in TUNING["day_plan"]], [1, 2, 3, 4, 5])
        for day, (dishes, ingredients) in self.TICKET.items():
            plan = plan_for_day(TUNING, day)
            self.assertEqual(plan["dishes"], dishes, day)
            self.assertEqual(plan["ingredients"], ingredients, day)
            self.assertEqual(list(plan["ingredients"]), sorted(plan["ingredients"]), "khóa sắp theo id")
            self.assertEqual(allowed_dishes(TUNING, day), sorted(dishes))

    def test_ac_p2_07_slots_needed(self):
        slots = {d: sum(plan_for_day(TUNING, d)["ingredients"].values()) for d in self.TICKET}
        self.assertEqual(slots, {1: 9, 2: 10, 3: 12, 4: 9, 5: 10})

    def test_ac_p2_07_menu_filtered_by_plan_before_stock(self):
        """Kho đủ cả 6 món nhưng Ngày 1 chỉ bán cá nướng / gỏi súng."""
        stock = {"ca_loc": 9, "ca_linh": 9, "bong_dien_dien": 9, "bong_sung": 9, "ca_keo": 9, "keo_neo": 9}
        seen = set()
        for seed in range(1, 25):
            sim = make_sim({"stock": stock}, allowed=allowed_dishes(TUNING, 1), seed=seed)
            seen |= {d["dish_id"] for n, d in run_until(sim, FIRST) if n == "customer_arrived"}
        self.assertEqual(seen, {"ca_loc_nuong_trui", "goi_bong_sung"})

    def test_ac_p2_07_no_dish_when_plan_dishes_missing(self):
        """Ngày 3 cần gỏi / canh chua / cá kèo; kho chỉ đủ lẩu cá linh (ngoài kế hoạch) -> no_dish."""
        sim = make_sim({"stock": {"ca_linh": 3, "bong_dien_dien": 0, "bong_sung": 1}}, allowed=allowed_dishes(TUNING, 3))
        self.assertIn(("no_dish", {}), run_until(sim, FIRST))
        sim = make_sim({"stock": {"ca_linh": 3, "bong_dien_dien": 1}}, allowed=allowed_dishes(TUNING, 3))
        self.assertIn(("no_dish", {}), run_until(sim, FIRST), "lẩu cá linh đủ kho nhưng không thuộc kế hoạch D3")

    def test_ac_p2_07_customer_may_order_beyond_planned_servings(self):
        """Đã đủ số suất dự kiến vẫn gọi tiếp món trong kế hoạch nếu còn nguyên liệu."""
        sim = make_sim({"stock": {"ca_loc": 9}}, allowed=allowed_dishes(TUNING, 2))
        interval = int(round(Q["customer_interval_s"] * 60))
        arr = [d for n, d in run_until(sim, FIRST + 3 * interval) if n == "customer_arrived"]
        self.assertEqual([d["dish_id"] for d in arr], ["ca_loc_nuong_trui"] * 4, "kế hoạch D2 chỉ 2 suất cá nướng")

    def test_ac_p2_07_override_and_bad_ingredients(self):
        override = [{"day": 2, "dishes": {"ca_keo_nuong": 1}}]
        self.assertEqual(plan_for_day(TUNING, 2, override), {"dishes": {"ca_keo_nuong": 1}, "ingredients": {"ca_keo": 2}})
        self.assertEqual(plan_for_day(TUNING, 1, override)["dishes"], self.TICKET[1][0], "ngày không ghi đè giữ preset")
        with self.assertRaises(BadInput):
            plan_for_day(TUNING, 2, [{"day": 2, "dishes": {"ca_keo_nuong": 1}, "ingredients": {"ca_keo": 1}}])
        with self.assertRaises(BadInput):
            plan_for_day(TUNING, 2, [{"day": 2, "dishes": {"pho_bo": 1}}])
        with self.assertRaises(BadInput):
            compute_ingredients(MENU, {"lau_mam": 0})

    def test_ac_p2_07_contract_rejects_bad_day_plan(self):
        for mutate in (lambda p: p.reverse(),
                       lambda p: p[0]["ingredients"].update(ca_loc=99),
                       lambda p: p[1]["dishes"].update(bun_rieu=1)):
            t = copy.deepcopy(TUNING)
            mutate(t["day_plan"])
            with self.assertRaises(BadInput):
                validate_tuning(t)


if __name__ == "__main__":
    unittest.main()
