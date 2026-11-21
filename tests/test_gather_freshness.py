"""Test Phase 3 — Lát 0 (adapter kho cá thể) + Lát 1 (hao tươi giỏ, `spoiled`, LIFO) — Hải.

Lát 0: `chonoi/inventory.py` chọn schema theo `contract_version` (AC-P3-01/06).
Lát 1: `chonoi/sim/gather.py` hao tươi + `spoiled` + LIFO, gate theo v1.2 (AC-P3-02).
Chạy: python -m unittest discover -s tests -v
"""

import json
import os
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.inventory import (read_inventory, write_inventory, validate_carried,
                              fresh_to_units, units_to_fresh)
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

from helpers import Workdir, write_json


def make_sim(w, scenario, version="1.2", seed=1):
    sc = write_json(w.path("sc.json"), scenario)
    return sc, GatherSim(load_contract()["tuning"], scenario, Streams(seed), IdAllocator(), version=version)


class InventoryAdapter(unittest.TestCase):
    """AC-P3-01: chọn schema theo version; v1.2 từ chối kho đếm."""

    def test_validate_carried_hop_le(self):
        items = validate_carried([{"id": "I1", "kind": "ca_linh", "fresh": 100},
                                  {"id": "I2", "kind": "ca_loc", "fresh": 97.5}])
        self.assertEqual([i["id"] for i in items], ["I1", "I2"])

    def test_validate_carried_tu_choi_xau(self):
        for bad in ([{"id": "", "kind": "ca_linh", "fresh": 50}],
                    [{"id": "I1", "kind": "ca_linh", "fresh": 50}, {"id": "I1", "kind": "ca_loc", "fresh": 50}],
                    [{"id": "I1", "kind": "ca_map", "fresh": 50}],
                    [{"id": "I1", "kind": "ca_linh", "fresh": 101}],
                    [{"id": "I1", "kind": "ca_linh"}]):
            with self.assertRaises(Exception):
                validate_carried(bad)

    def test_read_v12_tu_choi_kho_dem(self):
        with Workdir() as w:
            p = write_json(w.path("k.json"), {"items": {"ca_loc": 1}})
            with self.assertRaises(Exception):
                read_inventory(p, version="1.2")

    def test_write_read_roundtrip_carried(self):
        with Workdir() as w:
            p = w.path("k.json")
            write_inventory(p, [{"id": "I1", "kind": "ca_linh", "fresh": 100.0},
                                {"id": "I2", "kind": "ca_loc", "fresh": 29.995}], version="1.2")
            with open(p, encoding="utf-8") as f:
                root = json.load(f)
            self.assertEqual(list(root.keys()), ["items"])
            self.assertIsInstance(root["items"], list)
            back = read_inventory(p, version="1.2")
            self.assertEqual([i["id"] for i in back], ["I1", "I2"])
            self.assertEqual(back[0]["fresh"], 100.0)

    def test_fresh_units_roundtrip_nguong_30(self):
        for f in (100.0, 30.0, 29.9958, 0.0):
            self.assertEqual(units_to_fresh(fresh_to_units(f)), fresh_to_units(f) / 240)


class GatherFreshness(unittest.TestCase):
    """AC-P3-02: hao tươi giỏ, `spoiled`, LIFO, bàn giao cá thể."""

    SC = {"player": {"pos": [2, 0]}, "nodes": [], "fish": [],
          "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}]}

    def test_hold_scenario_thanh_ca_the(self):
        with Workdir() as w:
            sc, sim = make_sim(w, self.SC)
            self.assertEqual(sim.hold[0], {"id": "I1", "kind": "ca_linh", "u": fresh_to_units(30)})
            self.assertEqual(sim.snapshot()["hold"], [{"id": "I1", "kind": "ca_linh", "fresh": 30.0}])

    def test_spoiled_o_buoc_dau(self):
        with Workdir() as w:
            _, sim = make_sim(w, self.SC)
            ev = sim.step(LiveInputs().advance())
            self.assertIn(("spoiled", {"item_id": "I1", "kind": "ca_linh", "location": "hold"}), ev)
            self.assertLess(sim.hold[0]["u"], fresh_to_units(30))  # đã tụt xuống dưới ngưỡng

    def test_hang_moi_fresh_100_va_id_moi(self):
        with Workdir() as w:
            _, sim = make_sim(w, {"player": {"pos": [2, 0]}, "nodes": [], "fish": []})
            ev = []
            self.assertTrue(sim._try_hold("catch", "F1", ["ca_linh"] * 3, ev))
            self.assertEqual([it["id"] for it in sim.hold], ["I1", "I2", "I3"])
            self.assertTrue(all(it["u"] == fresh_to_units(100) for it in sim.hold))
            self.assertEqual([it["fresh"] for it in sim.inventory_items()], [100.0, 100.0, 100.0])

    def test_hao_dung_2_don_vi_moi_tick(self):
        with Workdir() as w:
            sc = dict(self.SC, hold=[{"id": "I1", "kind": "ca_linh", "fresh": 100}])
            _, sim = make_sim(w, sc)
            for _ in range(5):
                sim.step(LiveInputs().advance())
            self.assertEqual(sim.hold[0]["u"], fresh_to_units(100) - 10)  # −2/tick × 5

    def test_lifo_khi_ngat(self):
        sc = {"player": {"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
              "nodes": [], "fish": [],
              "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100},
                       {"id": "I2", "kind": "bong_sung", "fresh": 100}]}
        with Workdir() as w:
            _, sim = make_sim(w, sc)
            ev = sim.step(LiveInputs().advance())
            faint = [d for n, d in ev if n == "faint"][0]
            self.assertEqual([it["id"] for it in faint["lost"]], ["I2", "I1"])  # nhặt sau bỏ trước
            self.assertEqual(sim.inventory_items(), [])

    def test_v11_van_dung_schema_dem(self):
        with Workdir() as w:
            sc = {"player": {"pos": [2, 0]}, "nodes": [], "fish": [], "hold": ["ca_loc", "bong_sung"]}
            _, sim = make_sim(w, sc, version="1.1")
            self.assertEqual(sim.inventory_items(), {"bong_sung": 1, "ca_loc": 1})


if __name__ == "__main__":
    unittest.main()
