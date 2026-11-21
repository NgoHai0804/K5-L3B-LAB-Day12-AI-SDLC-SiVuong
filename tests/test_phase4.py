"""Test Phase 4 (Test Contract v1.3, Ticket-04):
  - contract_version 1.3 + extensions + bench_cmd/soak_cmd, v1.2 gameplay giữ nguyên;
  - benchmark có render (`bench_cmd`) xuất đúng 5 trường;
  - soak nhiều Ngày (`soak_cmd`) đạt khi days_completed == days và crashes == 0;
  - bảng xếp hạng cục bộ: sắp/giới hạn/Unicode/xuất + cổng ghi của headless (`--leaderboard`);
  - index.html có cảnh báo người chơi + phụ đề SFX + chế độ tương phản cao.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
"""

import json
import os
import shlex
import subprocess
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.leaderboard import LIMIT, export, load, record, sort_entries, validate_name
from helpers import ROOT, Workdir, run_headless, write_json

BENCH_KEYS = {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}
SOAK_KEYS = {"days", "days_completed", "crashes", "results", "duration_s"}


def contract() -> dict:
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


def run_cmd(key, *args, cwd=ROOT):
    """Chạy lệnh khai trong game.contract.json (bench_cmd / soak_cmd); trả (mã thoát, stderr)."""
    p = subprocess.run([*shlex.split(contract()[key]), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stderr


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class ContractV13(unittest.TestCase):
    def test_version_extensions_and_commands(self):
        c = contract()
        self.assertEqual(load_contract()["contract_version"], "1.3")
        self.assertIn("bench_cmd", c)
        self.assertIn("soak_cmd", c)
        self.assertIsInstance(c.get("extensions"), list)
        self.assertIn("leaderboard", c["extensions"])
        self.assertIn("subtitles", c["extensions"])
        self.assertEqual(c["team_size"], 5)

    def test_v12_gameplay_kept(self):
        t = contract()["tuning"]
        self.assertEqual(len(t["day_plan"]), 5)
        self.assertEqual(t["gather"]["duration_s"], 180)
        self.assertEqual(len(t["menu"]), 6)
        self.assertEqual(t["shop"]["max_ticks"], 600)


class Bench(unittest.TestCase):
    def test_json_has_exactly_five_fields(self):
        with Workdir() as w:
            out = w.path("bench.json")
            code, err = run_cmd("bench_cmd", "--seed", "42", "--duration", "0.5", "--warmup", "0", "--out", out)
            self.assertEqual(code, 0, err)
            data = read_json(out)
            self.assertEqual(set(data), BENCH_KEYS)
            self.assertIsInstance(data["frames"], int)
            for k in ("avg_fps", "p1_low_fps", "measured_s", "load_ms"):
                self.assertIsInstance(data[k], (int, float))
            self.assertGreaterEqual(data["frames"], 1)
            self.assertGreater(data["avg_fps"], 0)
            self.assertGreater(data["p1_low_fps"], 0)
            self.assertGreaterEqual(data["load_ms"], 0)

    def test_bad_input_exit_2(self):
        with Workdir() as w:
            out = w.path("bench.json")
            self.assertEqual(run_cmd("bench_cmd", "--seed", "1", "--duration", "-1", "--out", out)[0], 2)
            self.assertEqual(run_cmd("bench_cmd", "--seed", "1", "--duration", "0.1", "--width", "0", "--out", out)[0], 2)
            self.assertEqual(run_cmd("bench_cmd", "--seed", "1", "--duration", "0.1")[0], 2)  # thiếu --out
            self.assertFalse(os.path.exists(out))


class Soak(unittest.TestCase):
    def test_two_days_pass(self):
        with Workdir() as w:
            out = w.path("soak.json")
            code, err = run_cmd("soak_cmd", "--seed", "7", "--days", "2", "--out", out)
            self.assertEqual(code, 0, err)
            data = read_json(out)
            self.assertEqual(set(data), SOAK_KEYS)
            self.assertEqual(data["days"], 2)
            self.assertEqual(data["days_completed"], 2)
            self.assertEqual(data["crashes"], 0)
            self.assertEqual(len(data["results"]), 2)
            for r in data["results"]:
                self.assertEqual(set(r), {"day", "earned", "reputation", "score"})
            self.assertEqual([r["day"] for r in data["results"]], [1, 2])

    def test_deterministic_results(self):
        with Workdir() as w:
            a, b = w.path("a.json"), w.path("b.json")
            self.assertEqual(run_cmd("soak_cmd", "--seed", "5", "--days", "2", "--out", a)[0], 0)
            self.assertEqual(run_cmd("soak_cmd", "--seed", "5", "--days", "2", "--out", b)[0], 0)
            self.assertEqual(read_json(a)["results"], read_json(b)["results"])

    def test_bad_days_exit_2(self):
        with Workdir() as w:
            out = w.path("soak.json")
            self.assertEqual(run_cmd("soak_cmd", "--seed", "1", "--days", "0", "--out", out)[0], 2)
            self.assertEqual(run_cmd("soak_cmd", "--seed", "1", "--days", "3")[0], 2)  # thiếu --out
            self.assertFalse(os.path.exists(out))


class LeaderboardStore(unittest.TestCase):
    def test_record_sorts_desc_and_keeps_ties_stable(self):
        with Workdir() as w:
            lb = w.path("lb.json")
            record(lb, "A", 100, 5, 1)
            record(lb, "B", 300, 5, 1)
            record(lb, "C", 300, 5, 1)  # hòa với B, ghi sau nên đứng sau
            entries = load(lb)
            self.assertEqual([e["name"] for e in entries], ["B", "C", "A"])
            self.assertEqual(entries[0]["score"], 300)

    def test_limit_ten(self):
        with Workdir() as w:
            lb = w.path("lb.json")
            for i in range(15):
                record(lb, f"P{i}", i, 5, 1)
            entries = load(lb)
            self.assertEqual(len(entries), LIMIT)
            self.assertEqual(entries[0]["score"], 14)
            self.assertEqual(entries[-1]["score"], 5)

    def test_unicode_name_and_empty_rejected(self):
        with Workdir() as w:
            lb = w.path("lb.json")
            record(lb, "Út Sen", 300, 5, 42)
            self.assertEqual(load(lb)[0]["name"], "Út Sen")
            self.assertEqual(validate_name("Út Sen"), "Út Sen")
            self.assertRaises(BadInput, validate_name, "   ")
            self.assertRaises(BadInput, record, lb, "  ", 1, 5, 1)

    def test_missing_store_is_empty_and_export_sorted(self):
        with Workdir() as w:
            self.assertEqual(load(w.path("nope.json")), [])
            src, dst = w.path("src.json"), w.path("dst.json")
            record(src, "A", 10, 5, 1)
            record(src, "B", 90, 5, 1)
            export(src, dst)
            self.assertEqual([e["name"] for e in load(dst)], ["B", "A"])
            self.assertEqual(sort_entries([{"name": "x", "score": 1, "days_completed": 5, "seed": 1},
                                           {"name": "y", "score": 9, "days_completed": 5, "seed": 1}])[0]["name"], "y")

    def test_bad_store_schema_rejected(self):
        with Workdir() as w:
            bad = write_json(w.path("bad.json"), {"scores": []})
            self.assertRaises(BadInput, load, bad)
            dup = write_json(w.path("dup.json"), {"entries": [{"name": "A", "score": 1, "days_completed": 5, "seed": 1, "x": 2}]})
            self.assertRaises(BadInput, load, dup)


class HeadlessLeaderboard(unittest.TestCase):
    def test_missing_pair_exit_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            self.assertEqual(run_headless("--mode", "day", "--days", "5", "--ticks", "0",
                                          "--leaderboard", w.path("lb.json"), "--out", out)[0], 2)
            self.assertEqual(run_headless("--mode", "day", "--days", "5", "--ticks", "0",
                                          "--player-name", "X", "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))

    def test_wrong_mode_exit_2(self):
        with Workdir() as w:
            self.assertEqual(run_headless("--mode", "gather", "--ticks", "0", "--leaderboard", w.path("lb.json"),
                                          "--player-name", "X", "--out", w.path("g.jsonl"))[0], 2)

    def test_short_run_does_not_record(self):
        with Workdir() as w:
            lb = w.path("lb.json")
            self.assertEqual(run_headless("--mode", "day", "--days", "1", "--seed", "1", "--ticks", "120000",
                                          "--snapshot-every", "600", "--leaderboard", lb, "--player-name", "X",
                                          "--out", w.path("d.jsonl"))[0], 0)
            self.assertFalse(os.path.exists(lb), "chưa đủ 5 Ngày thì không ghi bảng")

    def test_full_standard_five_days_records_once(self):
        with Workdir() as w:
            lb = w.path("lb.json")
            out = w.path("d.jsonl")
            code, err = run_headless("--mode", "day", "--days", "5", "--seed", "42", "--ticks", "200000",
                                     "--snapshot-every", "600", "--leaderboard", lb, "--player-name", "Út Sen", "--out", out)
            self.assertEqual(code, 0, err)
            entries = load(lb)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["name"], "Út Sen")
            self.assertEqual(entries[0]["days_completed"], 5)
            self.assertEqual(entries[0]["seed"], 42)
            self.assertIsInstance(entries[0]["score"], int)

    def test_scenario_disqualifies_recording(self):
        with Workdir() as w:
            lb = w.path("lb.json")
            sc = write_json(w.path("sc.json"), {"day": {"reputation": 3.0}})
            self.assertEqual(run_headless("--mode", "day", "--days", "5", "--seed", "42", "--ticks", "200000",
                                          "--snapshot-every", "600", "--scenario", sc, "--leaderboard", lb,
                                          "--player-name", "X", "--out", w.path("d.jsonl"))[0], 0)
            self.assertFalse(os.path.exists(lb), "có scenario thì không ghi bảng")


class FrontendMarkers(unittest.TestCase):
    def test_index_html_has_warnings_subtitles_and_high_contrast(self):
        with open(os.path.join(ROOT, "chonoi", "web", "index.html"), encoding="utf-8") as f:
            html = f.read()
        for token in ("KHÁCH", "SẮP GIẬN!", "THỦY QUÁI GẦN ĐÂY!", "SẮP HẾT OXY",
                      "warningBanners", "drawCaptions", "let hiC", "CAPS", "function say"):
            self.assertIn(token, html, token)


if __name__ == "__main__":
    unittest.main()
