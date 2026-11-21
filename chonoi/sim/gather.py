"""Buổi sáng — Lặn & Hái (`gather`), Test Contract v1.2.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Thứ tự một bước (Ticket-03 "Thứ tự trong tick", Gather):
  1. đồng hồ, phase_tick, cooldown, giảm bất tử, nút mọc lại, hao tươi hàng có sẵn (spoiled theo id)
  2. bơi, oxy, ngạt (Máu 0 -> faint + gather_end, bỏ các bước còn lại)
  3. thủy quái theo id rồi tối đa một hit (Máu 0 -> faint + gather_end)
  4. interact: bến trước, rồi hái (chỉ ở mặt nước)
  5. bắt cá theo vị trí cá TRƯỚC khi cá bơi
  6. hết giờ -> gather_end(time); nếu còn giờ: cá bơi, sinh thêm theo lịch

Giỏ là danh sách cá thể {id, kind, fresh} theo thứ tự vào giỏ (mất hàng theo LIFO).
Độ tươi giữ bằng Fraction: −0.5/s = −1/120 mỗi tick, kẹp đáy 0; ươn khi < 30.

Sáng tạo (CHỈ khi truyền `extras`, headless không bao giờ truyền): sprint — giữ nút `sprint` để bơi ×1.5,
oxy dưới nước tốn ×1.5, tiêu thể lực; hết thể lực phải hồi tới 30% mới sprint lại. Thả đồ (`extras.drop`):
`inp.drop` = id cá thể hoặc True (món nhặt sau cùng) -> bỏ khỏi giỏ, phát `dropped`.
"""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import fresh_out, hold_to_items, item_out, to_fraction, validate_items
from .ramp import ramp_velocity

TICK = 60
AXES = ("x", "d")
ITEM_PREFIX = "I"
FISH_PREFIX = "F"
MONSTER_STATES = ("patrol", "chase", "recoil")

SPRINT_DEFAULT = {"speed_mult": 1.5, "oxygen_mult": 1.5, "stamina_max": 100.0,
                  "drain_per_s": 100.0 / 3.0, "regen_per_s": 25.0, "regen_delay_ticks": 30, "resume_ratio": 0.3}


