"""Test bản chơi (chonoi.play) và phần sáng tạo: chạy đúng DaySim; menu -> hội thoại -> intro -> sáng -> tối
-> kết quả -> Shop -> Ngày kế -> tổng kết. Kiểm phần sáng tạo (sprint, thả đồ, đóng quán sớm, sơ chế, va chạm,
món phụ, nhiệm vụ) chỉ bật ở bản chơi và headless không đổi."""

import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.play import EXTRA_DISHES, GEAR, MAX_DAYS, CampaignGame, day_tuning, make_quests
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.quan import QuanSim


def run_until(g, stage, limit=30000):
    for _ in range(limit):
        if g.stage == stage:
            return
        g._tick_once()
    raise AssertionError(f"không tới {stage}, đang ở {g.stage}")


def to_gather(g):
    """menu/hội thoại/intro -> sáng."""
    while g.stage in ("title", "story", "dayintro"):
        g.next_stage()


def finish_gather(g):
    g.inputs.set(interact=True)  # đứng sẵn ở bến
    g._tick_once()
    g.inputs.set(interact=False)


def finish_quan(g):
    g.session.sim.sub.time_left_ticks = 1
    g._tick_once()


def finish_day(g):
    to_gather(g)
    finish_gather(g); g.next_stage(); finish_quan(g); g.next_stage()
    g.next_stage(); g._tick_once()


def items(*kinds, fresh=100):
    return [{"id": f"I{i + 1}", "kind": k, "fresh": fresh} for i, k in enumerate(kinds)]


class CampaignTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_title_story_intro_gather_quan_shop_next_day(self):
        g = CampaignGame(self.tuning, 1, self.tmp.name)
        self.assertEqual(g.stage, "title")
        g._tick_once()
        self.assertEqual(g.session.tick, 0, "màn tiêu đề không chạy sim")
        g.next_stage()
        self.assertEqual(g.stage, "story")
        g._tick_once()
        self.assertEqual(g.session.tick, 0, "hội thoại không chạy sim")
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
        self.assertEqual((g.stage, g.session.sim.day), ("story", 2))
        with open(os.path.join(self.tmp.name, "campaign.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["day"], 2)

    def test_core_buy_goes_through_sim_and_gear_changes_next_day(self):
        g = CampaignGame(self.tuning, 2, self.tmp.name)
        to_gather(g)
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
        to_gather(g)
        gs = g.session.sim.sub
        self.assertEqual(gs.oxygen_max, 2700)
        self.assertEqual(gs.t["hold_capacity"], self.tuning["gather"]["hold_capacity"] + 4)

    def test_full_season_reaches_ending_and_resume(self):
        g = CampaignGame(self.tuning, 3, self.tmp.name)
        for day in range(1, MAX_DAYS + 1):
            self.assertEqual(g.session.sim.day, day)
            finish_day(g)
            if day == 2:
                g2 = CampaignGame(self.tuning, 3, self.tmp.name)
                self.assertTrue(g2.saved)
                g2.next_stage()
                self.assertEqual((g2.stage, g2.session.sim.day), ("story", 3))
        self.assertEqual(g.stage, "ending")
        self.assertEqual(len(g.history), MAX_DAYS)
        g.next_stage()
        self.assertEqual(g.stage, "title")

    def test_pause_freezes_timers(self):
        g = CampaignGame(self.tuning, 4, self.tmp.name)
        to_gather(g)
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
        to_gather(g)
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

    def test_drop_wrong_item(self):
        g = CampaignGame(self.tuning, 6, self.tmp.name)
        to_gather(g)
        gs = g.session.sim.sub
        gs.hold = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "keo_neo", "fresh": 100},
                   {"id": "I3", "kind": "bong_sung", "fresh": 100}]
        g.inputs.drop("I2"); g._tick_once()
        self.assertEqual([i["id"] for i in gs.hold], ["I1", "I3"])
        g.inputs.drop(True); g._tick_once()
        self.assertEqual([i["id"] for i in gs.hold], ["I1"])
        self.assertIn("dropped", [r["name"] for r in g.events])

    def test_early_close_only_when_empty(self):
        g = CampaignGame(self.tuning, 7, self.tmp.name)
        to_gather(g); finish_gather(g); g.next_stage()
        q = g.session.sim.sub
        q.customers = [{"id": "C9", "table_id": "T1", "dish_id": "goi_bong_sung", "order_tick": 0, "state": "waiting",
                        "patience_ticks_left": 3000, "eat_ticks_left": 0, "order_status": "unfulfillable",
                        "reserved": [], "base_price": None, "tip": None}]
        g.inputs.press("close_shift"); g._tick_once()
        self.assertEqual(g.stage, "quan", "còn khách thì không đóng sớm")
        q.customers = []
        g.inputs.press("close_shift"); g._tick_once()
        self.assertEqual(g.stage, "dayresult")
        self.assertEqual(q.reason, "early")

    def test_prep_minigame_speeds_cooking_once(self):
        t = day_tuning(self.tuning, 1, {k: 0 for k in GEAR})
        sc = {"player": {"pos": [2, 8]}, "stock": items("ca_loc"), "random_customers": False,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
        q = QuanSim(t, sc, Streams(1), IdAllocator(), extras={"prep": True})
        q.step(InputState((0.0, 0.0), {}, {"interact"}))
        left = q.stoves[0]["cook_ticks_left"]
        ev = q.step(InputState((0.0, 0.0), {}, set(), prep={"stove_id": "B1", "quality": 1.0}))
        self.assertIn("prep_done", [n for n, _ in ev])
        self.assertEqual(q.stoves[0]["cook_ticks_left"], left - 1 - int(360 * 0.4))
        before = q.stoves[0]["cook_ticks_left"]
        q.step(InputState((0.0, 0.0), {}, set(), prep={"stove_id": "B1", "quality": 1.0}))
        self.assertEqual(q.stoves[0]["cook_ticks_left"], before - 1, "mỗi món chỉ sơ chế một lần")

    def test_collision_blocks_counter_but_interact_still_reaches(self):
        q = QuanSim(self.tuning, {"player": {"pos": [9.0, 4.5]}, "random_customers": False}, Streams(1),
                    IdAllocator(), extras={"collide": True})
        for _ in range(120):
            q.step(InputState((0.0, 1.0), {}, set()))
        self.assertLess(q.pos[1], 6 - 0.4 - 0.25 + 1e-9, "không đi xuyên quầy T3")
        self.assertLessEqual(abs(q.pos[1] - 6), 1.5, "vẫn trong tầm tương tác")
        free = QuanSim(self.tuning, {"player": {"pos": [9.0, 4.5]}, "random_customers": False}, Streams(1), IdAllocator())
        for _ in range(120):
            free.step(InputState((0.0, 1.0), {}, set()))
        self.assertGreater(free.pos[1], 7, "headless: đi xuyên nội thất như luật lõi")

    def test_extra_dishes_offered_only_in_play(self):
        g = CampaignGame(self.tuning, 8, self.tmp.name)
        to_gather(g)
        g.session.sim.sub.hold = [{"id": "I1", "kind": "keo_neo", "fresh": 100}]
        finish_gather(g); g.next_stage()
        q = g.session.sim.sub
        self.assertIn("keo_neo_luoc", q.plan_dishes)
        for _ in range(130):
            g._tick_once()
        self.assertEqual(q.customers[0]["dish_id"], "keo_neo_luoc")
        t = day_tuning(self.tuning, 1, {k: 0 for k in GEAR})
        self.assertEqual(set(t["menu"]) - set(self.tuning["menu"]), set(EXTRA_DISHES))
        self.assertEqual(len(self.tuning["menu"]), 6, "tuning gốc (headless) không đổi")

    def test_quests_deterministic_and_rewarded(self):
        plan = self.tuning["day_plan"][0]
        self.assertEqual(make_quests(1, 1, plan), make_quests(1, 1, plan))
        g = CampaignGame(self.tuning, 9, self.tmp.name)
        to_gather(g)
        qs = g.today["quests"]
        self.assertEqual(len(qs), 3)
        for q in qs:  # giả lập xong hết
            q["done"] = True
        m0 = g.session.sim.money
        finish_gather(g); g.next_stage(); finish_quan(g)
        reward = sum(q["reward"] for q in qs)
        self.assertEqual(g.today["quest_reward"], reward)
        self.assertEqual(g.session.sim.money, m0 + reward)

    def test_gear_tuning_valid(self):
        top = {k: len(v[2]) for k, v in GEAR.items()}
        t = day_tuning(self.tuning, 3, top)
        self.assertEqual(t["gather"]["hold_capacity"], self.tuning["gather"]["hold_capacity"] + 8)

    def test_headless_has_no_creative_extras(self):
        s = Session("gather", self.tuning, {}, 1)
        self.assertNotIn("stamina", s.snapshot()["player"])
        s.step(InputState((1.0, 0.0), {"sprint": True}, set(), drop=True))
        self.assertLessEqual(abs(s.sim.vel[0]), self.tuning["gather"]["swim_speed"] + 1e-9)



if __name__ == "__main__":
    unittest.main()
