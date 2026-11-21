"""Test luật Phase 1 của nhóm (hộp đen qua headless_cmd), bám PRD-0 mục F / E — regression còn hiệu lực ở v1.2.

Đổi ở Phase 3 (lý do: Ticket-03 [THAY THẾ] kho đếm -> kho cá thể, giữ theo id, giá theo độ tươi):
  hold/stock/reserved/lost/items dùng mảng cá thể; base_price chốt theo fresh (hàng hao 1 tick -> 59 thay vì 60);
  fixture cá cố định dùng random_fish:false vì từ v1.1 cá bơi.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def run(w, mode, scenario=None, inputs=None, ticks=10, seed=1, every=1, extra=()):
    args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
            "--out", w.path("o.jsonl"), *extra]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), {mode: scenario})]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


def items(*kinds, fresh=100):
    return [{"id": f"I{i + 1}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


def kinds(arr):
    return [it["kind"] for it in arr]


def snap_at(rows, tick):
    return {r["tick"]: r for r in snapshots(rows)}[tick]


def names(rows):
    return [r["name"] for r in events(rows)]


# ---------------------------------------------------------------- GATHER
class Oxygen(unittest.TestCase):
    def test_underwater_drains_surface_refills(self):
        with Workdir() as w:
            rows = run(w, "gather", {"player": {"pos": [50, 10], "oxygen_ticks": 100}, "fish": []}, ticks=5)
            self.assertEqual(snap_at(rows, 5)["player"]["oxygen_ticks"], 95)
            rows = run(w, "gather", {"player": {"pos": [50, 0], "oxygen_ticks": 100}, "fish": []}, ticks=5)
            self.assertEqual(snap_at(rows, 5)["player"]["oxygen_ticks"], 130)

    def test_oxygen_empty_then_choke_at_t_plus_59(self):
        with Workdir() as w:
            rows = run(w, "gather", {"player": {"pos": [50, 10], "oxygen_ticks": 3}, "fish": []}, ticks=70)
            empty = events(rows, "oxygen_empty")
            self.assertEqual(len(empty), 1)
            self.assertEqual(empty[0]["tick"], 3)
            self.assertEqual(empty[0]["data"], {"oxygen_ticks": 0})
            choke = events(rows, "choke")
            self.assertEqual([e["tick"] for e in choke], [3 + 59])
            self.assertEqual(choke[0]["data"], {"hp": 2})
            self.assertEqual(snap_at(rows, 62)["player"]["zero_oxy_ticks"], 0)

    def test_surface_on_choke_tick_avoids_choke(self):
        with Workdir() as w:
            sc = {"player": {"pos": [50, 0.52], "vel": [0, -4], "oxygen_ticks": 0, "zero_oxy_ticks": 59}, "fish": []}
            rows = run(w, "gather", sc, [{"tick": 0, "move": [0, -1]}], ticks=3)
            self.assertNotIn("choke", names(rows))
            self.assertIn("surface", names(rows))

    def test_faint_drops_hold_lifo_and_empty_inventory(self):
        with Workdir() as w:
            sc = {"player": {"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                  "hold": items("ca_loc", "bong_sung", "ca_linh"), "fish": []}
            inv = w.path("inv.json")
            rows = run(w, "gather", sc, ticks=50, extra=("--inventory-out", inv))
            self.assertEqual(names(rows), ["choke", "faint", "gather_end"])
            faint = events(rows, "faint")[0]["data"]
            self.assertEqual((faint["cause"], faint["hp"]), ("choke", 0))
            self.assertEqual([it["id"] for it in faint["lost"]], ["I3", "I2", "I1"], "LIFO")
            self.assertEqual(events(rows, "gather_end")[0]["data"], {"reason": "fainted", "inventory": {"items": []}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_dive_and_surface_events(self):
        with Workdir() as w:
            rows = run(w, "gather", {"fish": []}, [{"tick": 0, "move": [0, 1]}, {"tick": 30, "move": [0, -1]}], ticks=70)
            self.assertEqual([n for n in names(rows) if n in ("dive", "surface")], ["dive", "surface"])
            dive = events(rows, "dive")[0]
            self.assertGreater(dive["data"]["pos"][1], 0.5)


class Harvest(unittest.TestCase):
    def test_gather_at_radius_edge_and_regrow(self):
        t = tuning()["gather"]
        with Workdir() as w:
            sc = {"player": {"pos": [20, 0]}, "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [22, 0]}],
                  "fish": [], "random_fish": False}
            rows = run(w, "gather", sc, [{"tick": 0, "interact": True}], ticks=2)
            ev = events(rows, "gather")
            self.assertEqual(ev[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": 1})
            self.assertEqual(ev[0]["tick"], 1)
            s = snap_at(rows, 1)
            self.assertEqual(s["hold"], [{"id": "I1", "kind": "bong_dien_dien", "fresh": 100}])
            self.assertEqual(s["nodes"][0]["regrow_ticks"], int(t["regrow_s"] * 60))
            self.assertFalse(s["nodes"][0]["ready"])

    def test_node_regrown_event(self):
        with Workdir() as w:
            sc = {"player": {"pos": [50, 0]}, "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [60, 0], "regrow_ticks": 2}]}
            rows = run(w, "gather", sc, ticks=3)
            self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "node_regrown")], [(2, {"node_id": "N1"})])

    def test_hold_full_on_gather(self):
        cap = tuning()["gather"]["hold_capacity"]
        with Workdir() as w:
            sc = {"player": {"pos": [12, 0]}, "hold": items(*["ca_loc"] * cap)}
            rows = run(w, "gather", sc, [{"tick": 0, "interact": True}], ticks=2)
            self.assertEqual(events(rows, "hold_full")[0]["data"],
                             {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
            self.assertTrue(snap_at(rows, 1)["nodes"][0]["ready"])

    def test_no_gather_underwater(self):
        with Workdir() as w:
            rows = run(w, "gather", {"player": {"pos": [12, 2]}}, [{"tick": 0, "interact": True}], ticks=2)
            self.assertNotIn("gather", names(rows))

    def test_nearest_node_tie_by_id(self):
        with Workdir() as w:
            sc = {"player": {"pos": [20, 0]}, "nodes": [{"id": "N10", "kind": "bong_sung", "pos": [21, 0]},
                                                         {"id": "N2", "kind": "bong_dien_dien", "pos": [19, 0]}]}
            rows = run(w, "gather", sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N2")


class Catch(unittest.TestCase):
    def test_catch_yield_and_cooldown(self):
        t = tuning()["gather"]
        cd = int(t["catch_cooldown_s"] * 60)
        with Workdir() as w:
            sc = {"player": {"pos": [15, 5]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [16, 5]},
                                                       {"id": "F2", "kind": "ca_loc", "pos": [15, 6]}], "random_fish": False}
            inp = [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": 2, "catch": True},
                   {"tick": 3, "catch": False}, {"tick": cd - 1, "catch": True},
                   {"tick": cd, "catch": False}, {"tick": cd + 1, "catch": True}]
            rows = run(w, "gather", sc, inp, ticks=cd + 3)
            caught = events(rows, "fish_caught")
            self.assertEqual(caught[0]["tick"], 1)
            self.assertEqual(caught[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": 3})
            self.assertEqual(len(caught), 2, "bấm khi đang hồi chiêu không bắt được")
            self.assertEqual(caught[1]["tick"], 2 + cd, "cooldown đặt ở t dùng lại từ t + L (bấm ở bước cd - 1 vẫn còn hồi)")
            self.assertEqual(kinds(snap_at(rows, cd + 3)["hold"]), ["ca_linh"] * 3 + ["ca_loc"])

    def test_catch_hold_full_keeps_fish_no_cooldown(self):
        cap = tuning()["gather"]["hold_capacity"]
        with Workdir() as w:
            sc = {"player": {"pos": [15, 5]}, "hold": items(*["ca_loc"] * (cap - 2)), "random_fish": False,
                  "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}, {"id": "F2", "kind": "ca_loc", "pos": [16, 5]}]}
            rows = run(w, "gather", sc, [{"tick": 0, "catch": True}], ticks=1)
            self.assertEqual(names(rows), ["hold_full"])
            self.assertEqual(events(rows)[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
            s = snap_at(rows, 1)
            self.assertEqual(len(s["fish"]), 2)
            self.assertEqual(s["player"]["catch_cd_ticks"], 0)

    def test_catch_out_of_range_or_at_surface(self):
        with Workdir() as w:
            rows = run(w, "gather", {"player": {"pos": [50, 5]}}, [{"tick": 0, "catch": True}], ticks=2)
            self.assertEqual(names(rows), [])
            self.assertEqual(snap_at(rows, 1)["player"]["catch_cd_ticks"], 0)
            sc = {"player": {"pos": [15, 0]}, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [15, 1]}]}
            rows = run(w, "gather", sc, [{"tick": 0, "catch": True}], ticks=2)
            self.assertNotIn("fish_caught", names(rows))

    def test_catch_on_last_tick_goes_to_inventory(self):
        with Workdir() as w:
            inv = w.path("inv.json")
            sc = {"player": {"pos": [15, 5]}, "time_left_ticks": 1, "random_fish": False,
                  "fish": [{"id": "F1", "kind": "ca_loc", "pos": [15, 5]}]}
            rows = run(w, "gather", sc, [{"tick": 0, "catch": True}], ticks=5, extra=("--inventory-out", inv))
            self.assertEqual(names(rows), ["fish_caught", "gather_end"])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.0}]})


# ---------------------------------------------------------------- QUAN
T = tuning()
Q = T["quan"]
FIRST = Q["first_customer_tick"]
STOVE = Q["stoves"][0]["pos"]
TABLE = Q["tables"][0]["pos"]


class Customers(unittest.TestCase):
    def test_first_customer_reserves_recipe(self):
        with Workdir() as w:
            rows = run(w, "quan", {"stock": items("ca_loc")}, ticks=FIRST, every=FIRST)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], FIRST)
            self.assertEqual(arr[0]["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})
            c = snap_at(rows, FIRST)["customers"][0]
            self.assertEqual((c["state"], c["order_status"], c["reserved"], c["order_tick"]),
                             ("waiting", "reserved", ["I1"], FIRST))
            self.assertEqual(c["patience_ticks_left"], int(Q["patience_s"] * 60))
            self.assertEqual(snap_at(rows, FIRST)["tables"][0]["customer_id"], "C1")

    def test_no_dish_when_stock_empty(self):
        with Workdir() as w:
            rows = run(w, "quan", {}, ticks=FIRST, every=FIRST)
            self.assertEqual([(e["name"], e["data"]) for e in events(rows)], [("no_dish", {})])

    def test_patience_runs_out(self):
        pat = int(Q["patience_s"] * 60)
        with Workdir() as w:
            rows = run(w, "quan", {"stock": items("ca_loc"), "random_customers": False,
                                   "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                                  "patience_ticks_left": 3}]}, ticks=5)
            left = events(rows, "customer_left")
            self.assertEqual(left[0]["tick"], 3)
            self.assertEqual(left[0]["data"], {"order_id": "C1", "table_id": "T1", "reason": "patience",
                                               "reputation": Q["reputation_initial"] + Q["left_reputation_delta"]})
            s = snap_at(rows, 3)
            self.assertEqual(s["customers"], [])
            self.assertEqual(kinds(s["stock"]), ["ca_loc"], "nhả giữ chỗ, tồn vật lý giữ nguyên")
            self.assertLess(pat, 10 ** 6)

    def test_reserved_over_stock_exit_2(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": [], "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}})
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(w.path("o.jsonl")))

    def test_bad_quan_fixtures_exit_2(self):
        bad = [
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "pho"}]},
            {"stock": items("ca_loc"), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                                     "reserved": ["I9"]}]},
            {"stock": items("ca_loc", fresh=20), "customers": [{"id": "C1", "table_id": "T1",
                                                               "dish_id": "ca_loc_nuong_trui"}]},
            {"stock": items("ca_loc"), "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                                     "order_status": "assigned"}]},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
                            "order_status": "served", "eat_ticks_left": 5}]},
            {"hand": {"order_id": "C9", "dish_id": "ca_loc_nuong_trui", "base_price": 60}},
            {"stoves": [{"id": "B1", "state": "cooking"}]},
            {"stoves": [{"id": "B9"}]},
            {"reputation": 9},
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned",
                            "reserved": []}],
             "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
             "stoves": [{"id": "B1", "state": "ready", "dish": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}}]},
        ]
        with Workdir() as w:
            for block in bad:
                sc = write_json(w.path("sc.json"), {"quan": block})
                code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, (block, err))


class Service(unittest.TestCase):
    def full_flow(self, w, patience=None):
        """Khách C1 có sẵn; đứng ở bếp nấu, chờ chín, bưng, đi tới bàn, phục vụ, chờ ăn xong."""
        cook = int(T["menu"]["ca_loc_nuong_trui"]["cook_s"] * 60)
        eat = int(Q["eat_s"] * 60)
        cust = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        if patience is not None:
            cust["patience_ticks_left"] = patience
        sc = {"player": {"pos": STOVE}, "stock": items("ca_loc", "ca_loc"), "random_customers": False, "customers": [cust]}
        t_pick = cook + 1
        walk = 200
        inp = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
               {"tick": t_pick, "interact": True}, {"tick": t_pick + 1, "interact": False, "move": [1, -0.86]}]
        return sc, inp, cook, eat, t_pick, walk

    def test_cook_pick_serve_pay_with_tip(self):
        with Workdir() as w:
            sc, inp, cook, eat, t_pick, _ = self.full_flow(w)
            # đi thẳng tới bàn: dùng scenario thứ hai đặt người ở bàn với món trên tay để tách bước
            rows = run(w, "quan", sc, inp, ticks=t_pick + 1)
            cs = events(rows, "cook_started")[0]
            self.assertEqual(cs["tick"], 1)
            self.assertEqual(cs["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui",
                                          "items": [{"id": "I1", "kind": "ca_loc", "fresh": 99.996}],
                                          "base_price": 59}, "floor(60 × 99.9958 / 100) = 59")
            s1 = snap_at(rows, 1)
            self.assertEqual([it["id"] for it in s1["stock"]], ["I2"])
            self.assertEqual(s1["customers"][0]["order_status"], "assigned")
            self.assertEqual(s1["stoves"][0]["state"], "cooking")
            ready = events(rows, "dish_ready")[0]
            self.assertEqual(ready["tick"], 1 + cook)
            picked = events(rows, "dish_picked")[0]
            self.assertEqual(picked["tick"], t_pick + 1)
            self.assertEqual(snap_at(rows, t_pick + 1)["hand"],
                             {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 59})
            self.assertEqual(snap_at(rows, t_pick + 1)["stoves"][0]["state"], "idle")

    def test_serve_and_pay(self):
        eat = int(Q["eat_s"] * 60)
        with Workdir() as w:
            sc = {"player": {"pos": TABLE}, "stock": [], "random_customers": False,
                  "hand": {"order_id": "C1", "dish_id": "lau_ca_linh_dien_dien", "base_price": 120},
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien",
                                 "order_status": "assigned", "reserved": []}]}
            rows = run(w, "quan", sc, [{"tick": 0, "interact": True}], ticks=eat + 2)
            served = events(rows, "served")[0]
            self.assertEqual(served["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien",
                                              "patience_ticks_left": int(Q["patience_s"] * 60) - 1,
                                              "base_price": 120, "tip": 24})
            paid = events(rows, "paid")[0]
            self.assertEqual(paid["tick"], 1 + eat)
            self.assertEqual(paid["data"], {"order_id": "C1", "table_id": "T1", "base_price": 120, "tip": 24,
                                            "amount": 144, "reason": "finished_eating"})
            end = rows[-1]
            self.assertEqual((end["money"], end["earned"]), (144, 144))
            self.assertAlmostEqual(end["reputation"], Q["reputation_initial"] + Q["tip_reputation"], places=6)
            self.assertEqual(end["score"], 144 + 100 * 3)
            self.assertEqual(snap_at(rows, 1 + eat)["customers"], [])

    def test_no_tip_when_patience_low(self):
        pat = int(Q["patience_s"] * 60)
        with Workdir() as w:
            sc = {"player": {"pos": TABLE}, "random_customers": False,
                  "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned",
                                 "reserved": [], "patience_ticks_left": pat // 2}]}
            rows = run(w, "quan", sc, [{"tick": 0, "interact": True}], ticks=1)
            self.assertEqual(events(rows, "served")[0]["data"]["tip"], 0, "kiên nhẫn sau bước 1 < 50% thì không boa")

    def test_serve_on_patience_zero_tick_is_valid(self):
        with Workdir() as w:
            sc = {"player": {"pos": TABLE}, "random_customers": False,
                  "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned",
                                 "reserved": [], "patience_ticks_left": 1}]}
            rows = run(w, "quan", sc, [{"tick": 0, "interact": True}], ticks=2)
            self.assertEqual(names(rows), ["served"])

    def test_closing_pays_eaters_and_releases_waiters(self):
        with Workdir() as w:
            sc = {"time_left_ticks": 2, "random_customers": False, "stock": items("bong_sung", "bong_sung"),
                  "tables": [], "customers": [
                      {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                       "order_status": "served", "reserved": [], "eat_ticks_left": 300, "base_price": 40, "tip": 8}]}
            rows = run(w, "quan", sc, ticks=10)
            self.assertEqual(names(rows), ["paid", "quan_end"])
            self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
            self.assertEqual(events(rows, "quan_end")[0]["data"],
                             {"reason": "time", "money": 48, "earned": 48, "shift_earned": 48,
                              "reputation": Q["reputation_initial"] + Q["tip_reputation"]})
            self.assertEqual(rows[-1]["reason"], "time")
            sc = {"time_left_ticks": 2, "random_customers": False, "stock": items("bong_sung", "bong_sung"),
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]}
            rows = run(w, "quan", sc, ticks=10)
            left = events(rows, "customer_left")[0]["data"]
            self.assertEqual((left["reason"], left["reputation"]), ("closing", Q["reputation_initial"]))

    def test_leaving_customer_drops_dish_on_stove(self):
        with Workdir() as w:
            dish = {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}
            sc = {"random_customers": False, "stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 100}],
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned",
                                 "reserved": [], "patience_ticks_left": 1}]}
            rows = run(w, "quan", sc, ticks=2)
            self.assertEqual(snap_at(rows, 1)["stoves"][0]["state"], "idle")
            self.assertIsNone(snap_at(rows, 1)["stoves"][0]["dish"])

    def test_deterministic_full_shift(self):
        with Workdir() as w:
            inp = [{"tick": 0, "move": [-1, 1]}, {"tick": 200, "move": [0, 0], "interact": True}]
            for i in (1, 2):
                code, err = run_headless("--mode", "quan", "--seed", "5", "--ticks", "11000",
                                         "--scenario", write_json(w.path("sc.json"), {"quan": {"stock": items(*["ca_loc"] * 3, *["ca_linh"] * 6, "bong_dien_dien", "bong_dien_dien", *["bong_sung"] * 4)}}),
                                         "--inputs", write_json(w.path("in.json"), frames(*inp)),
                                         "--out", w.path(f"q{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("q1.jsonl"), "rb") as a, open(w.path("q2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())
            rows = read_jsonl(w.path("q1.jsonl"))
            self.assertEqual(rows[-1]["reason"], "time")
            self.assertEqual(rows[-1]["ticks"], int(Q["duration_s"] * 60))


if __name__ == "__main__":
    unittest.main()
