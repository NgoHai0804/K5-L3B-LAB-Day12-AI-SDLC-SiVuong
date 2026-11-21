"""Test luật Phase 2 (Ticket-02, contract v1.1) và Phase 3 (Ticket-03, v1.2) qua headless_cmd (hộp đen).

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def run(w, mode, scenario=None, inputs=None, ticks=10, seed=1, every=1, extra=(), expect=0):
    args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
            "--out", w.path("o.jsonl"), *extra]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    assert code == expect, err
    return read_jsonl(w.path("o.jsonl")) if expect == 0 else None


def snap_at(rows, tick):
    return {r["tick"]: r for r in snapshots(rows)}[tick]


def items(*kinds, fresh=100, start=1):
    return [{"id": f"I{i + start}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


QUIET = {"random_fish": False, "monsters": []}


class Freshness(unittest.TestCase):
    def test_spoiled_on_first_step_from_30(self):
        with Workdir() as w:
            rows = run(w, "gather", {"gather": dict(QUIET, hold=items("ca_linh", fresh=30))}, ticks=1)
            sp = events(rows, "spoiled")
            self.assertEqual(len(sp), 1)
            self.assertEqual((sp[0]["tick"], sp[0]["data"]),
                             (1, {"item_id": "I1", "kind": "ca_linh", "location": "hold"}))

    def test_spoiled_once_and_by_id(self):
        with Workdir() as w:
            hold = [{"id": "I10", "kind": "ca_loc", "fresh": 30}, {"id": "I2", "kind": "bong_sung", "fresh": 30}]
            rows = run(w, "gather", {"gather": dict(QUIET, hold=hold)}, ticks=20)
            self.assertEqual([e["data"]["item_id"] for e in events(rows, "spoiled")], ["I2", "I10"])

    def test_gather_decay_half_per_second(self):
        with Workdir() as w:
            rows = run(w, "gather", {"gather": dict(QUIET, hold=items("ca_loc"))}, ticks=120, every=120)
            self.assertAlmostEqual(snap_at(rows, 120)["hold"][0]["fresh"], 99.0, delta=0.01)

    def test_quan_decay_quarter_per_second_and_price(self):
        with Workdir() as w:
            sc = {"quan": {"stock": items("ca_loc", fresh=50), "random_customers": False, "player": {"pos": [2, 8]},
                           "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}}
            rows = run(w, "quan", sc, [{"tick": 0, "interact": True}], ticks=1)
            cs = events(rows, "cook_started")[0]["data"]
            self.assertEqual(cs["base_price"], 29, "floor(60 × 49.9958 / 100)")
            self.assertAlmostEqual(cs["items"][0]["fresh"], 50 - 1 / 240, delta=0.01)

    def test_spoiled_stock_not_cooked_and_rereserve(self):
        """Phần giữ vừa ươn -> nhả và giữ lại cá thể tươi khác; thiếu -> unfulfillable."""
        with Workdir() as w:
            stock = [{"id": "I1", "kind": "ca_loc", "fresh": 30}, {"id": "I2", "kind": "ca_loc", "fresh": 80}]
            sc = {"quan": {"stock": stock, "random_customers": False,
                           "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                          "reserved": ["I1"]}]}}
            rows = run(w, "quan", sc, ticks=1)
            self.assertEqual(events(rows, "spoiled")[0]["data"], {"item_id": "I1", "kind": "ca_loc", "location": "stock"})
            c = snap_at(rows, 1)["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["I2"]))
            sc["quan"]["stock"] = stock[:1]
            rows = run(w, "quan", sc, ticks=1)
            c = snap_at(rows, 1)["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"]), ("unfulfillable", []))

    def test_freshest_reserved_first(self):
        with Workdir() as w:
            stock = [{"id": "I1", "kind": "ca_loc", "fresh": 60}, {"id": "I2", "kind": "ca_loc", "fresh": 90},
                     {"id": "I3", "kind": "ca_loc", "fresh": 90}]
            rows = run(w, "quan", {"quan": {"stock": stock}}, ticks=120, every=120)
            self.assertEqual(snap_at(rows, 120)["customers"][0]["reserved"], ["I2"])

    def test_spoiled_not_available_for_customers(self):
        with Workdir() as w:
            rows = run(w, "quan", {"quan": {"stock": items("ca_loc", fresh=20)}}, ticks=120, every=120)
            self.assertEqual([e["name"] for e in events(rows)], ["no_dish"])

    def test_bad_item_fixtures_exit_2(self):
        with Workdir() as w:
            for sc in ({"gather": {"hold": ["ca_loc"]}},
                       {"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": -1}]}},
                       {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 90}],
                                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                                "reserved": ["I1", "I1"]}]}}):
                mode = next(iter(sc))
                run(w, mode, sc, ticks=0, expect=2)


class FishAndMonsters(unittest.TestCase):
    def test_initial_fish_and_spawn_schedule(self):
        with Workdir() as w:
            rows = run(w, "gather", None, ticks=720, every=360)
            s0 = snap_at(rows, 0)
            self.assertEqual(len(s0["fish"]), 8)
            pts = {tuple(f["pos"]) for f in s0["fish"]}
            self.assertEqual(len(pts), 8, "8 điểm khác nhau")
            spawned = events(rows, "fish_spawned")
            self.assertEqual([e["tick"] for e in spawned], [360, 720])
            self.assertEqual(spawned[0]["data"]["id"], "F9")

    def test_fish_stays_in_species_band(self):
        with Workdir() as w:
            rows = run(w, "gather", None, ticks=3000, every=100)
            bands = {"ca_linh": (3, 12), "ca_loc": (8, 20), "ca_keo": (22, 28)}
            for s in snapshots(rows):
                for f in s["fish"]:
                    lo, hi = bands[f["kind"]]
                    self.assertTrue(lo - 1e-6 <= f["pos"][1] <= hi + 1e-6, f)
                    self.assertTrue(4 - 1e-6 <= f["pos"][0] <= 96 + 1e-6, f)

    def test_monster_hit_loses_half_lifo_invuln_recoil(self):
        with Workdir() as w:
            m = {"id": "M1", "kind": "ca_sau", "pos": [50, 20], "waypoints": [[50, 20], [54, 20]]}
            sc = {"gather": {"random_fish": False, "monsters": [m], "player": {"pos": [50, 20]},
                             "hold": items("ca_loc", "bong_sung", "ca_linh")}}
            rows = run(w, "gather", sc, ticks=120)
            hits = events(rows, "monster_hit")
            self.assertEqual(hits[0]["tick"], 1)
            self.assertGreaterEqual(hits[1]["tick"], 91, "bất tử đặt ở t=1, hit lại sớm nhất từ t + 90")
            d = hits[0]["data"]
            self.assertEqual((hits[0]["tick"], d["monster_id"], d["hp"]), (1, "M1", 2))
            self.assertEqual([i["id"] for i in d["lost"]], ["I3"])
            s1 = snap_at(rows, 1)
            self.assertEqual(s1["player"]["invuln_ticks"], 90)
            self.assertEqual((s1["monsters"][0]["state"], s1["monsters"][0]["state_ticks_left"]), ("recoil", 60))
            self.assertEqual(s1["monsters"][0]["recoil_dir"], [1.0, 0.0], "trùng tâm dùng +x")
            self.assertEqual(snap_at(rows, 61)["monsters"][0]["state"], "patrol")

    def test_monster_faint_drops_all(self):
        with Workdir() as w:
            m = {"id": "M1", "kind": "ca_sau", "pos": [50, 20], "waypoints": [[50, 20], [54, 20]]}
            sc = {"gather": {"random_fish": False, "monsters": [m], "player": {"pos": [50, 20], "hp": 1},
                             "hold": items("ca_loc", "bong_sung")}}
            rows = run(w, "gather", sc, ticks=5)
            self.assertEqual([e["name"] for e in events(rows)], ["monster_hit", "faint", "gather_end"])
            f = events(rows, "faint")[0]["data"]
            self.assertEqual((f["cause"], [i["id"] for i in f["lost"]]), ("monster", ["I1"]))

    def test_no_hit_in_shallow_water(self):
        with Workdir() as w:
            m = {"id": "M1", "kind": "ca_sau", "pos": [50, 10], "waypoints": [[50, 10], [54, 10]]}
            sc = {"gather": {"random_fish": False, "monsters": [m], "player": {"pos": [50, 9]}}}
            rows = run(w, "gather", sc, ticks=30)
            self.assertEqual(events(rows, "monster_hit"), [])

    def test_patrol_and_chase(self):
        with Workdir() as w:
            m = {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}
            rows = run(w, "gather", {"gather": {"random_fish": False, "monsters": [m]}}, ticks=60, every=60)
            self.assertAlmostEqual(snap_at(rows, 60)["monsters"][0]["pos"][0], 61.0, delta=1e-3)
            sc = {"gather": {"random_fish": False, "monsters": [m], "player": {"pos": [52, 24], "oxygen_ticks": 1800}}}
            rows = run(w, "gather", sc, ticks=1)
            mon = snap_at(rows, 1)["monsters"][0]
            self.assertEqual(mon["state"], "chase")
            self.assertAlmostEqual(mon["pos"][0], 60 - 3 / 60, delta=1e-3)

    def test_m2_from_day_3_only_in_layout(self):
        with Workdir() as w:
            rows = run(w, "gather", None, ticks=0)
            self.assertEqual([m["id"] for m in snap_at(rows, 0)["monsters"]], ["M1"])


class DayLoop(unittest.TestCase):
    def test_day_start_events_and_plan(self):
        with Workdir() as w:
            rows = run(w, "day", None, ticks=0)
            first = [r for r in rows if r["type"] == "event"]
            self.assertEqual([e["name"] for e in first], ["day_start", "day_plan", "phase_start"])
            self.assertEqual(first[1], {"type": "event", "tick": 0, "phase": "gather", "day": 1, "name": "day_plan",
                                        "data": {"dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
                                                 "ingredients": {"ca_loc": 3, "bong_sung": 6}}})
            s0 = snapshots(rows)[0]
            self.assertEqual((s0["mode"], s0["phase"], s0["day"], s0["upgrades"], s0["active_upgrades"]),
                             ("day", "gather", 1, {}, {}))

    def test_handover_shop_buy_and_next_day_upgrade(self):
        with Workdir() as w:
            sc = {"day": {"money": 300, "earned": 300},
                  "gather": {"hold": items("ca_loc", "bong_sung", "bong_sung"), "random_fish": False}}
            dur = 10800
            inp = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                   {"tick": 2 + dur, "buy": "oxygen"}, {"tick": 3 + dur, "buy": "oxygen"},
                   {"tick": 4 + dur, "shop_done": True}]
            rows = run(w, "day", sc, inp, ticks=dur + 6, every=1000, extra=("--days", "2"))
            ps = [(e["tick"], e["phase"]) for e in events(rows, "phase_start")]
            self.assertEqual(ps[:3], [(0, "gather"), (1, "quan"), (1 + dur, "shop")])
            q0 = snap_at(rows, 1)
            self.assertEqual((q0["phase"], q0["phase_tick"]), ("quan", 0))
            self.assertEqual([i["id"] for i in q0["stock"]], ["I1", "I2", "I3"])
            self.assertAlmostEqual(q0["stock"][0]["fresh"], 100 - 1 / 120, delta=0.01)
            bought = events(rows, "bought")[0]["data"]
            self.assertEqual(bought, {"upgrade": "oxygen", "level": 1, "price": 200, "money": bought["money"]})
            failed = events(rows, "buy_failed")[0]["data"]
            self.assertEqual(failed, {"action": "oxygen", "reason": "funds"})
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})
            ds = events(rows, "day_start")
            self.assertEqual([e["day"] for e in ds], [1, 2])
            s = snap_at(rows, 5 + dur)
            self.assertEqual((s["day"], s["phase"], s["active_upgrades"]), (2, "gather", {"oxygen": 1}))
            self.assertEqual(s["player"]["oxygen_max_ticks"], 2700)
            self.assertEqual(s["hold"][0]["id"], "I4", "id cá thể tăng tiếp xuyên Ngày")

    def test_shop_auto_close_and_days_complete(self):
        with Workdir() as w:
            inp = [{"tick": 0, "interact": True}]
            rows = run(w, "day", {"gather": {"random_fish": False}}, inp, ticks=12000, every=5000)
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "time"})
            end = rows[-1]
            self.assertEqual((end["reason"], end["days_completed"]), ("days_complete", 1))
            self.assertEqual(end["ticks"], 1 + 10800 + 600)

    def test_pause_freezes_sim_tick(self):
        with Workdir() as w:
            inp = [{"tick": 2, "pause": True}, {"tick": 3, "pause": False}, {"tick": 6, "pause": True}]
            rows = run(w, "gather", {"gather": QUIET}, inp, ticks=8)
            self.assertEqual([(e["tick"], e["name"]) for e in events(rows) if e["name"] in ("paused", "resumed")],
                             [(3, "paused"), (7, "resumed")])
            s5 = snap_at(rows, 5)
            self.assertEqual((s5["state"], s5["sim_tick"], s5["time_left_ticks"]), ("paused", 2, 10800 - 2))
            self.assertEqual(snap_at(rows, 7)["sim_tick"], 3)

    def test_bad_day_inputs_exit_2(self):
        with Workdir() as w:
            run(w, "day", None, ticks=0, extra=("--days", "6"), expect=2)
            run(w, "gather", None, ticks=0, extra=("--days", "2"), expect=2)
            run(w, "day", {"quan": {"stock": []}}, ticks=0, expect=2)
            run(w, "day", {"day": {"money": 10, "earned": 5}}, ticks=0, expect=2)
            run(w, "day", {"day": {"day_plan": [{"day": 1, "dishes": {"goi_bong_sung": 1},
                                                 "ingredients": {"bong_sung": 3}}]}}, ticks=0, expect=2)

    def test_day_plan_menu_filter(self):
        with Workdir() as w:
            sc = {"gather": {"hold": items("ca_keo", "ca_keo", "ca_loc"), "random_fish": False}}
            rows = run(w, "day", sc, [{"tick": 0, "interact": True}], ticks=130, every=1000)
            arr = events(rows, "customer_arrived")
            self.assertEqual(arr[0]["data"]["dish_id"], "ca_loc_nuong_trui", "ngày 1 không có cá kèo nướng")
            self.assertEqual(arr[0]["day"], 1)


class Determinism(unittest.TestCase):
    def test_day_same_seed_same_bytes(self):
        with Workdir() as w:
            outs = []
            for i in (1, 2):
                code, err = run_headless("--mode", "day", "--seed", "7", "--ticks", "3000", "--out", w.path(f"d{i}.jsonl"))
                self.assertEqual(code, 0, err)
                with open(w.path(f"d{i}.jsonl"), "rb") as f:
                    outs.append(f.read())
            self.assertEqual(outs[0], outs[1])


if __name__ == "__main__":
    unittest.main()
