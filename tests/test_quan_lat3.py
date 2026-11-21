"""Bộ test tự động cho Lát 3 (`chonoi/sim/quan.py`): khách theo lịch, giữ chỗ nguyên liệu, kiên nhẫn.

Phụ trách: Bùi Đình Quý Anh (Lát 3 · QA lead)
Bao phủ các tiêu chí:
- AC-P1-10: Lịch khách theo first_customer_tick rồi mỗi customer_interval_s × 60 tick (theo phase_tick, kể cả khi
            rút ngắn ca); bàn trống id nhỏ nhất; không còn bàn thì bỏ lượt; chọn món đều theo seed trong các món đủ
            kho khả dụng (tồn vật lý trừ phần giữ); không có món đủ thì no_dish {}; khách mới giữ đúng công thức,
            order_tick = phase_tick, kiên nhẫn đầy và giảm từ bước sau; random_customers=false tắt khách tự sinh.
- AC-P1-11: Kiên nhẫn về 0 khi còn giờ -> customer_left reason patience + uy tín left_reputation_delta, nhả phần
            giữ (tồn vật lý giữ nguyên); thiếu reserved ở fixture -> cấp theo công thức; tất định theo seed.
"""

import os
import subprocess
import sys
import unittest

from chonoi.contract import load_contract
from helpers import Workdir, events, frames, read_jsonl, snapshots, write_json


