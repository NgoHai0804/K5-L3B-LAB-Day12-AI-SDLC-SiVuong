"""Unit test luật Lát 2 (Đức) — hái nút, bắt cá, cập bến, hợp đồng kho (AC-P1-05..08).

Hộp đen qua `headless_cmd`. Giỏ đi qua seam `_try_hold` của lát 1, nên `hold_full`
ở đây kiểm cả khoá `kind` (hợp đồng đóng băng §4).
Chạy: python -m unittest discover -s tests -v
"""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def run_gather(w, scenario, fr, ticks=30, seed=1):
    sc = write_json(w.path("sc.json"), {"gather": scenario})
    ip = write_json(w.path("in.json"), frames(*fr))
    out = w.path("out.jsonl")
    code, err = run_headless("--mode", "gather", "--seed", str(seed), "--ticks", str(ticks),
                             "--out", out, "--scenario", sc, "--inputs", ip)
    assert code == 0, f"thoát {code}: {err}"
    return read_jsonl(out)


def end_row(rows):
    return [r for r in rows if r["type"] == "end"][0]


class TestHaiNut(unittest.TestCase):
    """AC-P1-05: hái nút `ready` gần nhất ở mặt nước."""

    # Đứng ngay nút N1 ở [12, 0] — xa bến [2, 0] (bán kính 3) nên interact = hái, không phải cập bến.
    SC = {"player": {"pos": [12, 0]}, "random_fish": False,
          "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}]}

    def test_01_hai_duoc_phat_gather_va_vao_gio(self):
        with Workdir() as w:
            rows = run_gather(w, self.SC, [{"tick": 1, "interact": True}])
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien"})
            self.assertEqual(snapshots(rows)[-1]["hold"], ["bong_dien_dien"])

    def test_02_nut_het_ready_sau_khi_hai(self):
        with Workdir() as w:
            rows = run_gather(w, self.SC, [{"tick": 1, "interact": True}])
            node = snapshots(rows)[-1]["nodes"][0]
            self.assertFalse(node["ready"])
            self.assertGreater(node["regrow_ticks"], 0)

    def test_03_khong_hai_lai_khi_chua_moc_lai(self):
        with Workdir() as w:
            rows = run_gather(w, self.SC, [{"tick": 1, "interact": True},
                                           {"tick": 2, "interact": False},
                                           {"tick": 3, "interact": True}])
            self.assertEqual(len(events(rows, "gather")), 1)

    def test_04_node_regrown_sau_dung_regrow_ticks(self):
        # regrow_ticks = 5 trong scenario -> mọc lại sớm để test nhanh.
        sc = dict(self.SC, nodes=[{"id": "N1", "kind": "bong_sung", "pos": [12, 0], "regrow_ticks": 5}])
        with Workdir() as w:
            rows = run_gather(w, sc, [], ticks=10)
            self.assertEqual([e["tick"] for e in events(rows, "node_regrown")], [5])

    def test_05_ngoai_interact_radius_thi_khong_hai(self):
        sc = dict(self.SC, nodes=[{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}])
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "interact": True}])
            self.assertEqual(events(rows, "gather"), [])

    def test_06_gio_day_thi_hold_full_co_kind_va_nut_con_ready(self):
        sc = dict(self.SC, hold=["ca_loc"] * 12)  # hold_capacity = 12
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "interact": True}])
            ev = events(rows, "hold_full")
            self.assertEqual(len(ev), 1)
            # hợp đồng §4: hold_full phải có `kind`; các khoá chẩn đoán của lát 1 giữ nguyên.
            self.assertEqual(ev[0]["data"]["kind"], "bong_dien_dien")
            self.assertEqual(ev[0]["data"]["node_id"], "N1")
            self.assertEqual(events(rows, "gather"), [])
            self.assertTrue(snapshots(rows)[-1]["nodes"][0]["ready"])

    def test_07_id_nho_thang_khi_cung_khoang_cach(self):
        sc = dict(self.SC, nodes=[{"id": "N2", "kind": "bong_sung", "pos": [13, 0]},
                                  {"id": "N1", "kind": "bong_dien_dien", "pos": [11, 0]}])
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "interact": True}])
            self.assertEqual(events(rows, "gather")[0]["data"]["node_id"], "N1")

    def test_08_duoi_nuoc_thi_khong_hai_duoc(self):
        # nút buộc ở d = 0; người lặn xuống d = 5 thì ngoài bán kính và sai điều kiện mặt nước.
        sc = dict(self.SC, player={"pos": [12, 5]})
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "interact": True}])
            self.assertEqual(events(rows, "gather"), [])


