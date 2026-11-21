"""Test bản chơi (chonoi.play): chạy đúng DaySim; menu -> intro -> sáng -> tối -> kết quả -> Shop -> Ngày kế -> tổng kết.
Kiểm phần sáng tạo không phá contract: tuning đồ nghề vẫn hợp lệ, sprint chỉ có ở bản chơi."""

import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.play import GEAR, MAX_DAYS, CampaignGame, day_tuning


def run_until(g, stage, limit=30000):
    for _ in range(limit):
        if g.stage == stage:
            return
        g._tick_once()
    raise AssertionError(f"không tới {stage}, đang ở {g.stage}")


def finish_gather(g):
    g.inputs.set(interact=True)  # đứng sẵn ở bến
    g._tick_once()
    g.inputs.set(interact=False)


def finish_quan(g):
    g.session.sim.sub.time_left_ticks = 1
    g._tick_once()


class CampaignTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_title_intro_gather_quan_shop_next_day(self):
        g = CampaignGame(self.tuning, 1, self.tmp.name)
        self.assertEqual(g.stage, "title")
        g._tick_once()
        self.assertEqual(g.session.tick, 0, "màn tiêu đề không chạy sim")
        g.next_stage()
        self.assertEqual(g.stage, "dayintro")
        run_until(g, "gather")  # tự chuyển sau 4 s
        self.assertEqual(g.session.tick, 0)
        g.session.sim.sub.hold = [{"id": "I1", "kind": "ca_loc", "fresh": 100}]
        finish_gather(g)
        self.assertEqual(g.stage, "eveningintro")
        self.assertEqual([i["id"] for i in g.session.snapshot()["stock"]], ["I1"])
        g.next_stage()
        self.assertEqual(g.stage, "quan")
        finish_quan(g)
        self.assertEqual(g.stage, "dayresult")
        self.assertEqual(len(g.history), 1)
        g.next_stage()
        self.assertEqual(g.stage, "shop")
        g.next_stage()  # đóng Shop qua shop_done của sim
        g._tick_once()
        self.assertEqual((g.stage, g.session.sim.day), ("dayintro", 2))
        with open(os.path.join(self.tmp.name, "campaign.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["day"], 2)

    def test_core_buy_goes_through_sim_and_gear_changes_next_day(self):
        g = CampaignGame(self.tuning, 2, self.tmp.name)
        g.next_stage(); g.next_stage()
        finish_gather(g); g.next_stage(); finish_quan(g); g.next_stage()
        self.assertEqual(g.stage, "shop")
        g.session.sim.money = 1000
        g.session.sim.earned = 1000
        self.assertTrue(g.buy("oxygen"))
        g._tick_once()
        self.assertEqual(g.session.sim.upgrades, {"oxygen": 1})
        self.assertTrue(g.buy("gio"))
        self.assertEqual(g.session.sim.money, 1000 - 200 - GEAR["gio"][2][0])
        g.next_stage(); g._tick_once()
        g.next_stage()
        gs = g.session.sim.sub
        self.assertEqual(gs.oxygen_max, 2700)
        self.assertEqual(gs.t["hold_capacity"], self.tuning["gather"]["hold_capacity"] + 4)

    def test_full_season_reaches_ending_and_resume(self):
        g = CampaignGame(self.tuning, 3, self.tmp.name)
        g.next_stage()
        for day in range(1, MAX_DAYS + 1):
            self.assertEqual((g.stage, g.session.sim.day), ("dayintro", day))
            g.next_stage(); finish_gather(g); g.next_stage(); finish_quan(g); g.next_stage()
            g.next_stage(); g._tick_once()
            if day == 2:
                g2 = CampaignGame(self.tuning, 3, self.tmp.name)
                self.assertTrue(g2.saved)
                g2.next_stage()
                self.assertEqual((g2.stage, g2.session.sim.day), ("dayintro", 3))
        self.assertEqual(g.stage, "ending")
        self.assertEqual(len(g.history), MAX_DAYS)
        g.next_stage()
        self.assertEqual(g.stage, "title")

    def test_pause_freezes_timers(self):
        g = CampaignGame(self.tuning, 4, self.tmp.name)
        g.next_stage(); g.next_stage()
        t0 = g.session.sim.time_left_ticks
        g.inputs.press("pause"); g._tick_once()
        for _ in range(30):
            g._tick_once()
        self.assertEqual(g.session.sim.time_left_ticks, t0)
        self.assertEqual(json.loads(g.state_json())["state"], "paused")
        g.inputs.press("pause"); g._tick_once()
        self.assertEqual(g.session.sim.time_left_ticks, t0 - 1)

    def test_sprint_faster_costs_more_oxygen_and_stamina(self):
        g = CampaignGame(self.tuning, 5, self.tmp.name)
        g.next_stage(); g.next_stage()
        gs = g.session.sim.sub
        gs.pos = [30.0, 10.0]
        g.inputs.set(move=[1, 0], sprint=True)
        for _ in range(60):
            g._tick_once()
        self.assertTrue(gs.sprinting)
        self.assertAlmostEqual(gs.pos[0] - 30, 6.0 * (60 - 3.5) / 60, delta=0.6)  # ≈ 6 m/s sau ramp
        self.assertEqual(gs.oxygen_max - gs.oxygen_ticks, 90, "oxy tốn ×1.5")
        self.assertLess(gs.stamina, gs.sprint_cfg["stamina_max"])
        for _ in range(200):
            g._tick_once()
        self.assertTrue(gs.exhausted, "hết thể lực thì ngừng sprint")
        self.assertFalse(gs.sprinting)

    def test_gear_tuning_valid(self):
        top = {k: len(v[2]) for k, v in GEAR.items()}
        t = day_tuning(self.tuning, 3, top)
        self.assertEqual(t["gather"]["hold_capacity"], self.tuning["gather"]["hold_capacity"] + 8)
        self.assertIs(day_tuning(self.tuning, 1, {k: 0 for k in GEAR}), self.tuning)

    def test_headless_has_no_sprint(self):
        from chonoi.runner import Session
        s = Session("gather", self.tuning, {}, 1)
        self.assertNotIn("stamina", s.snapshot()["player"])
        s.step(InputState((1.0, 0.0), {"sprint": True}, set()))
        self.assertLessEqual(abs(s.sim.vel[0]), self.tuning["gather"]["swim_speed"] + 1e-9)


if __name__ == "__main__":
    unittest.main()