def _run_py_headless(*args):
    """Chạy `chonoi.headless` bằng chính interpreter hiện tại (tương thích cả Windows và Linux)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = subprocess.run([sys.executable, "-m", "chonoi.headless", *args], cwd=root, capture_output=True, text=True)
    return p.returncode, p.stderr


Q = load_contract()["tuning"]["quan"]
MENU = load_contract()["tuning"]["menu"]
FIRST = int(Q["first_customer_tick"])
INTERVAL = int(round(Q["customer_interval_s"] * 60))
PATIENCE = int(round(Q["patience_s"] * 60))
TABLES = [tb["id"] for tb in Q["tables"]]  # v1.1: T1–T4 (P1: chỉ T1)
FULL_STOCK = {"ca_loc": 5, "ca_linh": 9, "bong_dien_dien": 3, "bong_sung": 6, "ca_keo": 4, "keo_neo": 2}


def run_quan(w, scenario, ticks, seed=1, every=1, inputs=None, name="o.jsonl"):
    args = ["--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
            "--scenario", write_json(w.path("sc.json"), {"quan": scenario}), "--out", w.path(name)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = _run_py_headless(*args)
    assert code == 0, err
    return read_jsonl(w.path(name))


def snap_at(rows, tick):
    return {r["tick"]: r for r in snapshots(rows)}[tick]


class TestQuanLat3Schedule(unittest.TestCase):
    """AC-P1-10: lịch khách, chọn bàn, chọn món, giữ chỗ, no_dish."""

    def test_ac_p1_10_first_customer_reserves_recipe(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1}}, ticks=FIRST)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], FIRST)
            self.assertEqual(arr[0]["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})
            s = snap_at(rows, FIRST)
            c = s["customers"][0]
            self.assertEqual((c["state"], c["order_status"], c["reserved"], c["order_tick"]),
                             ("waiting", "reserved", {"ca_loc": 1}, FIRST))
            self.assertEqual(c["patience_ticks_left"], PATIENCE, "kiên nhẫn đầy lúc vừa tới")
            self.assertEqual(s["tables"][0]["customer_id"], "C1")
            self.assertEqual(s["stock"], {"ca_loc": 1}, "giữ chỗ không trừ tồn vật lý")

    def test_ac_p1_10_patience_starts_next_step(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1}}, ticks=FIRST + 2)
            self.assertEqual(snap_at(rows, FIRST + 1)["customers"][0]["patience_ticks_left"], PATIENCE - 1)
            self.assertEqual(snap_at(rows, FIRST + 2)["customers"][0]["patience_ticks_left"], PATIENCE - 2)

    def test_ac_p1_10_no_dish_when_stock_empty(self):
        with Workdir() as w:
            rows = run_quan(w, {}, ticks=FIRST, every=FIRST)
            self.assertEqual([(e["name"], e["data"], e["tick"]) for e in events(rows)], [("no_dish", {}, FIRST)])
            self.assertEqual(snapshots(rows)[-1]["customers"], [])

    def test_ac_p1_10_table_busy_skips_turn_without_event(self):
        """Mọi bàn đều có khách (fixture) -> lượt khách bị bỏ, không phát event."""
        with Workdir() as w:
            sc = {"stock": FULL_STOCK, "customers": [
                {"id": f"C{i + 1}", "table_id": tid, "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": PATIENCE}
                for i, tid in enumerate(TABLES)]}
            rows = run_quan(w, sc, ticks=FIRST + INTERVAL, every=50)
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(events(rows, "no_dish"), [])

    def test_ac_p1_10_only_cookable_dish_is_chosen(self):
        """Gỏi cần 2 bông súng, lẩu cần 3 cá linh + 1 bông điên điển: chỉ cá nướng đủ kho."""
        with Workdir() as w:
            for seed in range(1, 6):
                rows = run_quan(w, {"stock": {"ca_loc": 1, "bong_sung": 1, "ca_linh": 3}}, ticks=FIRST, seed=seed)
                self.assertEqual(events(rows, "customer_arrived")[0]["data"]["dish_id"], "ca_loc_nuong_trui", seed)

    def test_ac_p1_10_next_customers_take_smallest_free_table(self):
        """Lượt k ở FIRST + k·INTERVAL lấy bàn trống id nhỏ nhất (T1 -> T2 -> ...), id khách nối tiếp C1, C2, ..."""
        with Workdir() as w:
            n = len(TABLES)
            rows = run_quan(w, {"stock": FULL_STOCK}, ticks=FIRST + (n - 1) * INTERVAL, every=600)
            arr = events(rows, "customer_arrived")
            self.assertEqual([e["tick"] for e in arr], [FIRST + k * INTERVAL for k in range(n)])
            self.assertEqual([e["data"]["table_id"] for e in arr], TABLES)
            self.assertEqual([e["data"]["order_id"] for e in arr], [f"C{k + 1}" for k in range(n)])

    def test_ac_p1_10_schedule_uses_phase_tick_when_shift_shortened(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1}, "time_left_ticks": FIRST + 5}, ticks=FIRST + 10, every=50)
            arr = events(rows, "customer_arrived")
            self.assertEqual([e["tick"] for e in arr], [FIRST])

    def test_ac_p1_10_no_spawn_on_closing_tick(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1}, "time_left_ticks": FIRST}, ticks=FIRST + 5, every=50)
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(events(rows, "quan_end")[0]["tick"], FIRST)

    def test_ac_p1_10_random_customers_false_disables_spawn(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": FULL_STOCK, "random_customers": False}, ticks=FIRST + INTERVAL, every=500)
            self.assertEqual(events(rows, "customer_arrived") + events(rows, "no_dish"), [])

    def test_ac_p1_10_dish_choice_deterministic_and_covers_menu(self):
        seen = set()
        with Workdir() as w:
            for seed in range(1, 41):
                a = events(run_quan(w, {"stock": FULL_STOCK}, ticks=FIRST, seed=seed, name="a.jsonl"), "customer_arrived")
                b = events(run_quan(w, {"stock": FULL_STOCK}, ticks=FIRST, seed=seed, name="b.jsonl"), "customer_arrived")
                self.assertEqual(a, b, "cùng seed -> cùng món")
                seen.add(a[0]["data"]["dish_id"])
                with open(w.path("a.jsonl"), "rb") as fa, open(w.path("b.jsonl"), "rb") as fb:
                    self.assertEqual(fa.read(), fb.read())
        self.assertEqual(seen, set(MENU), "chọn đều trong các món đủ kho: 40 seed phải gặp đủ mọi món của menu")


class TestQuanLat3Patience(unittest.TestCase):
    """AC-P1-11: kiên nhẫn, customer_left, uy tín, nhả giữ chỗ."""

    def test_ac_p1_11_patience_runs_out(self):
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 1}, "random_customers": False, "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 3}]}
            rows = run_quan(w, sc, ticks=5)
            left = events(rows, "customer_left")
            self.assertEqual(left[0]["tick"], 3)
            self.assertEqual(left[0]["data"], {"order_id": "C1", "table_id": "T1", "reason": "patience",
                                               "reputation": Q["reputation_initial"] + Q["left_reputation_delta"]})
            s = snap_at(rows, 3)
            self.assertEqual(s["customers"], [])
            self.assertEqual(s["tables"][0]["customer_id"], None)
            self.assertEqual(s["stock"], {"ca_loc": 1}, "nhả giữ chỗ, tồn vật lý giữ nguyên")

    def test_ac_p1_11_reputation_clamped_at_min(self):
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 1}, "random_customers": False, "reputation": 0.2, "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 1}]}
            rows = run_quan(w, sc, ticks=2)
            self.assertEqual(events(rows, "customer_left")[0]["data"]["reputation"], Q["reputation_min"])

    def test_ac_p1_11_fixture_missing_reserved_gets_recipe(self):
        with Workdir() as w:
            sc = {"stock": {"ca_linh": 3, "bong_dien_dien": 1}, "random_customers": False, "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"}]}
            rows = run_quan(w, sc, ticks=0)
            c = snapshots(rows)[0]["customers"][0]
            self.assertEqual(c["reserved"], {"bong_dien_dien": 1, "ca_linh": 3})
            self.assertEqual((c["state"], c["order_status"], c["order_tick"], c["patience_ticks_left"]),
                             ("waiting", "reserved", 0, PATIENCE))

    def test_ac_p1_11_left_customer_frees_stock_for_next_order(self):
        """Khách bỏ về nhả phần giữ: lượt kế tiếp gọi được đúng món đó."""
        with Workdir() as w:
            sc = {"stock": {"ca_loc": 1}, "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": FIRST - 1}]}
            rows = run_quan(w, sc, ticks=FIRST, every=FIRST)
            self.assertEqual(events(rows, "customer_left")[0]["tick"], FIRST - 1)
            arr = events(rows, "customer_arrived")
            self.assertEqual(arr[0]["data"], {"order_id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})


if __name__ == "__main__":
    unittest.main()
