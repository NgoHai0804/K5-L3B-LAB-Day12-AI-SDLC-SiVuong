"""Bộ test Phase 2 (Test Contract v1.1) cho `chonoi/sim/quan.py` và nội dung MR-1.

Phụ trách: Nguyễn Thanh Tùng (Team Tối · Lát 4 & Content Lead)
Bao phủ:
- AC-P2-Q1: 2 bếp (B1, B2), 4 bàn (T1–T4) hoạt động song song; ưu tiên interact (dist, bếp trước bàn, id);
            nấu đồng thời trên B1 và B2 đúng thứ tự đơn reserved cũ nhất theo (order_tick, id bàn).
- AC-P2-Q2: Đủ 6 món & 6 nguyên liệu chuẩn Phase 2 (gồm canh_chua_ca_loc, ca_keo_nuong, lau_mam),
            thời gian nấu, giá và tiền boa floor(price * 0.2) chính xác.
- AC-P2-Q3: Lịch khách 120 + 900*k, chọn bàn trống id nhỏ nhất (T1 -> T2 -> T3 -> T4),
            lọc menu theo kế hoạch ngày (`allowed_dishes` D1–D5) trước khi lọc kho khả dụng,
            phát `no_dish` khi có bàn trống mà thiếu nguyên liệu.
- AC-P2-Q4: Mở rộng Cháy món (`burn_s: 20` -> 1200 tick): đúng 1200 tick vẫn bưng được;
            vượt 1200 tick (`ready_ticks == 1201`) phát `dish_burnt`, bếp về `idle`,
            thử giữ lại ngay cho đơn -> `reserved` nếu đủ kho, `unfulfillable` nếu thiếu kho.
- AC-P2-MR1: Nội dung sáng tạo cảm hứng Dave the Diver phủ đủ 6 nguyên liệu, 6 món, 3 sinh vật, 5 ngày,
             Shop và Chợ Nổi Review (hỗ trợ `dish_burnt` và `photo`), tắt mặc định ở headless.
"""

import unittest

from chonoi.content import (
    CREATURE_GUIDE,
    DAY_STORY_BRIEFS,
    DISH_LORE,
    INGREDIENT_GUIDE,
    SHOP_LORE,
    ServiceReviewTracker,
    dialogue_for_event,
    summarize_shift_review,
)
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


def _v11_tuning(burn_s=None):
    return {
        "tick_hz": 60,
        "quan": {
            "duration_s": 180,
            "bounds": {"x": [0, 16], "z": [0, 10]},
            "start_pos": [8, 5],
            "walk_speed": 4.0,
            "ramp_max_ticks": 6,
            "interact_radius": 1.5,
            "stoves": [
                {"id": "B1", "pos": [2, 8]},
                {"id": "B2", "pos": [5, 8]},
            ],
            "tables": [
                {"id": "T1", "pos": [9, 2]},
                {"id": "T2", "pos": [13, 2]},
                {"id": "T3", "pos": [9, 6]},
                {"id": "T4", "pos": [13, 6]},
            ],
            "first_customer_tick": 120,
            "customer_interval_s": 15,
            "patience_s": 60,
            "eat_s": 10,
            "burn_s": burn_s,
            "carry_limit": 1,
            "tip_rate": 0.2,
            "tip_min_patience_ratio": 0.5,
            "tip_reputation": 0.2,
            "left_reputation_delta": -0.5,
            "reputation_initial": 3.0,
            "reputation_min": 0,
            "reputation_max": 5,
        },
        "menu": {
            "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
            "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
            "lau_ca_linh_dien_dien": {"recipe": {"ca_linh": 3, "bong_dien_dien": 1}, "cook_s": 10, "price": 120},
            "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
            "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
            "lau_mam": {
                "recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1},
                "cook_s": 12,
                "price": 200,
            },
        },
        "score": {"reputation_multiplier": 100},
    }


def _idle_inp():
    return InputState((0.0, 0.0), {"interact": False, "catch": False}, set())


def _interact_inp():
    return InputState((0.0, 0.0), {"interact": True, "catch": False}, {"interact"})


