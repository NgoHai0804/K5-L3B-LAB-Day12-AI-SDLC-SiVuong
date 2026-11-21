"""Unit test luật Lát 1 (Hải) — buổi sáng: oxy, biên mặt nước, ngạt, ngất, giỏ (AC-P1-02..04).

Hộp đen qua `headless_cmd` cho phần chạy được end-to-end; white-box cho seam giỏ `_try_hold`.
Chạy: python -m unittest discover -s tests -v
"""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def gather_scenario(tmp, block):
    return write_json(tmp.path("sc.json"), {"gather": block})


class Oxygen(unittest.TestCase):
    def test_01_oxy_drains_underwater_and_emits_empty_once(self):
        """Dưới nước oxy −1/tick; `oxygen_empty` chỉ khi từ dương xuống 0 (AC-P1-02)."""
        with Workdir() as w:
            sc = gather_scenario(w, {"player": {"pos": [50, 10], "oxygen_ticks": 2}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "4",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            empty = events(rows, "oxygen_empty")
            self.assertEqual(len(empty), 1, empty)
            self.assertEqual(empty[0]["tick"], 2)
            self.assertEqual(snapshots(rows)[-1]["player"]["oxygen_ticks"], 0)

    def test_02_oxy_refills_at_surface_and_clamps(self):
        """Ở mặt nước hồi `oxygen_refill_per_tick` mỗi tick, kẹp [0, oxygen_max] (AC-P1-02)."""
        g = load_contract()["tuning"]["gather"]
        with Workdir() as w:
            sc = gather_scenario(w, {"player": {"pos": [50, 0], "oxygen_ticks": 10}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            p = snapshots(read_jsonl(w.path("o.jsonl")))[-1]["player"]
            self.assertEqual(p["oxygen_ticks"], 10 + int(g["oxygen_refill_per_tick"]))
            self.assertEqual(p["zero_oxy_ticks"], 0)


class SurfaceBoundary(unittest.TestCase):
    def test_03_dive_when_crossing_down(self):
        with Workdir() as w:
            sc = gather_scenario(w, {"player": {"pos": [50, 0.2]}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, 1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "20",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            dives = events(read_jsonl(w.path("o.jsonl")), "dive")
            self.assertEqual(len(dives), 1, dives)
            self.assertIn("pos", dives[0]["data"])

    def test_03_surface_when_crossing_up(self):
        with Workdir() as w:
            sc = gather_scenario(w, {"player": {"pos": [50, 2]}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "120",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(read_jsonl(w.path("o.jsonl")), "surface")), 1)


class Choke(unittest.TestCase):
    def test_04_choke_at_sixtieth_underwater_zero_oxy_tick(self):
        """Chạm oxy 0 ở tick 1 và ở dưới nước liên tục ⇒ ngạt đầu ở tick 60 (1 + 59), −1 Máu (AC-P1-03)."""
        with Workdir() as w:
            sc = gather_scenario(w, {"player": {"pos": [50, 10], "oxygen_ticks": 1, "hp": 3}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "60",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            chokes = events(rows, "choke")
            self.assertEqual(len(chokes), 1, chokes)
            self.assertEqual(chokes[0]["tick"], 60)
            self.assertEqual(chokes[0]["data"]["hp"], 2)
            self.assertEqual(snapshots(rows)[-1]["player"]["hp"], 2)

    def test_04_surfacing_at_choke_step_avoids_choke(self):
        """Nổi lên đúng bước đáng ngạt ⇒ hồi oxy, reset đếm, KHÔNG ngạt (AC-P1-03)."""
        with Workdir() as w:
            sc = gather_scenario(w, {"player": {"pos": [50, 0.51], "oxygen_ticks": 0,
                                                "zero_oxy_ticks": 59, "hp": 3}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, -1]}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "choke"), [])
            self.assertEqual(len(events(rows, "surface")), 1)
            self.assertEqual(snapshots(rows)[-1]["player"]["hp"], 3)


class FaintAndHold(unittest.TestCase):
    def test_05_faint_drops_hold_lifo_and_writes_empty_inventory(self):
        """Máu 0 ⇒ `faint` (cause choke, lost LIFO, hp 0) → `gather_end` fainted, kho rỗng (AC-P1-03/04)."""
        with Workdir() as w:
            sc = gather_scenario(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0,
                                                "zero_oxy_ticks": 59, "hp": 1},
                                     "hold": ["ca_loc", "bong_sung", "bong_sung"]})
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inventory-out", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual(events(rows, "choke")[0]["tick"], 1)
            faint = events(rows, "faint")
            self.assertEqual(len(faint), 1, faint)
            self.assertEqual(faint[0]["data"]["cause"], "choke")
            self.assertEqual(faint[0]["data"]["lost"], ["bong_sung", "bong_sung", "ca_loc"])
            self.assertEqual(faint[0]["data"]["hp"], 0)
            end = events(rows, "gather_end")[0]["data"]
            self.assertEqual(end["reason"], "fainted")
            self.assertEqual(end["inventory"], {"items": {}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class HoldSeam(unittest.TestCase):
    def _sim(self, hold):
        return GatherSim(load_contract()["tuning"], {"hold": list(hold)}, Streams(1), IdAllocator())

    def test_06_try_hold_reports_full_with_free_and_required(self):
        cap = load_contract()["tuning"]["gather"]["hold_capacity"]
        sim = self._sim(["ca_loc"] * cap)
        ev = []
        self.assertFalse(sim._try_hold("gather", "N3", ["bong_sung"], ev))
        self.assertEqual(ev, [("hold_full", {"action": "gather", "node_id": "N3",
                                             "required": 1, "free": 0})])

    def test_06_try_hold_appends_in_order(self):
        sim = self._sim(["ca_loc"])
        ev = []
        self.assertTrue(sim._try_hold("catch", "F1", ["ca_linh", "ca_linh", "ca_linh"], ev))
        self.assertEqual(ev, [])
        self.assertEqual(sim.hold, ["ca_loc", "ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(sim._hold_free(), sim.t["hold_capacity"] - 4)


if __name__ == "__main__":
    unittest.main()
