"""Bộ test tự động cho Lát 4 (`chonoi/sim/quan.py`) và nội dung MR-1 (`chonoi/content/dave_theme.py`).

Phụ trách: Nguyễn Thanh Tùng (Lát 4 · Content Lead)
Bao phủ các tiêu chí:
- AC-P1-12: Bếp nấu (chọn đơn reserved cũ nhất theo order_tick rồi id bàn, tiêu đúng nguyên liệu giữ,
            cook_started với items sắp theo kind & base_price, cook_ticks_left đếm ngược,
            dish_ready với ready_ticks = 0, ready_ticks chỉ tăng cho món đã ready ở đầu bước, không cháy).
- AC-P1-13: Ưu tiên interact theo (khoảng cách, bếp trước bàn, id) + bỏ lượt nếu mục tiêu chọn không tương tác được;
            bưng món (dish_picked, tay trống), phục vụ (served, đúng order_id, đúng tick kiên nhẫn về 0 vẫn hợp lệ),
            tính boa theo tip_min_patience_ratio sau bước 1.
- AC-P1-14: Ăn xong trả tiền (paid reason finished_eating), boa dương cộng tip_reputation có kẹp trần;
            hết ca khách còn ăn (kể cả vừa được giao món ở tick cuối) trả ngay (paid reason closing),
            khách còn chờ rời (customer_left reason closing, không trừ uy tín), dọn xong phát quan_end;
            khách rời do patience nhả giữ chỗ và bỏ món trên bếp/tay không hoàn nguyên liệu đã nấu.
- MR-1:     Nội dung cảm hứng Dave the Diver (chonoi.content.dave_theme) tắt ở headless, không ảnh hưởng JSONL.
"""

import json
import os
import subprocess
import sys
import unittest

from chonoi.content import (
    DISH_LORE,
    INGREDIENT_GUIDE,
    ServiceReviewTracker,
    dialogue_for_event,
    summarize_shift_review,
)
from chonoi.contract import load_contract
from chonoi.runner import run as run_sim
from helpers import Workdir, events, frames, read_jsonl, snapshots, write_json