def _unit(vx, vy):
    n = math.hypot(vx, vy)
    return (vx / n, vy / n) if n > 0 else (1.0, 0.0)


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, active=None, hold=None, extras=None):
        t = tuning["gather"]
        self.t = t
        self.tuning = tuning
        self.rng = streams
        self.ids = ids
        self.day = day
        active = active or {}
        fr = tuning["freshness"]
        self.decay = to_fraction(fr["gather_decay_per_s"]) / TICK
        self.spoil_at = to_fraction(fr["spoiled_below"])
        self.fresh0 = to_fraction(fr["initial"])
        self.hp_max = int(active.get("hp_max", t["hp_max"]))
        self.oxygen_max = int(round(active.get("oxygen_max_s", t["oxygen_max_s"]) * TICK))
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        if self.oxygen_ticks > self.oxygen_max:
            raise BadInput("player.oxygen_ticks vượt oxy tối đa")
        self.hp = p.get("hp", self.hp_max)
        if not (1 <= self.hp <= self.hp_max):
            raise BadInput("player.hp phải trong [1, hp_max]")
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        # giỏ: cá thể. Ngày đầu giữ id fixture; DaySim truyền `hold` đã cấp id cho các Ngày sau.
        if hold is not None:
            self.hold = hold
        else:
            self.hold = validate_items(scenario.get("hold", []))
        if len(self.hold) > t["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
        for it in self.hold:
            ids.reserve(it["id"])
        self.duration_ticks = int(round(t["duration_s"] * TICK))
        self.time_left_ticks = scenario.get("time_left_ticks", self.duration_ticks)
        self.phase_tick = 0
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        self.random_fish = scenario.get("random_fish", True)
        self.fish = []
        if "fish" in scenario:
            self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                          "heading_deg": float(f.get("heading_deg", 0)), "age_ticks": int(f.get("age_ticks", 0))}
                         for f in scenario["fish"]]
            for f in self.fish:
                ids.reserve(f["id"])
        elif self.random_fish:
            for _ in range(int(t["fish_initial"])):
                self._spawn_fish(None)
        self.monsters = self._build_monsters(scenario)
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None
        # sáng tạo: sprint (chỉ bản chơi)
        self.extras = extras or {}
        self.sprint_cfg = dict(SPRINT_DEFAULT, **self.extras["sprint"]) if "sprint" in self.extras else None
        if self.sprint_cfg:
            self.stamina = self.sprint_cfg["stamina_max"]
            self.sprinting = False
            self.exhausted = False
            self._rest_ticks = 0
            self._oxy_carry = 0.0

    # --- dựng ------------------------------------------------------------------
    def _build_monsters(self, scenario):
        mon = self.t["monsters"]
        species = mon["species"]
        if "monsters" in scenario:
            src = scenario["monsters"]
        else:
            src = [m for m in mon["spawns"] if m.get("from_day", 1) <= self.day]
        out = []
        for m in src:
            if m["kind"] not in species:
                raise BadInput(f"monsters.{m['id']}: kind lạ")
            state = m.get("state", "patrol")
            ticks = int(m.get("state_ticks_left", 0))
            rdir = m.get("recoil_dir")
            if state == "recoil":
                if ticks <= 0 or rdir is None:
                    raise BadInput(f"monsters.{m['id']}: recoil cần state_ticks_left > 0 và recoil_dir")
                rdir = _unit(*rdir)
            out.append({"id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
                        "waypoints": [[float(c) for c in w] for w in m["waypoints"]],
                        "target_idx": int(m.get("target_idx", 1)), "state": state,
                        "state_ticks_left": ticks, "recoil_dir": list(rdir) if rdir else None})
            self.ids.reserve(m["id"])
        return sort_by_id(out)

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> list:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        player = {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                  "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                  "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                  "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                  "at_surface": self._at_surface()}
        if self.sprint_cfg:
            player.update(stamina=self.stamina, stamina_max=self.sprint_cfg["stamina_max"],
                          sprinting=self.sprinting, exhausted=self.exhausted)
        return {
            "player": player,
            "hold": [item_out(it) for it in self.hold], "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"], "waypoints": m["waypoints"],
                          "target_idx": m["target_idx"], "state": m["state"],
                          "state_ticks_left": m["state_ticks_left"], "recoil_dir": m["recoil_dir"]}
                         for m in self.monsters],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, cooldown, nút mọc lại, hao tươi
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        spoiled = []
        for it in self.hold:
            before = it["fresh"]
            it["fresh"] = max(Fraction(0), before - self.decay)
            if before >= self.spoil_at > it["fresh"]:
                spoiled.append(it)
        for it in sorted(spoiled, key=lambda i: id_key(i["id"])):
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))
        # 2. bơi + oxy + ngạt
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif now_surface and not was_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        if self._oxygen(events):
            return events
        # 3. thủy quái
        if self._monsters(events):
            return events
        # 4. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_surface:
                self._harvest(events)
        # 5. bắt cá
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not now_surface:
            self._catch(events)
        # 5b. (sáng tạo) thả đồ nhặt nhầm
        if self.extras.get("drop") and getattr(inp, "drop", None):
            self._drop(inp.drop, events)
        # 6. hết giờ; còn giờ thì cá bơi, sinh thêm
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        if self.random_fish:
            self._swim_fish()
            if self.phase_tick % int(self.t["fish_spawn_ticks"]) == 0 and len(self.fish) < int(self.t["fish_max"]):
                self._spawn_fish(events)
        return events

    # --- oxy / ngạt -------------------------------------------------------------
    def _oxygen(self, events) -> bool:
        t = self.t
        if self._at_surface():
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
            return False
        before = self.oxygen_ticks
        drain = 1
        if self.sprint_cfg and self.sprinting:
            self._oxy_carry += self.sprint_cfg["oxygen_mult"] - 1
            extra = int(self._oxy_carry)
            self._oxy_carry -= extra
            drain += extra
        self.oxygen_ticks = max(0, self.oxygen_ticks - drain)
        if before > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks > 0:
            self.zero_oxy_ticks = 0
            return False
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < int(t["choke_interval_ticks"]):
            return False
        self.zero_oxy_ticks = 0
        self.hp = max(0, self.hp - 1)
        events.append(("choke", {"hp": self.hp}))
        if self.hp > 0:
            return False
        self._faint("choke", events)
        return True

    def _faint(self, cause, events):
        lost = []
        while self.hold:
            lost.append(item_out(self.hold.pop()))
        events.append(("faint", {"cause": cause, "lost": lost, "hp": 0}))
        self._finish("fainted", events)

    # --- thủy quái ----------------------------------------------------------------
    def _clamp_monster(self, m, sp):
        b = self.t["bounds"]
        m["pos"][0] = min(max(m["pos"][0], b["x"][0]), b["x"][1])
        lo, hi = sp["depths"]
        m["pos"][1] = min(max(m["pos"][1], max(lo, b["d"][0])), min(hi, b["d"][1]))

    def _monsters(self, events) -> bool:
        if not self.monsters:
            return False
        species = self.t["monsters"]["species"]
        just_free = set()
        for m in self.monsters:
            sp = species[m["kind"]]
            if m["state"] == "recoil":
                step = sp["recoil_dist"] / sp["recoil_ticks"]
                m["pos"][0] += m["recoil_dir"][0] * step
                m["pos"][1] += m["recoil_dir"][1] * step
                self._clamp_monster(m, sp)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m.update(state="patrol", state_ticks_left=0, recoil_dir=None)
                    just_free.add(m["id"])
                continue
            dist = math.dist(m["pos"], self.pos)
            deep = self.pos[1] >= sp["depths"][0]
            if m["state"] == "patrol" and deep and dist <= sp["detect_radius"]:
                m["state"] = "chase"
            elif m["state"] == "chase" and (dist > sp["exit_radius"] or not deep):
                m["state"] = "patrol"
            if m["state"] == "chase":
                step = min(sp["chase_speed"] / TICK, dist)
                if dist > 0:
                    m["pos"][0] += (self.pos[0] - m["pos"][0]) / dist * step
                    m["pos"][1] += (self.pos[1] - m["pos"][1]) / dist * step
            else:
                wp = m["waypoints"][m["target_idx"]]
                dw = math.dist(m["pos"], wp)
                step = sp["patrol_speed"] / TICK
                if dw <= step:
                    m["pos"] = [wp[0], wp[1]]
                    m["target_idx"] = 1 - m["target_idx"]
                else:
                    m["pos"][0] += (wp[0] - m["pos"][0]) / dw * step
                    m["pos"][1] += (wp[1] - m["pos"][1]) / dw * step
            self._clamp_monster(m, sp)
        if self.invuln_ticks > 0:
            return False
        best = None
        for m in self.monsters:
            sp = species[m["kind"]]
            if m["state"] == "recoil" or m["id"] in just_free or self.pos[1] < sp["depths"][0]:
                continue
            d = math.dist(m["pos"], self.pos)
            if d <= sp["hit_radius"]:
                key = (d, id_key(m["id"]))
                if best is None or key < best[0]:
                    best = (key, m)
        if best is None:
            return False
        m = best[1]
        sp = species[m["kind"]]
        self.hp = max(0, self.hp - 1)
        n_lost = math.floor(len(self.hold) * to_fraction(self.t["monsters"]["loss_ratio"]))
        lost = [item_out(self.hold.pop()) for _ in range(n_lost)]
        self.invuln_ticks = int(self.t["monsters"]["invuln_ticks"])
        m.update(state="recoil", state_ticks_left=int(sp["recoil_ticks"]),
                 recoil_dir=list(_unit(m["pos"][0] - self.pos[0], m["pos"][1] - self.pos[1])))
        events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)}))
        if self.hp == 0:
            self._faint("monster", events)
            return True
        return False

    # --- hái / bắt cá -----------------------------------------------
    def _free(self) -> int:
        return int(self.t["hold_capacity"]) - len(self.hold)

    @staticmethod
    def _nearest(cands, pos, radius):
        best = None
        for e in cands:
            dd = math.dist(pos, e["pos"])
            if dd <= radius:
                key = (dd, id_key(e["id"]))
                if best is None or key < best[0]:
                    best = (key, e)
        return best[1] if best else None

    def _add_items(self, kind, n):
        for _ in range(n):
            self.hold.append({"id": self.ids.new(ITEM_PREFIX), "kind": kind, "fresh": self.fresh0})

    def _harvest(self, events):
        ready = [n for n in self.nodes if n["regrow_ticks"] == 0]
        n = self._nearest(ready, self.pos, self.t["interact_radius"])
        if n is None:
            return
        amount = int(self.t["node_yield"])
        free = self._free()
        if free < amount:
            events.append(("hold_full", {"action": "gather", "node_id": n["id"], "required": amount, "free": free}))
            return
        self._add_items(n["kind"], amount)
        n["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": n["id"], "kind": n["kind"], "amount": amount}))

    def _catch(self, events):
        f = self._nearest(self.fish, self.pos, self.t["catch_radius"])
        if f is None:
            return
        y = int(self.t["fish_yield"][f["kind"]])
        free = self._free()
        if free < y:
            events.append(("hold_full", {"action": "catch", "fish_id": f["id"], "required": y, "free": free}))
            return
        self._add_items(f["kind"], y)
        self.fish = [x for x in self.fish if x is not f]
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": f["id"], "kind": f["kind"], "yield": y}))

    def _drop(self, which, events):
        if not self.hold:
            return
        if which is True:
            it = self.hold[-1]
        else:
            it = next((x for x in self.hold if x["id"] == which), None)
            if it is None:
                return
        self.hold = [x for x in self.hold if x is not it]
        events.append(("dropped", {"item_id": it["id"], "kind": it["kind"], "pos": list(self.pos)}))

    # --- cá bơi / sinh -----------------------------------------------------------
    def _swim_fish(self):
        t = self.t
        step = t["fish_speed"] / TICK
        turn = int(t["fish_turn_ticks"])
        rng = self.rng.get("fish_turn")
        xlo, xhi = t["fish_x"]
        for f in sort_by_id(self.fish):
            n = f["age_ticks"] + 1
            if n % turn == 0:
                f["heading_deg"] = rng.random() * 360.0
            a = math.radians(f["heading_deg"])
            vx, vd = math.cos(a), math.sin(a)
            x = f["pos"][0] + vx * step
            d = f["pos"][1] + vd * step
            dlo, dhi = t["fish_depths"][f["kind"]]
            flip_x = flip_d = False
            if x > xhi:
                x, flip_x = 2 * xhi - x, True
            elif x < xlo:
                x, flip_x = 2 * xlo - x, True
            if d > dhi:
                d, flip_d = 2 * dhi - d, True
            elif d < dlo:
                d, flip_d = 2 * dlo - d, True
            if flip_x or flip_d:
                vx, vd = (-vx if flip_x else vx), (-vd if flip_d else vd)
                f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360
            f["pos"] = [min(max(x, xlo), xhi), min(max(d, dlo), dhi)]
            f["age_ticks"] = n

    def _spawn_fish(self, events):
        """Sinh tối đa một đàn: loài theo trọng số (chỉ loài còn điểm hợp lệ), rồi điểm đều, rồi hướng."""
        t = self.t
        clear = t["fish_spawn_clearance"]
        valid = {}
        for kind in ("ca_linh", "ca_loc", "ca_keo"):
            pts = [[float(x), float(d)] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]]
            pts = [p for p in pts if all(math.dist(p, f["pos"]) > clear for f in self.fish)]
            if pts and t["fish_weights"][kind] > 0:
                valid[kind] = pts
        if not valid:
            return
        rng = self.rng.get("fish_spawn")
        total = sum(t["fish_weights"][k] for k in valid)
        r = rng.random() * total
        kind = None
        for k in valid:
            r -= t["fish_weights"][k]
            if r < 0:
                kind = k
                break
        if kind is None:
            kind = list(valid)[-1]
        pts = valid[kind]
        pos = pts[rng.randrange(len(pts))]
        f = {"id": self.ids.new(FISH_PREFIX), "kind": kind, "pos": pos,
             "heading_deg": rng.random() * 360.0, "age_ticks": 0}
        self.fish.append(f)
        if events is not None:
            events.append(("fish_spawned", {"id": f["id"], "kind": kind, "pos": list(pos)}))

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _sprint_update(self, inp, moving):
        c = self.sprint_cfg
        want = inp.holding("sprint") and moving and not self.exhausted
        if want and self.stamina > 0:
            self.sprinting = True
            self.stamina = max(0.0, self.stamina - c["drain_per_s"] / TICK)
            self._rest_ticks = 0
            if self.stamina == 0:
                self.exhausted = True
        else:
            self.sprinting = False
            self._rest_ticks += 1
            if self._rest_ticks > c["regen_delay_ticks"]:
                self.stamina = min(c["stamina_max"], self.stamina + c["regen_per_s"] / TICK)
            if self.exhausted and self.stamina >= c["stamina_max"] * c["resume_ratio"]:
                self.exhausted = False

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        if self.sprint_cfg:
            self._sprint_update(inp, (mx, md) != (0.0, 0.0))
            if self.sprinting:
                speed *= self.sprint_cfg["speed_mult"]
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


__all__ = ["GatherSim", "fresh_out"]
