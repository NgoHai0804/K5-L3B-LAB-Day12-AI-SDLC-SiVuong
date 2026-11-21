"""Unit test luật Phase 2 — Lát 1 (Hải): số chuẩn v1.1 + cá bơi/sinh (AC-P2-01, AC-P2-02).

Chạy: python -m unittest discover -s tests -v
"""

import json
import os
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_gather(w, scenario, ticks, seed=1, fr=None):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    args = ["--mode", "gather", "--seed", str(seed), "--ticks", str(ticks),
            "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl")]
    if fr is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*fr))]
    code, err = run_headless(*args)
    assert code == 0, f"thoát {code}: {err}"
    return read_jsonl(w.path("o.jsonl"))


class TuningV11(unittest.TestCase):
    """AC-P2-01: tuning chuẩn v1.1."""

    def setUp(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            self.g = json.load(f)["tuning"]["gather"]
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            self.c = json.load(f)

    def test_contract_version_va_fish_yield_ba_loai(self):
        self.assertEqual(self.c["contract_version"], "1.1")
        self.assertEqual(self.g["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})

    def test_sau_nut_gom_hai_nut_keo_neo(self):
        kinds = sorted(n["kind"] for n in self.g["nodes"])
        self.assertEqual(kinds.count("keo_neo"), 2)
        self.assertEqual(len(self.g["nodes"]), 6)

    def test_dau_ca_tam_dan(self):
        self.assertEqual(len(self.g["fish_initial"]), self.g["fish_spawn"]["initial"])


class FishSwim(unittest.TestCase):
    """AC-P2-02: cá bơi 1.5 m/s theo dải độ sâu, phản xạ mép."""

    def test_01_ca_boi_dich_chuyen(self):
        sc = {"player": {"pos": [2, 0]}, "nodes": [],
              "fish": [{"id": "F1", "kind": "ca_loc", "pos": [50, 15], "heading_deg": 0}]}
        with Workdir() as w:
            rows = run_gather(w, sc, ticks=10)
            f = snapshots(rows)[-1]["fish"][0]
            self.assertGreater(f["pos"][0], 50.0)   # bơi về +x (heading 0)
            self.assertEqual(f["pos"][1], 15)       # không đổi độ sâu

    def test_02_phan_xa_o_mep_x(self):
        sc = {"player": {"pos": [2, 0]}, "nodes": [],
              "fish": [{"id": "F1", "kind": "ca_loc", "pos": [95, 15], "heading_deg": 0}]}
        with Workdir() as w:
            rows = run_gather(w, sc, ticks=60)
            xs = [s["fish"][0]["pos"][0] for s in snapshots(rows)]
            self.assertTrue(all(4 <= x <= 96 for x in xs), xs)
            self.assertLess(snapshots(rows)[-1]["fish"][0]["pos"][0], 96.0)  # đã phản xạ về

    def test_03_giu_trong_dai_do_sau(self):
        sc = {"player": {"pos": [2, 0]}, "nodes": [],
              "fish": [{"id": "F1", "kind": "ca_loc", "pos": [50, 19.5], "heading_deg": 90}]}
        with Workdir() as w:
            rows = run_gather(w, sc, ticks=60)
            ds = [s["fish"][0]["pos"][1] for s in snapshots(rows)]
            self.assertTrue(all(8 <= d <= 20 for d in ds), ds)  # dải ca_loc [8,20]

    def test_04_doi_huong_theo_buoc_120(self):
        sc = {"player": {"pos": [2, 0]}, "nodes": [],
              "fish": [{"id": "F1", "kind": "ca_loc", "pos": [50, 15], "heading_deg": 0}]}
        with Workdir() as w:
            rows = run_gather(w, sc, ticks=121)
            snap = snapshots(rows)
            self.assertEqual(snap[119]["fish"][0]["heading_deg"], 0.0)   # chưa tới bước 120
            self.assertNotEqual(snap[120]["fish"][0]["heading_deg"], 0.0)  # bước 120 đổi hướng theo seed
            self.assertEqual(snap[120]["fish"][0]["heading_deg"],
                             snap[121 if len(snap) > 121 else 120]["fish"][0]["heading_deg"])


class FishSpawn(unittest.TestCase):
    """AC-P2-02: đầu ca 8 đàn, trần 12, sinh ≤1 mỗi 360 tick."""

    SC = {"player": {"pos": [2, 0]}, "nodes": []}

    def test_01_dau_ca_tam_dan(self):
        with Workdir() as w:
            rows = run_gather(w, self.SC, ticks=1)
            self.assertEqual(len(snapshots(rows)[0]["fish"]), 8)

    def test_02_sinh_them_o_tick_360(self):
        with Workdir() as w:
            rows = run_gather(w, self.SC, ticks=361)
            self.assertEqual(len(snapshots(rows)[359]["fish"]), 8)
            self.assertEqual(len(snapshots(rows)[360]["fish"]), 9)

    def test_03_ton_trong_tran_12(self):
        with Workdir() as w:
            rows = run_gather(w, self.SC, ticks=2160)
            self.assertLessEqual(len(snapshots(rows)[-1]["fish"]), 12)
            self.assertEqual(len(snapshots(rows)[-1]["fish"]), 12)

    def test_04_random_fish_false_tat_sinh(self):
        sc = dict(self.SC, random_fish=False)
        with Workdir() as w:
            self.assertEqual(len(snapshots(run_gather(w, sc, ticks=361))[-1]["fish"]), 0)


class Determinism(unittest.TestCase):
    def test_cung_seed_giong_tung_byte(self):
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [1, 1]}))
            for i in (1, 2):
                code, err = run_headless("--mode", "gather", "--seed", "9", "--ticks", "800",
                                         "--inputs", inp, "--out", w.path(f"o{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