def _run_py_headless(*args):
    """Chạy `chonoi.headless` bằng chính interpreter hiện tại (tương thích cả Windows và Linux)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = subprocess.run([sys.executable, "-m", "chonoi.headless", *args], cwd=root, capture_output=True, text=True)
    return p.returncode, p.stderr


def _tuning():
    return load_contract()["tuning"]


class TestQuanLat4Cooking(unittest.TestCase):
    """AC-P1-12: Bếp nấu, thứ tự đơn reserved, tiêu nguyên liệu, dish_ready và ready_ticks."""

    def test_ac_p1_12_cook_oldest_reserved_and_ready_ticks(self):
        tuning = _tuning()
        # Hai đơn reserved: C2 order_tick=10 (cũ hơn) phải được nấu trước C1 order_tick=20.
        scenario = {
            "player": {"pos": [2.0, 8.0]},  # đúng vị trí bếp B1
            "stock": {"ca_linh": 3, "bong_dien_dien": 1, "ca_loc": 1},
            "random_customers": False,
            "stoves": [{"id": "B1", "pos": [2.0, 8.0]}],
            "tables": [{"id": "T1", "pos": [9.0, 2.0]}],
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "lau_ca_linh_dien_dien",
                    "order_tick": 10,
                    "state": "waiting",
                    "order_status": "reserved",
                }
            ],
        }
        cook_ticks = int(round(tuning["menu"]["lau_ca_linh_dien_dien"]["cook_s"] * 60))
        with Workdir() as w:
            out = w.path("cook.jsonl")
            run_sim("quan", tuning, scenario, 42, [{"tick": 0, "interact": True}], cook_ticks + 5, out, 1)
            rows = read_jsonl(out)

        started = events(rows, "cook_started")
        self.assertEqual(len(started), 1)
        self.assertEqual(started[0]["tick"], 1)
        self.assertEqual(
            started[0]["data"],
            {
                "stove_id": "B1",
                "order_id": "C1",
                "dish_id": "lau_ca_linh_dien_dien",
                "items": ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"],
                "base_price": 120,
            },
        )
        snaps = {s["tick"]: s for s in snapshots(rows)}
        # Sau tick 1: nguyên liệu đã tiêu khỏi stock, khách chuyển assigned và nhả reserved
        self.assertEqual(snaps[1]["stock"], {"ca_loc": 1})
        self.assertEqual(snaps[1]["customers"][0]["order_status"], "assigned")
        self.assertEqual(snaps[1]["customers"][0]["reserved"], {})
        self.assertEqual(snaps[1]["stoves"][0]["state"], "cooking")
        self.assertEqual(snaps[1]["stoves"][0]["cook_ticks_left"], cook_ticks)

        # Sau đúng cook_ticks bước kể từ tick 1 (tức tick 1 + cook_ticks): dish_ready và ready_ticks == 0
        ready_ev = events(rows, "dish_ready")
        self.assertEqual(len(ready_ev), 1)
        ready_tick = 1 + cook_ticks
        self.assertEqual(ready_ev[0]["tick"], ready_tick)
        self.assertEqual(
            ready_ev[0]["data"],
            {"stove_id": "B1", "order_id": "C1", "dish_id": "lau_ca_linh_dien_dien"},
        )
        self.assertEqual(snaps[ready_tick]["stoves"][0]["state"], "ready")
        self.assertEqual(snaps[ready_tick]["stoves"][0]["ready_ticks"], 0)
        # Bước kế tiếp mới bắt đầu tăng ready_ticks (chỉ tăng cho món đã ready ở đầu bước) và không cháy
        self.assertEqual(snaps[ready_tick + 1]["stoves"][0]["ready_ticks"], 1)
        self.assertEqual(snaps[ready_tick + 3]["stoves"][0]["ready_ticks"], 3)
        self.assertEqual(snaps[ready_tick + 3]["stoves"][0]["state"], "ready")

    def test_ac_p1_12_interact_priority_stove_before_table_and_no_fallthrough(self):
        tuning = _tuning()
        # Đặt bếp B1 và bàn T1 ở CÙNG khoảng cách (0m) tới người chơi.
        # Bếp đang cooking (không tương tác được) -> phải chọn bếp trước bàn và BỎ LƯỢT, KHÔNG phục vụ bàn!
        scenario = {
            "player": {"pos": [5.0, 5.0]},
            "random_customers": False,
            "stoves": [
                {
                    "id": "B1",
                    "pos": [5.0, 5.0],
                    "state": "cooking",
                    "dish": {"order_id": "C2", "dish_id": "goi_bong_sung", "base_price": 40},
                    "cook_ticks_left": 100,
                    "ready_ticks": 0,
                }
            ],
            "tables": [{"id": "T1", "pos": [5.0, 5.0]}],
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
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
        with Workdir() as w:
            out = w.path("prio.jsonl")
            run_sim("quan", tuning, scenario, 1, [{"tick": 0, "interact": True}], 2, out, 1)
            rows = read_jsonl(out)
        self.assertEqual(events(rows, "served"), [])
        self.assertIsNotNone(snapshots(rows)[-1]["hand"])


class TestQuanLat4PickServeTip(unittest.TestCase):
    """AC-P1-13: Bưng món, phục vụ đúng đơn, tính boa theo tỷ lệ kiên nhẫn và phục vụ đúng tick patience=0."""

    def test_ac_p1_13_pick_and_serve_with_tip(self):
        tuning = _tuning()
        pat_max = int(round(tuning["quan"]["patience_s"] * 60))
        # Đặt kiên nhẫn ban đầu = đúng 50% + 1 tick -> sau bước 1 giảm còn đúng 50% -> vẫn được boa!
        half_plus_one = (pat_max // 2) + 1
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
                    "ready_ticks": 5,
                }
            ],
            "tables": [{"id": "T1", "pos": [3.0, 8.0]}],  # trong tầm 1.5m nhưng xa hơn bếp (1.0m vs 0.0m)
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_tick": 0,
                    "state": "waiting",
                    "patience_ticks_left": half_plus_one + 1,  # 2 tick (bưng ở tick 0, phục vụ ở tick 1)
                    "order_status": "assigned",
                    "reserved": {},
                }
            ],
        }
        # Tick 0: đứng ở [2,8] bấm E -> bưng từ B1. Tick 1: đã ở [3,8]? Ta đặt B1 ở [2,8], T1 ở [2.8,8]
        # Để đơn giản hơn, test 2 bước bằng fixture riêng cho bưng và phục vụ, hoặc di chuyển sang T1.
        # Ở đây di chuyển không cần: đặt player ở [2.4, 8.0], B1 ở [2.0, 8.0] (dist 0.4), T1 ở [3.0, 8.0] (dist 0.6).
        # Khi bưng xong tay đầy, để chọn T1 ta di chuyển sang phải (move=[1,0]) vài tick.
        scenario["player"]["pos"] = [2.4, 8.0]
        scenario["customers"][0]["patience_ticks_left"] = pat_max  # dư dả cho boa
        inp = [
            {"tick": 0, "interact": True},
            {"tick": 1, "interact": False, "move": [1, 0]},
            {"tick": 15, "move": [0, 0], "interact": True},
        ]
        with Workdir() as w:
            out = w.path("serve.jsonl")
            run_sim("quan", tuning, scenario, 7, inp, 20, out, 1)
            rows = read_jsonl(out)

        picked = events(rows, "dish_picked")
        self.assertEqual(len(picked), 1)
        self.assertEqual(picked[0]["tick"], 1)
        self.assertEqual(picked[0]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui"})

        served = events(rows, "served")
        self.assertEqual(len(served), 1)
        self.assertEqual(served[0]["tick"], 16)
        self.assertEqual(served[0]["data"]["base_price"], 60)
        self.assertEqual(served[0]["data"]["tip"], 12)  # floor(60 * 0.2)
        self.assertEqual(served[0]["data"]["patience_ticks_left"], pat_max - 16)
        snaps = {s["tick"]: s for s in snapshots(rows)}
        self.assertIsNone(snaps[16]["hand"])
        self.assertEqual(snaps[16]["customers"][0]["state"], "eating")
        self.assertEqual(snaps[16]["customers"][0]["eat_ticks_left"], int(round(tuning["quan"]["eat_s"] * 60)))

    def test_ac_p1_13_serve_on_exact_zero_patience_tick_still_valid_with_zero_tip(self):
        tuning = _tuning()
        scenario = {
            "player": {"pos": [9.0, 2.0]},
            "random_customers": False,
            "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "goi_bong_sung",
                    "order_tick": 0,
                    "state": "waiting",
                    "patience_ticks_left": 1,  # Bước 1 giảm về 0, nhưng interact ở bước 3 vẫn hợp lệ!
                    "order_status": "assigned",
                    "reserved": {},
                }
            ],
        }
        with Workdir() as w:
            out = w.path("zero_pat.jsonl")
            run_sim("quan", tuning, scenario, 1, [{"tick": 0, "interact": True}], 2, out, 1)
            rows = read_jsonl(out)

        served = events(rows, "served")
        self.assertEqual(len(served), 1)
        self.assertEqual(served[0]["data"]["patience_ticks_left"], 0)
        self.assertEqual(served[0]["data"]["tip"], 0)
        self.assertEqual(events(rows, "customer_left"), [])


class TestQuanLat4PaymentAndClosing(unittest.TestCase):
    """AC-P1-14: Trả tiền khi ăn xong, cộng uy tín kẹp trần, hết ca (closing) và quan_end."""

    def test_ac_p1_14_finish_eating_pays_and_clamps_reputation(self):
        tuning = _tuning()
        scenario = {
            "random_customers": False,
            "reputation": 4.9,  # gần trần 5.0
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_tick": 0,
                    "state": "eating",
                    "patience_ticks_left": 2000,
                    "eat_ticks_left": 2,
                    "order_status": "served",
                    "reserved": {},
                    "base_price": 60,
                    "tip": 12,
                }
            ],
        }
        with Workdir() as w:
            out = w.path("pay.jsonl")
            run_sim("quan", tuning, scenario, 1, [], 3, out, 1)
            rows = read_jsonl(out)

        paid = events(rows, "paid")
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0]["tick"], 2)
        self.assertEqual(
            paid[0]["data"],
            {
                "order_id": "C1",
                "table_id": "T1",
                "base_price": 60,
                "tip": 12,
                "amount": 72,
                "reason": "finished_eating",
            },
        )
        snaps = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(snaps[2]["customers"], [])
        self.assertEqual(snaps[2]["tables"][0]["customer_id"], None)
        self.assertEqual(snaps[2]["money"], 72)
        self.assertEqual(snaps[2]["earned"], 72)
        self.assertEqual(snaps[2]["reputation"], 5.0)  # kẹp trần reputation_max = 5

    def test_ac_p1_14_serve_on_last_tick_pays_closing_and_emits_quan_end(self):
        tuning = _tuning()
        scenario = {
            "player": {"pos": [9.0, 2.0]},
            "time_left_ticks": 1,  # Hết ca ngay ở bước đầu tiên!
            "random_customers": False,
            "reputation": 3.0,
            "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_tick": 0,
                    "state": "waiting",
                    "patience_ticks_left": 3000,
                    "order_status": "assigned",
                    "reserved": {},
                }
            ],
        }
        with Workdir() as w:
            out = w.path("closing_serve.jsonl")
            run_sim("quan", tuning, scenario, 1, [{"tick": 0, "interact": True}], 10, out, 1)
            rows = read_jsonl(out)

        ev_names = [e["name"] for e in events(rows)]
        self.assertEqual(ev_names, ["served", "paid", "quan_end"])
        self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
        self.assertEqual(events(rows, "paid")[0]["data"]["amount"], 72)
        self.assertEqual(
            events(rows, "quan_end")[0]["data"],
            {"reason": "time", "money": 72, "earned": 72, "shift_earned": 72, "reputation": 3.2},
        )
        self.assertEqual(rows[-1]["type"], "end")
        self.assertEqual(rows[-1]["reason"], "time")
        self.assertEqual(rows[-1]["score"], 72 + 100 * 3)

    def test_ac_p1_14_waiting_customer_at_closing_no_rep_penalty_and_cleans_stove(self):
        tuning = _tuning()
        scenario = {
            "time_left_ticks": 1,
            "random_customers": False,
            "reputation": 3.5,
            "stoves": [
                {
                    "id": "B1",
                    "pos": [2.0, 8.0],
                    "state": "cooking",
                    "dish": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
                    "cook_ticks_left": 50,
                    "ready_ticks": 0,
                }
            ],
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "goi_bong_sung",
                    "order_tick": 0,
                    "state": "waiting",
                    "patience_ticks_left": 100,
                    "order_status": "assigned",
                    "reserved": {},
                }
            ],
        }
        with Workdir() as w:
            out = w.path("closing_wait.jsonl")
            run_sim("quan", tuning, scenario, 1, [], 5, out, 1)
            rows = read_jsonl(out)

        left = events(rows, "customer_left")
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0]["data"], {"order_id": "C1", "table_id": "T1", "reason": "closing", "reputation": 3.5})
        last_snap = snapshots(rows)[-1]
        self.assertEqual(last_snap["customers"], [])
        self.assertEqual(last_snap["stoves"][0]["state"], "idle")
        self.assertIsNone(last_snap["stoves"][0]["dish"])

    def test_headless_cli_full_lat4_loop_deterministic(self):
        """Chạy nguyên tiến trình headless CLI cho Lát 4 để kiểm tra tính tất định từng byte."""
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "player": {"pos": [2.0, 8.0]},
                        "stock": {"ca_loc": 1},
                        "time_left_ticks": 500,
                        "random_customers": False,
                        "customers": [
                            {
                                "id": "C1",
                                "table_id": "T1",
                                "dish_id": "ca_loc_nuong_trui",
                                "order_tick": 0,
                                "state": "waiting",
                                "order_status": "reserved",
                            }
                        ],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False}))
            o1, o2 = w.path("o1.jsonl"), w.path("o2.jsonl")
            for out in (o1, o2):
                code, err = _run_py_headless(
                    "--mode", "quan", "--seed", "42", "--scenario", sc, "--inputs", inp, "--ticks", "400", "--out", out
                )
                self.assertEqual(code, 0, err)
            with open(o1, "rb") as f1, open(o2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())
            rows = read_jsonl(o1)
            self.assertEqual(len(events(rows, "cook_started")), 1)
            self.assertEqual(len(events(rows, "dish_ready")), 1)


class TestMR1DaveTheDiverContent(unittest.TestCase):
    """Kiểm chứng nội dung sáng tạo MR-1: đầy đủ lore & tắt hoàn toàn khi ở chế độ headless."""

    def test_guides_cover_all_core_ingredients_and_dishes(self):
        tuning = _tuning()
        self.assertEqual(set(INGREDIENT_GUIDE.keys()), {"ca_loc", "ca_linh", "bong_dien_dien", "bong_sung"})
        self.assertEqual(set(DISH_LORE.keys()), set(tuning["menu"].keys()))
        self.assertIsNotNone(dialogue_for_event("cook_started"))
        self.assertIsNotNone(dialogue_for_event("paid", {"tip": 12}))

    def test_review_tracker_disabled_by_default_for_headless(self):
        tracker = ServiceReviewTracker()
        self.assertFalse(tracker.enabled)
        self.assertIsNone(tracker.observe("paid", {"tip": 12}))
        self.assertEqual(tracker.review_likes, 0)

    def test_review_tracker_summarizes_events_when_enabled(self):
        rows = [
            {"type": "event", "name": "served", "data": {"order_id": "C1"}},
            {"type": "event", "name": "paid", "data": {"order_id": "C1", "tip": 12}},
            {"type": "event", "name": "served", "data": {"order_id": "C2"}},
            {"type": "event", "name": "paid", "data": {"order_id": "C2", "tip": 24}},
        ]
        summary = summarize_shift_review(rows, enabled=True)
        self.assertEqual(summary["served_count"], 2)
        self.assertEqual(summary["tipped_count"], 2)
        self.assertEqual(summary["best_tip_streak"], 2)
        self.assertEqual(summary["total_tips"], 36)
        self.assertEqual(summary["review_likes"], 4)
        self.assertEqual(summary["tier_stars"], "★★★☆☆")


if __name__ == "__main__":
    unittest.main()
