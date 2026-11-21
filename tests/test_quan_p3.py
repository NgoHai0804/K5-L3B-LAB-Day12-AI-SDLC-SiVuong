"""Bộ test Phase 3 (TICKET-03 · Contract v1.2 — Độ tươi & Kho cá thể) cho `chonoi/sim/quan.py` và MR-1.

Phụ trách: Nguyễn Thanh Tùng (Team Tối · Lát 4 & Content Lead)
Bao phủ:
- AC-P3-01: Kho cá thể `[{id, kind, fresh}]`, hao tươi quán 0.25/s (= 1/240 mỗi tick),
            ngưỡng ươn `< 30` (so trước làm tròn), phát `spoiled` đúng 1 lần theo id, hàng ươn vẫn nằm trong kho.
- AC-P3-02: Giữ chỗ theo mảng id cá thể tươi nhất (hòa theo id nhỏ); khi phần giữ có cá thể vừa ươn,
            phát hết `spoiled` theo id rồi nhả toàn bộ phần giữ của đơn và thử giữ lại đúng 1 lần
            theo `(order_tick, id bàn)` -> `reserved` nếu đủ hoặc `unfulfillable` nếu thiếu.
- AC-P3-03: Chốt giá theo độ tươi lúc bắt đầu nấu `base_price = floor(price * avg_fresh / 100)`,
            `cook_started.data.items` là mảng cá thể sắp theo `(kind, id)`,
            boa `floor(base_price * 0.2)` áp trên giá đã chốt, món chín không hao tươi.
- AC-P3-04: Validate v1.2 (từ chối id trùng, fresh ngoài [0,100], giữ cá thể đã ươn, giữ trùng giữa 2 đơn -> BadInput),
            mở rộng `burn` hoạt động đúng với kho cá thể.
- AC-P3-MR1: Nhãn độ tươi `freshness_badge`, lời thoại `spoiled`/`current_*`/`reservation_*` và
             `ServiceReviewTracker` tắt mặc định ở headless.
"""

import unittest

from chonoi.content import (
    ServiceReviewTracker,
    dialogue_for_event,
    freshness_badge,
    summarize_shift_review,
)
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