class TestBatCa(unittest.TestCase):
    """AC-P1-06: bắt đàn cá dưới nước theo `fish_yield` + hồi chiêu."""

    # Đứng ngay đàn cá dưới nước. ca_linh -> fish_yield = 3.
    SC = {"player": {"pos": [15, 5]}, "nodes": [],
          "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}]}

    def test_01_bat_duoc_dung_fish_yield(self):
        with Workdir() as w:
            rows = run_gather(w, self.SC, [{"tick": 1, "catch": True}])
            ev = events(rows, "fish_caught")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["data"], {"fish_id": "F1", "kind": "ca_linh"})
            self.assertEqual(snapshots(rows)[-1]["hold"], ["ca_linh"] * 3)

    def test_02_ca_bi_xoa_khoi_danh_sach(self):
        with Workdir() as w:
            rows = run_gather(w, self.SC, [{"tick": 1, "catch": True}])
            self.assertEqual(snapshots(rows)[-1]["fish"], [])

    def test_03_ca_loc_cho_dung_1_mon(self):
        sc = dict(self.SC, fish=[{"id": "F1", "kind": "ca_loc", "pos": [15, 5]}])
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "catch": True}])
            self.assertEqual(snapshots(rows)[-1]["hold"], ["ca_loc"])

    def test_04_o_mat_nuoc_thi_khong_bat_duoc(self):
        # Người ở mặt nước (d = 0) -> sai điều kiện "chỉ khi dưới nước".
        sc = dict(self.SC, player={"pos": [15, 0]},
                  fish=[{"id": "F1", "kind": "ca_loc", "pos": [15, 1]}])
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "catch": True}])
            self.assertEqual(events(rows, "fish_caught"), [])

    def test_05_hoi_chieu_chan_cu_bat_thu_hai(self):
        sc = dict(self.SC, fish=[{"id": "F1", "kind": "ca_loc", "pos": [15, 5]},
                                 {"id": "F2", "kind": "ca_loc", "pos": [15.5, 5]}])
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "catch": True},
                                      {"tick": 2, "catch": False},
                                      {"tick": 3, "catch": True}], ticks=20)
            self.assertEqual(len(events(rows, "fish_caught")), 1)

    def test_06_sau_hoi_chieu_thi_bat_duoc_tiep(self):
        sc = dict(self.SC, fish=[{"id": "F1", "kind": "ca_loc", "pos": [15, 5]},
                                 {"id": "F2", "kind": "ca_loc", "pos": [15.5, 5]}])
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "catch": True},
                                      {"tick": 2, "catch": False},
                                      {"tick": 40, "catch": True}], ticks=60)
            self.assertEqual(len(events(rows, "fish_caught")), 2)

    def test_07_ngoai_catch_radius_thi_khong_bat(self):
        sc = dict(self.SC, fish=[{"id": "F1", "kind": "ca_loc", "pos": [20, 5]}])
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "catch": True}])
            self.assertEqual(events(rows, "fish_caught"), [])

    def test_08_gio_khong_du_cho_ca_linh_thi_hold_full(self):
        # còn 2 chỗ nhưng ca_linh cần 3 -> bỏ hẳn, cá không mất, không vào hồi chiêu.
        sc = dict(self.SC, hold=["ca_loc"] * 10)
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "catch": True}])
            ev = events(rows, "hold_full")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["data"]["kind"], "ca_linh")
            self.assertEqual(ev[0]["data"]["fish_id"], "F1")
            self.assertEqual(ev[0]["data"]["required"], 3)
            self.assertEqual(ev[0]["data"]["free"], 2)
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(len(snapshots(rows)[-1]["fish"]), 1)

    def test_09_id_nho_thang_khi_cung_khoang_cach(self):
        sc = dict(self.SC, fish=[{"id": "F2", "kind": "ca_loc", "pos": [16, 5]},
                                 {"id": "F1", "kind": "ca_loc", "pos": [14, 5]}])
        with Workdir() as w:
            rows = run_gather(w, sc, [{"tick": 1, "catch": True}])
            self.assertEqual(events(rows, "fish_caught")[0]["data"]["fish_id"], "F1")


