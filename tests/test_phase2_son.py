"""AC-P2-10..12: manifest, pause, CLI/scenario seams.

Bản gốc (từ `origin/main`) viết cho Contract v1.1 và API cũ. Khi gộp vào `main` (v1.3), các điểm
đã đổi hợp lệ được cập nhật lại và ghi lý do:
  - `contract_version` giờ là v1.3;
  - `--days` là **tuỳ chọn** (mặc định 1) — kiểm giá trị sai vẫn thoát 2 TRƯỚC khi ghi;
  - nút `attack`/`photo` chỉ hợp lệ khi bật mở rộng tương ứng;
  - `buy` khi nạp inputs phải là **chuỗi khác rỗng** (lệnh lạ bị Shop từ chối, không phải lúc nạp);
  - trong `day`, `quan.stock`/`quan.reputation` **bị cấm** (dùng `gather.hold`);
  - đặt lệnh mua ở bản chơi qua `LiveInputs.buy()`.
"""

import os
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.headless import main as headless_main
from chonoi.inputs import InputPlayer, LiveInputs, load_frames
from chonoi.runner import Session
from chonoi.scenario import load_scenario

from helpers import Workdir, frames, write_json


class Manifest(unittest.TestCase):
    def test_declares_day_buttons_commands_and_snapshots(self):
        contract = load_contract()
        self.assertEqual(contract["contract_version"], "1.3")
        self.assertEqual(contract["modes"], ["gather", "quan", "day"])
        self.assertIn("state", contract["snapshot_contract"]["common"])  # pause biểu diễn qua `state`, không có trường `paused`
        self.assertEqual(contract["input_contract"]["commands"]["buy"], ["oxygen", "hp"])

    def test_buttons_are_edges_and_buy_is_frame_only(self):
        with Workdir() as w:
            path = write_json(w.path("inputs.json"), frames(
                {"tick": 0, "pause": True, "buy": "oxygen"},
                {"tick": 1},
                {"tick": 2, "catch": True},
            ))
            player = InputPlayer(load_frames(path))
            first = player.advance(0)
            self.assertTrue(first.pressed("pause"))
            self.assertEqual(first.buy, "oxygen")
            second = player.advance(1)
            self.assertFalse(second.pressed("pause"))
            self.assertIsNone(second.buy)
            self.assertTrue(player.advance(2).pressed("catch"))

    def test_buy_must_be_nonempty_string(self):
        with Workdir() as w:
            for bad in ("", 5, None):
                path = write_json(w.path("inputs.json"), frames({"tick": 0, "buy": bad}))
                with self.assertRaises(BadInput):
                    load_frames(path)

    def test_extension_button_rejected_when_disabled(self):
        with Workdir() as w:
            path = write_json(w.path("inputs.json"), frames({"tick": 0, "attack": True}))
            with self.assertRaises(BadInput):  # mở rộng Lao chưa bật
                load_frames(path)


class DayCli(unittest.TestCase):
    def test_day_scenario_rejects_stock_and_unknown(self):
        tuning = load_contract()["tuning"]
        with Workdir() as w:
            good = write_json(w.path("good.json"), {"day": {"reputation": 3.0}})
            self.assertEqual(load_scenario(good, "day", tuning)["day"], {"reputation": 3.0})
            conflict = write_json(w.path("sc.json"), {"quan": {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}})
            with self.assertRaises(BadInput):
                load_scenario(conflict, "day", tuning)
            bad = write_json(w.path("bad.json"), {"day": {"clock": 1}})
            with self.assertRaises(BadInput):
                load_scenario(bad, "day", tuning)

    def test_days_optional_and_invalid_validated_before_output(self):
        with Workdir() as w:
            out = w.path("out.jsonl")
            self.assertEqual(headless_main(["--mode", "day", "--days", "0", "--seed", "1", "--ticks", "0", "--out", out]), 2)
            self.assertFalse(os.path.exists(out))
            self.assertEqual(headless_main(["--mode", "day", "--seed", "1", "--ticks", "0", "--out", out]), 0)
            self.assertTrue(os.path.exists(out))

    def test_days_passed_to_runner(self):
        with Workdir() as w, patch("chonoi.headless.run") as run:
            out = w.path("out.jsonl")
            code = headless_main(["--mode", "day", "--days", "2", "--seed", "1", "--ticks", "0", "--out", out])
            self.assertEqual(code, 0)
            self.assertEqual(run.call_args.kwargs["days"], 2)

    def test_inventory_flags_are_rejected_for_day(self):
        with Workdir() as w:
            code = headless_main([
                "--mode", "day", "--days", "1", "--seed", "1", "--ticks", "0",
                "--out", w.path("out.jsonl"), "--inventory", w.path("stock.json"),
            ])
            self.assertEqual(code, 2)


class Pause(unittest.TestCase):
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

    def test_live_input_buy_via_buy_method(self):
        live = LiveInputs()
        live.set(pause=True)
        live.buy("hp")
        live.set(pause=False)
        state = live.advance()
        self.assertTrue(state.pressed("pause"))
        self.assertEqual(state.buy, "hp")
        self.assertIsNone(live.advance().buy)


if __name__ == "__main__":
    unittest.main()
