"""AC-P2-10..12: Contract v1.1, pause, CLI/scenario seams owned by Sơn."""

import os
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer, LiveInputs, load_frames
from chonoi.headless import main as headless_main
from chonoi.runner import Session
from chonoi.scenario import load_scenario

from helpers import Workdir, frames, write_json


class ContractV11(unittest.TestCase):
    def test_manifest_declares_day_buttons_commands_and_snapshots(self):
        contract = load_contract()
        self.assertEqual(contract["contract_version"], "1.1")
        self.assertEqual(contract["modes"], ["gather", "quan", "day"])
        self.assertIn("paused", contract["snapshot_contract"]["common"])
        self.assertEqual(contract["input_contract"]["commands"]["buy"], ["oxygen", "hp"])

    def test_v11_buttons_are_edges_and_buy_is_frame_only(self):
        with Workdir() as w:
            path = write_json(w.path("inputs.json"), frames(
                {"tick": 0, "pause": True, "attack": True, "buy": "oxygen"},
                {"tick": 1},
                {"tick": 2, "pause": False, "photo": True},
            ))
            player = InputPlayer(load_frames(path))
            first = player.advance(0)
            self.assertTrue(first.pressed("pause"))
            self.assertTrue(first.pressed("attack"))
            self.assertEqual(first.buy, "oxygen")
            second = player.advance(1)
            self.assertFalse(second.pressed("pause"))
            self.assertIsNone(second.buy)
            third = player.advance(2)
            self.assertTrue(third.pressed("photo"))

    def test_invalid_buy_is_rejected(self):
        with Workdir() as w:
            path = write_json(w.path("inputs.json"), frames({"tick": 0, "buy": "boat"}))
            with self.assertRaises(BadInput):
                load_frames(path)

    def test_day_scenario_accepts_fixture_fields_and_rejects_unknown(self):
        tuning = load_contract()["tuning"]
        with Workdir() as w:
            good = write_json(w.path("good.json"), {"day": {
                "day": 3, "phase": "shop", "random_fish": False,
                "upgrades": {"oxygen": 1, "hp": 2}, "stock": {"ca_loc": 1},
                "gather": {}, "quan": {}, "shop": {}
            }})
            self.assertEqual(load_scenario(good, "day", tuning)["day"], 3)
            bad = write_json(w.path("bad.json"), {"day": {"clock": 1}})
            with self.assertRaises(BadInput):
                load_scenario(bad, "day", tuning)

    def test_day_cli_requires_days_before_creating_output(self):
        with Workdir() as w:
            out = w.path("out.jsonl")
            code = headless_main(["--mode", "day", "--seed", "1", "--ticks", "0", "--out", out])
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

    def test_day_cli_passes_days_to_runner(self):
        with Workdir() as w, patch("chonoi.headless.run") as run:
            out = w.path("out.jsonl")
            code = headless_main([
                "--mode", "day", "--days", "2", "--seed", "1", "--ticks", "0", "--out", out
            ])
            self.assertEqual(code, 0)
            self.assertEqual(run.call_args.kwargs["days"], 2)

    def test_inventory_flags_are_rejected_for_day(self):
        with Workdir() as w:
            code = headless_main([
                "--mode", "day", "--days", "1", "--seed", "1", "--ticks", "0",
                "--out", w.path("out.jsonl"), "--inventory", w.path("stock.json")
            ])
            self.assertEqual(code, 2)


class PauseV11(unittest.TestCase):
    def test_pause_freezes_and_resume_runs_gameplay_same_step(self):
        tuning = load_contract()["tuning"]
        session = Session("gather", tuning, {"time_left_ticks": 30}, seed=1)
        player = InputPlayer([
            {"tick": 0, "pause": True},
            {"tick": 1, "pause": False},
            {"tick": 2, "pause": True},
        ])
        before = session.snapshot()
        self.assertEqual([r["name"] for r in session.step(player.advance(0))], ["paused"])
        session.step(player.advance(1))
        frozen = session.snapshot()
        self.assertEqual(frozen["sim_tick"], before["sim_tick"])
        self.assertEqual(frozen["phase_tick"], before["phase_tick"])
        self.assertEqual(frozen["time_left_ticks"], before["time_left_ticks"])
        rows = session.step(player.advance(2))
        after = session.snapshot()
        self.assertEqual(rows[0]["name"], "resumed")
        self.assertEqual(after["sim_tick"], before["sim_tick"] + 1)
        self.assertEqual(after["phase_tick"], before["phase_tick"] + 1)
        self.assertEqual(after["time_left_ticks"], before["time_left_ticks"] - 1)

    def test_live_input_keeps_pause_edge_and_buy_command(self):
        live = LiveInputs()
        live.set(pause=True, buy="hp")
        live.set(pause=False)
        state = live.advance()
        self.assertTrue(state.pressed("pause"))
        self.assertEqual(state.buy, "hp")
        self.assertIsNone(live.advance().buy)


if __name__ == "__main__":
    unittest.main()