class TestGhiKho(unittest.TestCase):
    """AC-P1-07/08: cập bến + hợp đồng file kho (docs/contracts/README.md §1)."""

    SC = {"player": {"pos": [12, 0]}, "random_fish": False,
          "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}]}

    # hái ở [12, 0] rồi bơi về bến [2, 0] bấm interact.
    DOCK_FR = [{"tick": 1, "interact": True},
               {"tick": 2, "interact": False, "move": [-1, 0]},
               {"tick": 400, "move": [0, 0], "interact": True}]

    def _run(self, scenario, fr, ticks):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": scenario})
            ip = write_json(w.path("in.json"), frames(*fr))
            out, inv = w.path("out.jsonl"), w.path("kho.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(ticks),
                                     "--out", out, "--scenario", sc, "--inputs", ip,
                                     "--inventory-out", inv)
            self.assertEqual(code, 0, err)
            data = None
            if os.path.exists(inv):
                with open(inv, encoding="utf-8") as f:
                    data = json.load(f)
            return read_jsonl(out), data

    def test_01_docked_ghi_kho_dung_khoa_goc_items(self):
        rows, kho = self._run(self.SC, self.DOCK_FR, 600)
        self.assertEqual(end_row(rows)["reason"], "docked")
        self.assertEqual(list(kho.keys()), ["items"])
        self.assertEqual(kho["items"], {"bong_dien_dien": 1})

    def test_02_gather_end_khop_voi_file_kho(self):
        rows, kho = self._run(self.SC, self.DOCK_FR, 600)
        ev = events(rows, "gather_end")
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["data"]["inventory"]["items"], kho["items"])

    def test_03_tick_limit_thi_KHONG_ghi_kho(self):
        rows, kho = self._run(self.SC, [{"tick": 1, "interact": True}], 30)
        self.assertEqual(end_row(rows)["reason"], "tick_limit")
        self.assertIsNone(kho, "tick_limit khong duoc ghi file kho")

    def test_04_het_gio_reason_time_van_ghi_kho(self):
        sc = dict(self.SC, time_left_ticks=5)
        rows, kho = self._run(sc, [{"tick": 1, "interact": True}], 30)
        self.assertEqual(end_row(rows)["reason"], "time")
        self.assertEqual(kho["items"], {"bong_dien_dien": 1})

    def test_05_bo_muc_bang_0(self):
        # không hái gì, kết thúc do hết giờ -> items rỗng, không có khoá nào = 0.
        sc = dict(self.SC, time_left_ticks=5)
        _, kho = self._run(sc, [], 30)
        self.assertEqual(kho["items"], {})

    def test_06_fainted_thi_ghi_kho_rong(self):
        # oxy đã cạn + ngạt 59 tick + Máu 1 -> tick 1 choke lần cuối -> faint, giỏ mất sạch.
        sc = {"player": {"pos": [15, 5], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59},
              "hold": ["ca_loc", "bong_sung"], "nodes": [], "fish": []}
        rows, kho = self._run(sc, [], 30)
        self.assertEqual(end_row(rows)["reason"], "fainted")
        self.assertEqual(kho["items"], {})

    def test_07_sample_la_mau_hop_le_cho_ca_hai_team(self):
        from chonoi.inventory import read_inventory
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        items = read_inventory(os.path.join(root, "docs", "contracts", "inventory.sample.json"))
        self.assertTrue(items)

    def test_08_kho_so_am_thi_thoat_2(self):
        with Workdir() as w:
            bad = write_json(w.path("bad.json"), {"items": {"ca_loc": -1}})
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5",
                                   "--out", w.path("o.jsonl"), "--inventory", bad)
            self.assertEqual(code, 2)

    def test_09_kho_id_la_thi_thoat_2(self):
        with Workdir() as w:
            bad = write_json(w.path("bad.json"), {"items": {"ca_map": 1}})
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5",
                                   "--out", w.path("o.jsonl"), "--inventory", bad)
            self.assertEqual(code, 2)

    def test_10_kho_khoa_goc_la_thi_thoat_2(self):
        with Workdir() as w:
            bad = write_json(w.path("bad.json"), {"items": {"ca_loc": 1}, "extra": 1})
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5",
                                   "--out", w.path("o.jsonl"), "--inventory", bad)
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
