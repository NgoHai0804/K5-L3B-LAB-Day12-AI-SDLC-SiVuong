"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

Nhóm viết tiếp (đúng thứ tự một bước trong PRD mục 13.8, "Gather"):
  XONG (lát 1 - Hải): bơi + oxy + biên + giỏ  (AC-P1-01..04)
      - oxy: dưới nước (d > surface_depth) trừ 1 tick/tick, mặt nước hồi oxygen_refill_per_tick, kẹp [0, max]
      - ngạt: oxy = 0 và đang dưới nước -> đếm zero_oxy_ticks, đủ choke_interval_ticks thì -1 Máu (choke)
      - Máu về 0 -> ngất (faint, gather_end reason `fainted`, mất toàn bộ giỏ, kho rỗng)
      - sự kiện dive / surface / oxygen_empty / choke / faint
      - giỏ: thứ tự nhặt (LIFO), sức chứa hold_capacity; seam `_try_hold` phát hold_full cho lát 2
  XONG (lát 2 - Đức): hái + bắt cá + cập bến + kho  (AC-P1-05..08)
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
      - cả hái và bắt cá đi qua seam `_try_hold` của lát 1, không tự thêm giỏ
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..ids import sort_by_id
from ..inventory import hold_to_items, version_tuple, fresh_to_units, units_to_fresh, UNITS_MAX
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, version="1.1"):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.version = version
        # v1.2 (ADR-0002): kho cá thể + độ tươi; lưu nội bộ bằng đơn vị nguyên (240 = 1 điểm).
        self.fresh = version_tuple(version) >= (1, 2)
        fc = tuning.get("freshness", {})
        self.fresh_units = fresh_to_units(fc.get("initial", 100.0))
        self.spoiled_units = fresh_to_units(fc.get("spoiled_below", 30.0))
        self.decay_units = int(round(fresh_to_units(fc.get("gather_decay_per_s", 0.5)) / TICK))
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        src_hold = scenario.get("hold", [])
        if self.fresh:  # v1.2: mỗi phần tử là cá thể {id,kind,u}, thứ tự vào giỏ (cuối = mới nhất)
            self.hold = [{"id": h["id"], "kind": h["kind"], "u": fresh_to_units(h["fresh"])} for h in src_hold]
            for h in self.hold:
                ids.reserve(h["id"])
        else:
            self.hold = list(src_hold)  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0  # số bước đã chạy (1-based sau khi tăng ở đầu mỗi bước)
        self.random_fish = bool(scenario.get("random_fish", True))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif self.random_fish:
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        # v1.1: cá BƠI mỗi bước trong dải độ sâu theo loài; sinh thêm theo lịch (AC-P2-02).
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0)} for f in src_fish]
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self):
        """Schema đếm (dict) ở v1.0/v1.1; schema cá thể (list) ở v1.2."""
        if self.fresh:
            return [{"id": it["id"], "kind": it["kind"], "fresh": units_to_fresh(it["u"])} for it in self.hold]
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": ([{"id": it["id"], "kind": it["kind"], "fresh": units_to_fresh(it["u"])} for it in self.hold]
                     if self.fresh else self.hold),
            "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 1b. độ tươi hàng có sẵn ở đầu bước (v1.2): hao giỏ, phát spoiled theo id
        self._decay_hold(events)
        # 2. cá bơi (v1.1) + sinh thêm theo lịch
        self._fish_step()
        # 3. bơi + chặn mép, rồi biên mặt nước -> oxy -> ngạt -> ngất
        was_surface = self._at_surface()
        self._move(inp)
        self._water(events, was_surface)
        if self.done:  # ngất (faint) -> dừng bước
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                n = self._nearest_ready_node()
                if n is not None:
                    amounts = [n["kind"]] * int(self.t["node_yield"])
                    if self._try_hold("gather", n["id"], amounts, events):
                        events.append(("gather", {"node_id": n["id"], "kind": n["kind"]}))
                        n["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        # 4. bắt cá: chỉ khi dưới nước và hết hồi chiêu
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not self._at_surface():
            f = self._nearest_fish()
            if f is not None:
                amounts = [f["kind"]] * int(self.t["fish_yield"][f["kind"]])
                if self._try_hold("catch", f["id"], amounts, events):
                    events.append(("fish_caught", {"fish_id": f["id"], "kind": f["kind"]}))
                    self.fish = [g for g in self.fish if g["id"] != f["id"]]
                    self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _nearest_ready_node(self):
        """Nút `ready` gần nhất trong interact_radius; bằng khoảng cách thì id nhỏ hơn thắng."""
        r = self.t["interact_radius"]
        cands = [n for n in sort_by_id(self.nodes)
                 if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= r]
        if not cands:
            return None
        return min(cands, key=lambda n: math.dist(self.pos, n["pos"]))

    def _nearest_fish(self):
        """Đàn cá gần nhất trong catch_radius; bằng khoảng cách thì id nhỏ hơn thắng."""
        r = self.t["catch_radius"]
        cands = [f for f in sort_by_id(self.fish) if math.dist(self.pos, f["pos"]) <= r]
        if not cands:
            return None
        return min(cands, key=lambda f: math.dist(self.pos, f["pos"]))

    def _fish_step(self):
        """Cá bơi mỗi bước trong dải độ sâu loài + sinh thêm theo lịch (AC-P2-02)."""
        t = self.t
        if self.phase_tick % int(t["fish_turn_every_ticks"]) == 0:
            rng = self.rng.get("fish_move")
            for f in sort_by_id(self.fish):  # đổi hướng TRƯỚC khi di chuyển
                f["heading_deg"] = rng.random() * 360.0
        step_len = float(t["fish_speed"]) / TICK
        x_lo, x_hi = t["fish_x_bounds"]
        for f in sort_by_id(self.fish):
            d_lo, d_hi = t["fish_depth_bands"][f["kind"]]
            self._advance_fish(f, step_len, x_lo, x_hi, d_lo, d_hi)
        if self.random_fish and self.phase_tick % int(t["fish_spawn"]["every_ticks"]) == 0:
            self._spawn_fish()

    @staticmethod
    def _advance_fish(f, dist, x_lo, x_hi, d_lo, d_hi):
        """Bơi `dist` theo hướng; chạm mép thì phản xạ phần dư và đảo thành phần vuông góc."""
        hx = math.cos(math.radians(f["heading_deg"]))
        hd = math.sin(math.radians(f["heading_deg"]))
        x, d = f["pos"]
        # mở rộng biên cho đàn khởi tạo ngoài dải (scenario cũ) để không dịch chuyển đột ngột
        x_lo, x_hi = min(x_lo, x), max(x_hi, x)
        d_lo, d_hi = min(d_lo, d), max(d_hi, d)
        nx = x + hx * dist
        if nx < x_lo:
            nx, hx = x_lo + (x_lo - nx), -hx
        elif nx > x_hi:
            nx, hx = x_hi - (nx - x_hi), -hx
        nd = d + hd * dist
        if nd < d_lo:
            nd, hd = d_lo + (d_lo - nd), -hd
        elif nd > d_hi:
            nd, hd = d_hi - (nd - d_hi), -hd
        f["pos"] = [nx, nd]
        f["heading_deg"] = math.degrees(math.atan2(hd, hx)) % 360

    def _spawn_candidates(self):
        sp = self.t["fish_spawn"]
        return [(float(x), float(d), kind)
                for kind in sorted(sp["depths"]) for x in sp["x"] for d in sp["depths"][kind]]

    def _spawn_fish(self):
        """Sinh tối đa 1 đàn: điểm cách mọi đàn đang sống > min_dist; loài theo trọng số."""
        sp = self.t["fish_spawn"]
        if len(self.fish) >= int(sp["cap"]):
            return
        min_dist = float(sp["min_dist"])
        cand = [p for p in self._spawn_candidates()
                if all(math.dist((p[0], p[1]), tuple(f["pos"])) > min_dist for f in self.fish)]
        if not cand:  # hết điểm -> bỏ lượt
            return
        weights = sp["weights"]
        species = [k for k in sorted(weights) if any(p[2] == k for p in cand)]
        rng = self.rng.get("fish_spawn")
        roll, acc, chosen = rng.random() * sum(weights[k] for k in species), 0, species[-1]
        for k in species:
            acc += weights[k]
            if roll < acc:
                chosen = k
                break
        pts = sorted(p for p in cand if p[2] == chosen)
        x, d, kind = pts[rng.randrange(len(pts))]  # chọn đều một điểm của loài
        self.fish.append({"id": self.ids.new("F"), "kind": kind,
                          "pos": [x, d], "heading_deg": rng.random() * 360.0})

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _water(self, events, was_surface):
        """Biên mặt nước, oxy, ngạt, ngất theo `d` CUỐI bước (AC-P1-02/03)."""
        t = self.t
        now_surface = self._at_surface()
        if was_surface != now_surface:  # chỉ phát khi đổi phía mốc mặt nước
            events.append(("dive" if not now_surface else "surface", {"pos": list(self.pos)}))
        if now_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0  # nổi lên -> hồi oxy và reset đếm ngạt
            return
        prev = self.oxygen_ticks
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if prev > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks == 0:  # kể cả bước vừa chạm 0
            self.zero_oxy_ticks += 1
            if self.zero_oxy_ticks >= int(t["choke_interval_ticks"]):
                self.zero_oxy_ticks = 0
                self.hp -= 1
                events.append(("choke", {"hp": self.hp}))
                if self.hp <= 0:  # ngất: bỏ giỏ LIFO, kho rỗng
                    if self.fresh:
                        lost = [{"id": it["id"], "kind": it["kind"], "fresh": units_to_fresh(it["u"])}
                                for it in reversed(self.hold)]
                    else:
                        lost = list(self.hold[::-1])
                    self.hold = []
                    events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                    self._finish("fainted", events)

    def _hold_free(self) -> int:
        return int(self.t["hold_capacity"]) - len(self.hold)

    def _try_hold(self, action, item_id, amounts, events) -> bool:
        """Thêm nguyên liệu vào giỏ nếu đủ chỗ (LIFO). Đầy -> phát `hold_full`, trả False.

        Seam cho lát 2: hái dùng action="gather" (node_id), bắt cá dùng action="catch" (fish_id).
        `hold_full` mang đúng 4 khoá theo hợp đồng đóng băng §4: action, node_id|fish_id, required, free.
        """
        free = self._hold_free()
        if len(amounts) > free:
            key = "node_id" if action == "gather" else "fish_id"
            events.append(("hold_full", {"action": action, key: item_id,
                                         "required": len(amounts), "free": free}))
            return False
        if self.fresh:  # v1.2: cấp id cá thể mới, độ tươi đầy; hao từ bước sau
            for kind in amounts:
                self.hold.append({"id": self.ids.new("I"), "kind": kind, "u": self.fresh_units})
        else:
            self.hold.extend(amounts)
        return True

    def _decay_hold(self, events):
        """Hao độ tươi giỏ ở đầu bước (v1.2); phát `spoiled` đúng một lần khi vượt ngưỡng (theo id)."""
        if not self.fresh:
            return
        for it in sort_by_id(self.hold):
            prev = it["u"]
            it["u"] = max(0, it["u"] - self.decay_units)
            if prev >= self.spoiled_units and it["u"] < self.spoiled_units:
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
