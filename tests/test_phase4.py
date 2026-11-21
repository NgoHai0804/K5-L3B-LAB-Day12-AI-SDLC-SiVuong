"""Bộ test Phase 4 (TICKET-04 · Contract v1.3): benchmark, soak 10 ngày, leaderboard, cảnh báo & phụ đề SFX."""

import json
import os
import subprocess
import sys
import unittest

from chonoi.bench import compute_p1_low_fps
from chonoi.content import HIGH_CONTRAST_WARNINGS, sfx_subtitle_for_event
from chonoi.errors import BadInput
from chonoi.leaderboard import export_leaderboard, load_leaderboard, record_entry
from helpers import Workdir


def _run_module(mod, *args):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = subprocess.run([sys.executable, "-m", mod, *args], cwd=root, capture_output=True, text=True)
    return p.returncode, p.stderr


class TestPhase4BenchmarkAndSoak(unittest.TestCase):
    def test_p1_low_fps_exact_formula(self):
        # 100 frames: 99 khung 10ms, 1 khung chậm nhất 50ms -> k=1 -> 1/0.05 = 20.0 FPS
        frames = [0.01] * 99 + [0.05]
        self.assertEqual(compute_p1_low_fps(frames), 20.0)

    def test_bench_cli_outputs_five_required_fields(self):
        with Workdir() as w:
            out = w.path("bench.json")
            code, err = _run_module("chonoi.bench", "--seed", "42", "--duration", "0.2", "--warmup", "0", "--out", out)
            self.assertEqual(code, 0, err)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(set(data.keys()), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(data["frames"], 0)
            self.assertGreater(data["avg_fps"], 0)
            self.assertGreater(data["p1_low_fps"], 0)

    def test_soak_10_days_deterministic_and_zero_crashes(self):
        with Workdir() as w:
            s1, s2 = w.path("soak1.json"), w.path("soak2.json")
            for out in (s1, s2):
                code, err = _run_module("chonoi.soak", "--seed", "7", "--days", "10", "--out", out)
                self.assertEqual(code, 0, err)
            with open(s1, encoding="utf-8") as f1, open(s2, encoding="utf-8") as f2:
                d1, d2 = json.load(f1), json.load(f2)
            self.assertEqual(d1["days"], 10)
            self.assertEqual(d1["days_completed"], 10)
            self.assertEqual(d1["crashes"], 0)
            self.assertEqual(len(d1["results"]), 10)
            # So tính lặp ở các trường gameplay (bỏ duration_s thực tế)
            self.assertEqual(d1["results"], d2["results"])


class TestPhase4LeaderboardAndAccessibility(unittest.TestCase):
    def test_leaderboard_top10_and_stable_tie_order_across_reload(self):
        with Workdir() as w:
            store = w.path("lb.json")
            out = w.path("export.json")
            record_entry(store, "Út Sen", 300, 5, 42)
            record_entry(store, "Má Tư", 300, 5, 7)  # hòa 300 -> Út Sen ghi trước phải đứng trước
            record_entry(store, "Chú Sáu", 500, 5, 1)
            for i in range(10):
                record_entry(store, f"Khách {i}", 100 + i, 5, i)

            reloaded = load_leaderboard(store)
            self.assertEqual(len(reloaded), 10)
            self.assertEqual([e["name"] for e in reloaded[:3]], ["Chú Sáu", "Út Sen", "Má Tư"])

            export_leaderboard(out, store)
            with open(out, encoding="utf-8") as f:
                exported = json.load(f)
            self.assertEqual(exported["entries"][0]["name"], "Chú Sáu")

            with self.assertRaises(BadInput):
                record_entry(store, "   ", 100, 5, 1)

    def test_high_contrast_warnings_and_sfx_subtitles(self):
        self.assertEqual(set(HIGH_CONTRAST_WARNINGS.keys()), {"monster_near", "oxygen_low", "customer_angry"})
        for w in HIGH_CONTRAST_WARNINGS.values():
            self.assertTrue(w["icon"] and w["text"])
        self.assertIn("tiền boa", sfx_subtitle_for_event("paid", {"tip": 12}))
        self.assertIsNotNone(sfx_subtitle_for_event("oxygen_empty"))
        self.assertIsNotNone(sfx_subtitle_for_event("dish_ready"))


if __name__ == "__main__":
    unittest.main()