class TestQuanPhase2MultiStoveMenu(unittest.TestCase):
    """AC-P2-Q1 & AC-P2-Q2: 2 bếp, 4 bàn và 6 món chuẩn Phase 2."""

    def test_two_stoves_cook_in_order_and_lau_mam_price_tip(self):
        tuning = _v11_tuning()
        scenario = {
            "player": {"pos": [2.0, 8.0]},  # đứng cạnh B1
            "stock": {
                "ca_linh": 2,
                "ca_keo": 3,
                "keo_neo": 1,
                "bong_dien_dien": 1,
            },
            "random_customers": False,
            "customers": [
                # C2 ở T2 gọi trước (order_tick=10) -> phải nấu ở B1 trước
                {
                    "id": "C2",
                    "table_id": "T2",
                    "dish_id": "lau_mam",
                    "order_tick": 10,
                    "state": "waiting",
                    "order_status": "reserved",
                },
                # C1 ở T1 gọi sau (order_tick=20) -> nấu tiếp ở B2
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_keo_nuong",
                    "order_tick": 20,
                    "state": "waiting",
                    "order_status": "reserved",
                },
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(42), IdAllocator())

        # Tick 1: tương tác B1 -> nấu C2 (lau_mam, 12s = 720 tick, giá 200)
        ev1 = sim.step(_interact_inp())
        self.assertEqual(len(ev1), 1)
        self.assertEqual(ev1[0][0], "cook_started")
        self.assertEqual(
            ev1[0][1],
            {
                "stove_id": "B1",
                "order_id": "C2",
                "dish_id": "lau_mam",
                "items": ["bong_dien_dien", "ca_keo", "ca_linh", "ca_linh", "keo_neo"],
                "base_price": 200,
            },
        )

        # Chuyển người chơi sang B2 [5, 8] và nấu tiếp C1 (ca_keo_nuong, 6s = 360 tick, giá 70)
        sim.pos = [5.0, 8.0]
        ev2 = sim.step(_interact_inp())
        self.assertEqual(ev2[0][0], "cook_started")
        self.assertEqual(ev2[0][1]["stove_id"], "B2")
        self.assertEqual(ev2[0][1]["order_id"], "C1")
        self.assertEqual(ev2[0][1]["items"], ["ca_keo", "ca_keo"])
        self.assertEqual(ev2[0][1]["base_price"], 70)
        self.assertEqual(sim.snapshot()["stock"], {})

        # Sau 360 tick: B2 chín trước; sau tổng 720 tick từ tick 1 (tức thêm 359 tick nữa): B1 chín
        ready_order = []
        for _ in range(725):
            for name, data in sim.step(_idle_inp()):
                if name == "dish_ready":
                    ready_order.append((data["stove_id"], data["order_id"]))
        self.assertEqual(ready_order, [("B2", "C1"), ("B1", "C2")])

        # Bưng lau_mam từ B1 và phục vụ T2 -> boa = floor(200 * 0.2) = 40
        sim.pos = [2.0, 8.0]
        ev_pick = sim.step(_interact_inp())
        self.assertEqual(ev_pick[0][0], "dish_picked")
        self.assertEqual(ev_pick[0][1]["dish_id"], "lau_mam")

        sim.pos = [13.0, 2.0]  # bàn T2
        ev_serve = sim.step(_interact_inp())
        self.assertEqual(ev_serve[0][0], "served")
        self.assertEqual(ev_serve[0][1]["base_price"], 200)
        self.assertEqual(ev_serve[0][1]["tip"], 40)


class TestQuanPhase2ScheduleAndDayPlan(unittest.TestCase):
    """AC-P2-Q3: Lịch khách 120 + 900*k, 4 bàn, lọc menu theo kế hoạch ngày và no_dish."""

    def test_customer_schedule_smallest_table_and_day_plan_filter(self):
        tuning = _v11_tuning()
        # Kho có đủ nguyên liệu cho cả 6 món, nhưng kế hoạch D1 chỉ cho phép ca_loc_nuong_trui và goi_bong_sung.
        scenario = {
            "stock": {
                "ca_loc": 5,
                "bong_sung": 10,
                "ca_linh": 10,
                "ca_keo": 10,
                "keo_neo": 5,
                "bong_dien_dien": 5,
            },
            "random_customers": True,
        }
        allowed_d1 = {"ca_loc_nuong_trui", "goi_bong_sung"}
        sim = QuanSim(tuning, scenario, Streams(99), IdAllocator(), allowed_dishes=allowed_d1)

        arrivals = []
        for tick in range(1, 120 + 900 * 3 + 1):
            for name, data in sim.step(_idle_inp()):
                if name == "customer_arrived":
                    arrivals.append((tick, data["table_id"], data["dish_id"]))

        self.assertEqual([t for t, _, _ in arrivals], [120, 1020, 1920, 2820])
        self.assertEqual([tb for _, tb, _ in arrivals], ["T1", "T2", "T3", "T4"])
        for _, _, dish_id in arrivals:
            self.assertIn(dish_id, allowed_d1)

    def test_no_dish_when_plan_dishes_lack_stock_even_if_other_dish_has_stock(self):
        tuning = _v11_tuning()
        # Có sẵn bong_sung×2 (đủ nấu goi_bong_sung), nhưng kế hoạch D2 chỉ gồm ca_loc_nuong_trui và lau_ca_linh_dien_dien!
        scenario = {"stock": {"bong_sung": 2}, "random_customers": True}
        allowed_d2 = {"ca_loc_nuong_trui", "lau_ca_linh_dien_dien"}
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator(), allowed_dishes=allowed_d2)

        got = []
        for _ in range(120):
            got.extend(sim.step(_idle_inp()))
        self.assertEqual(got, [("no_dish", {})])
        self.assertEqual(sim.snapshot()["customers"], [])