def _v12_tuning(burn_s=None):
    return {
        "tick_hz": 60,
        "freshness": {
            "initial": 100,
            "gather_decay_per_s": 0.5,
            "quan_decay_per_s": 0.25,
            "spoiled_below": 30,
        },
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


class TestQuanPhase3FreshnessAndSpoilage(unittest.TestCase):
    """AC-P3-01 & AC-P3-02: Ngưỡng ươn 30, phát spoiled theo id và thử giữ lại đúng 1 lần."""

    def test_spoiled_emitted_once_at_threshold_30_in_id_order(self):
        tuning = _v12_tuning()
        scenario = {
            "random_customers": False,
            "stock": [
                {"id": "I10", "kind": "ca_loc", "fresh": 30},
                {"id": "I2", "kind": "ca_linh", "fresh": 30},
                {"id": "I3", "kind": "bong_sung", "fresh": 29.5},  # đã ươn sẵn -> không phát lại
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())

        # Bước 1: I2 và I10 đều từ 30 xuống 30 - 1/240 < 30 -> phát spoiled theo thứ tự id (I2 trước I10)
        ev1 = sim.step(_idle_inp())
        self.assertEqual(
            ev1,
            [
                ("spoiled", {"item_id": "I2", "kind": "ca_linh", "location": "stock"}),
                ("spoiled", {"item_id": "I10", "kind": "ca_loc", "location": "stock"}),
            ],
        )
        # Bước 2: không phát lại spoiled nữa; hàng ươn vẫn nằm trong stock
        ev2 = sim.step(_idle_inp())
        self.assertEqual(ev2, [])
        self.assertEqual([it["id"] for it in sim.snapshot()["stock"]], ["I2", "I3", "I10"])

    def test_auto_reserve_picks_freshest_then_smallest_id(self):
        tuning = _v12_tuning()
        scenario = {
            "random_customers": False,
            "stock": [
                {"id": "I1", "kind": "bong_sung", "fresh": 60},
                {"id": "I2", "kind": "bong_sung", "fresh": 90},
                {"id": "I10", "kind": "bong_sung", "fresh": 90},
                {"id": "I3", "kind": "bong_sung", "fresh": 95},
            ],
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "goi_bong_sung",  # cần 2 bong_sung -> phải chọn I3 (95) và I2 (90, hòa id nhỏ hơn I10)
                    "order_tick": 0,
                    "state": "waiting",
                    "order_status": "reserved",
                }
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I2", "I3"])

    def test_spoiled_reserved_item_releases_and_retries_once_by_order_tick_then_table(self):
        tuning = _v12_tuning()
        # C1 (order_tick=5, T2) và C2 (order_tick=10, T1) cùng giữ 1 ca_loc đang ở đúng fresh=30.
        # Trong kho chỉ còn DUY NHẤT 1 ca_loc tươi dự phòng là I9 (fresh=80).
        # Khi bước 1 chạy: I1 và I2 cùng ươn -> phát hết spoiled trước -> sau đó xử lý C1 (cũ hơn) trước:
        # C1 nhả I1 và giữ được I9 (reserved), C2 nhả I2 nhưng hết hàng tươi -> unfulfillable!
        scenario = {
            "random_customers": False,
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 30},
                {"id": "I2", "kind": "ca_loc", "fresh": 30},
                {"id": "I9", "kind": "ca_loc", "fresh": 80},
            ],
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T2",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_tick": 5,
                    "state": "waiting",
                    "order_status": "reserved",
                    "reserved": ["I1"],
                },
                {
                    "id": "C2",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_tick": 10,
                    "state": "waiting",
                    "order_status": "reserved",
                    "reserved": ["I2"],
                },
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())
        ev = sim.step(_idle_inp())
        self.assertEqual(
            ev,
            [
                ("spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "stock"}),
                ("spoiled", {"item_id": "I2", "kind": "ca_loc", "location": "stock"}),
            ],
        )
        by_id = {c["id"]: c for c in sim.snapshot()["customers"]}
        self.assertEqual(by_id["C1"]["order_status"], "reserved")
        self.assertEqual(by_id["C1"]["reserved"], ["I9"])
        self.assertEqual(by_id["C2"]["order_status"], "unfulfillable")
        self.assertEqual(by_id["C2"]["reserved"], [])


class TestQuanPhase3FreshPricingAndCooking(unittest.TestCase):
    """AC-P3-03 & AC-P3-04: Giá chốt theo độ tươi, items mảng cá thể, boa trên giá chốt, burn & validation."""

    def test_cook_started_locks_freshness_price_and_tip_uses_locked_price(self):
        tuning = _v12_tuning()
        # Đặt quan_decay_per_s = 0.25 -> sau 1 tick mỗi cá thể giảm 1/240.
        # Dùng 2 bong_sung: fresh ban đầu 90 + 1/240 và 60 + 1/240 -> đúng lúc nấu (tick 1) là 90 và 60 -> TB = 75.
        # Thay vào đó dùng fresh ban đầu = 80 và 80 (sau 1 tick: 79.995833... -> floor(40 * avg / 100) = 31)
        # Để kiểm công thức chính xác: với ca_loc_nuong_trui (giá 60), fresh ban đầu = 50 -> sau 1 tick = 49.99583...
        # 60 * (11999/240) / 100 = 29.9975 -> floor = 29; boa = floor(29 * 0.2) = 5!
        # Và kiểm trường hợp chẵn: với decay 0.25/s = 1/240/tick, chạy ở fresh 100 (giảm 1/240) -> 60 * 23999 / 24000 = 59.9975 -> floor = 59.
        # Kiểm cả 2 món có nhiều nguyên liệu: canh_chua_ca_loc (giá 90): ca_loc (I5, fresh 100) + bong_dien_dien (I2, fresh 80).
        scenario = {
            "player": {"pos": [2.0, 8.0]},
            "random_customers": False,
            "stock": [
                {"id": "I5", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "bong_dien_dien", "fresh": 80},
            ],
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "canh_chua_ca_loc",
                    "order_tick": 0,
                    "state": "waiting",
                    "order_status": "reserved",
                    "reserved": ["I2", "I5"],
                }
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())
        ev_start = sim.step(_interact_inp())
        self.assertEqual(len(ev_start), 1)
        self.assertEqual(ev_start[0][0], "cook_started")
        data = ev_start[0][1]
        # items sắp theo (kind, id): bong_dien_dien (I2) trước ca_loc (I5)
        self.assertEqual([it["id"] for it in data["items"]], ["I2", "I5"])
        self.assertEqual([it["kind"] for it in data["items"]], ["bong_dien_dien", "ca_loc"])
        # avg_fresh = ((80 - 1/240) + (100 - 1/240)) / 2 = 90 - 1/240
        # 90 * (90 - 1/240) / 100 = 81 - 90/24000 = 80.99625 -> floor = 80
        self.assertEqual(data["base_price"], 80)
        # Kho đã tiêu sạch 2 cá thể đó
        self.assertEqual(sim.snapshot()["stock"], [])

        # Chờ nấu xong 8s = 480 tick, bưng và phục vụ -> giá đã chốt giữ nguyên 80 (món chín không hao tươi),
        # boa = floor(80 * 0.2) = 16!
        for _ in range(480):
            sim.step(_idle_inp())
        ev_pick = sim.step(_interact_inp())
        self.assertEqual(ev_pick[0][0], "dish_picked")
        sim.pos = [9.0, 2.0]  # bàn T1
        ev_serve = sim.step(_interact_inp())
        self.assertEqual(ev_serve[0][0], "served")
        self.assertEqual(ev_serve[0][1]["base_price"], 80)
        self.assertEqual(ev_serve[0][1]["tip"], 16)

    def test_v12_validation_rejects_bad_stock_and_spoiled_reservation(self):
        tuning = _v12_tuning()
        # Id trùng
        with self.assertRaises(BadInput):
            QuanSim(
                tuning,
                {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 90}, {"id": "I1", "kind": "ca_loc", "fresh": 80}]},
                Streams(1),
                IdAllocator(),
            )
        # Fresh ngoài [0, 100]
        with self.assertRaises(BadInput):
            QuanSim(
                tuning,
                {"stock": [{"id": "I1", "kind": "ca_loc", "fresh": 105}]},
                Streams(1),
                IdAllocator(),
            )
        # Giữ cá thể đã ươn
        with self.assertRaises(BadInput):
            QuanSim(
                tuning,
                {
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 25}],
                    "customers": [
                        {
                            "id": "C1",
                            "table_id": "T1",
                            "dish_id": "ca_loc_nuong_trui",
                            "order_status": "reserved",
                            "reserved": ["I1"],
                        }
                    ],
                },
                Streams(1),
                IdAllocator(),
            )

    def test_burn_with_freshness_re_reserves_freshest_item(self):
        tuning = _v12_tuning(burn_s=20)
        scenario = {
            "random_customers": False,
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 50},
                {"id": "I2", "kind": "ca_loc", "fresh": 90},
            ],
            "stoves": [
                {
                    "id": "B1",
                    "pos": [2.0, 8.0],
                    "state": "ready",
                    "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                    "cook_ticks_left": 0,
                    "ready_ticks": 1200,
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
                    "reserved": [],
                }
            ],
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())
        ev = sim.step(_idle_inp())
        self.assertEqual(
            ev,
            [("dish_burnt", {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved"})],
        )
        # Phải chọn cá thể tươi hơn là I2 (90) thay vì I1 (50)
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I2"])


class TestMR1Phase3FreshnessContent(unittest.TestCase):
    """AC-P3-MR1: Nhãn độ tươi và lời thoại Mùa Nước Nổi tách biệt khỏi headless."""

    def test_freshness_badge_and_phase3_dialogues(self):
        self.assertEqual(freshness_badge(95)["label"], "Tươi rói")
        self.assertEqual(freshness_badge(60)["label"], "Tươi vừa")
        self.assertEqual(freshness_badge(35)["label"], "Sắp ươn")
        self.assertEqual(freshness_badge(29.9)["label"], "Đã ươn")
        self.assertIsNotNone(dialogue_for_event("spoiled"))
        self.assertIsNotNone(dialogue_for_event("current_warning"))
        self.assertIsNotNone(dialogue_for_event("reservation_served"))

        # Tắt mặc định cho headless
        disabled = ServiceReviewTracker()
        self.assertIsNone(disabled.observe("spoiled", {"item_id": "I1"}))
        self.assertEqual(disabled.spoiled_count, 0)

        summary = summarize_shift_review(
            [
                {"type": "event", "name": "spoiled", "data": {"item_id": "I1"}},
                {"type": "event", "name": "reservation_served", "data": {"reservation_id": "R1"}},
            ],
            enabled=True,
        )
        self.assertEqual(summary["spoiled_count"], 1)
        self.assertEqual(summary["reservation_served_count"], 1)
        self.assertEqual(summary["review_likes"], 3)


if __name__ == "__main__":
    unittest.main()