class TestQuanPhase2BurnExtension(unittest.TestCase):
    """AC-P2-Q4: Mở rộng Cháy món (`burn_s: 20` -> 1200 tick)."""

    def test_exact_1200_ticks_still_pickable(self):
        tuning = _v11_tuning(burn_s=20)
        scenario = {
            "player": {"pos": [2.0, 8.0]},
            "random_customers": False,
            "stoves": [
                {
                    "id": "B1",
                    "pos": [2.0, 8.0],
                    "state": "ready",
                    "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "cook_ticks_left": 0,
                    "ready_ticks": 1199,  # Sau bước 1 tăng lên đúng 1200 -> KHÔNG cháy, bưng được!
                }
            ],
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_tick": 0,
                    "state": "waiting",
                    "order_status": "assigned",
                    "reserved": {},
                }
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())
        ev = sim.step(_interact_inp())
        self.assertEqual([name for name, _ in ev], ["dish_picked"])
        self.assertIsNotNone(sim.snapshot()["hand"])

    def test_burn_at_1201_re_reserves_or_marks_unfulfillable(self):
        tuning = _v11_tuning(burn_s=20)
        # Trường hợp 1: còn đủ 1 ca_loc trong kho -> sau cháy chuyển lại reserved và giữ chỗ ngay.
        sc_ok = {
            "stock": {"ca_loc": 1},
            "random_customers": False,
            "stoves": [
                {
                    "id": "B1",
                    "pos": [2.0, 8.0],
                    "state": "ready",
                    "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "cook_ticks_left": 0,
                    "ready_ticks": 1200,  # Bước 1 tăng lên 1201 > 1200 -> CHÁY!
                }
            ],
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_tick": 0,
                    "state": "waiting",
                    "order_status": "assigned",
                    "reserved": {},
                }
            ],
        }
        sim_ok = QuanSim(tuning, sc_ok, Streams(1), IdAllocator())
        ev_ok = sim_ok.step(_idle_inp())
        self.assertEqual(
            ev_ok,
            [("dish_burnt", {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved"})],
        )
        snap_ok = sim_ok.snapshot()
        self.assertEqual(snap_ok["stoves"][0]["state"], "idle")
        self.assertEqual(snap_ok["customers"][0]["order_status"], "reserved")
        self.assertEqual(snap_ok["customers"][0]["reserved"], {"ca_loc": 1})

        # Trường hợp 2: kho rỗng -> sau cháy chuyển thành unfulfillable, khách vẫn ngồi chờ.
        sc_empty = dict(sc_ok, stock={})
        sim_empty = QuanSim(tuning, sc_empty, Streams(1), IdAllocator())
        ev_empty = sim_empty.step(_idle_inp())
        self.assertEqual(
            ev_empty,
            [("dish_burnt", {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "order_status": "unfulfillable"})],
        )
        snap_empty = sim_empty.snapshot()
        self.assertEqual(snap_empty["customers"][0]["order_status"], "unfulfillable")
        self.assertEqual(snap_empty["customers"][0]["reserved"], {})


class TestMR1Phase2DaveContent(unittest.TestCase):
    """AC-P2-MR1: Nội dung Dave the Diver phủ đủ 6 nguyên liệu, 6 món, 3 sinh vật, 5 ngày và Shop."""

    def test_phase2_guides_and_review_tracker(self):
        tuning = _v11_tuning()
        self.assertEqual(
            set(INGREDIENT_GUIDE.keys()),
            {"ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo"},
        )
        self.assertEqual(set(DISH_LORE.keys()), set(tuning["menu"].keys()))
        self.assertEqual(set(CREATURE_GUIDE.keys()), {"ca_sau", "ran", "ca_ho"})
        self.assertEqual(set(DAY_STORY_BRIEFS.keys()), {1, 2, 3, 4, 5})
        self.assertEqual(set(SHOP_LORE.keys()), {"oxygen", "hp", "weapon", "net", "vendor"})
        self.assertIsNotNone(dialogue_for_event("dish_burnt"))
        self.assertIsNotNone(dialogue_for_event("photo"))

        # Tắt mặc định cho headless
        disabled = ServiceReviewTracker()
        self.assertIsNone(disabled.observe("photo", {"id": "H1"}))
        self.assertEqual(disabled.review_likes, 0)

        # Khi bật ở client: photo (+3 likes), paid có boa (+2), dish_burnt (-1) -> tổng 4 likes (★★★☆☆)
        summary = summarize_shift_review(
            [
                {"type": "event", "name": "photo", "data": {"id": "H1"}},
                {"type": "event", "name": "paid", "data": {"tip": 40}},
                {"type": "event", "name": "dish_burnt", "data": {"stove_id": "B1"}},
            ],
            enabled=True,
        )
        self.assertEqual(summary["photos_taken"], 1)
        self.assertEqual(summary["burnt_count"], 1)
        self.assertEqual(summary["review_likes"], 4)
        self.assertEqual(summary["tier_stars"], "★★★☆☆")


if __name__ == "__main__":
    unittest.main()
