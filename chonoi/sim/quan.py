"""Buổi tối — Mở Quán (`quan`), Test Contract v1.2. Nhìn từ trên xuống, vị trí `[x, z]` (z hướng bắc).

Thứ tự một bước (Ticket-03, Quán):
  1. đồng hồ và timer: phase_tick, ca, nấu, ăn, kiên nhẫn; ready_ticks +1 cho món đã ready
  2. hao tươi kho thô −0.25/s (kể cả hàng đang giữ), phát hết `spoiled` theo id, rồi xử lý các đơn có phần
     giữ vừa ươn theo (order_tick, id bàn): nhả toàn bộ, thử giữ lại đúng một lần; thiếu -> unfulfillable
  3. bếp theo id: nấu xong -> ready (burn_s = null, không cháy)
  4. di chuyển, rồi tối đa MỘT interact (khoảng cách, bếp trước bàn, id)
       bếp idle  -> lấy đơn reserved cũ nhất (order_tick, id bàn), tiêu ĐÚNG các id đang giữ,
                    chốt base_price = floor(giá × trung bình fresh / 100)
       bếp ready -> giao món cho tay trống; bàn -> tay cầm đúng order_id -> served (boa chốt ở đây)
  5. theo id bàn: ăn xong -> paid; còn giờ: hết kiên nhẫn -> customer_left (patience) và trừ uy tín.
     Hết ca: khách ăn trả ngay, khách chờ rời (closing, không trừ uy tín), quan_end.
  6. còn giờ: lượt khách (tick 120 + 900·k) vào bàn trống id nhỏ nhất, chọn đều theo seed trong các món
     (của kế hoạch Ngày nếu chạy day) đủ nguyên liệu KHẢ DỤNG (chưa ươn, chưa bị giữ); không có -> no_dish.

Kho `stock` là danh sách cá thể vật lý {id, kind, fresh} (gồm phần đang giữ). Giữ chỗ theo id cá thể.

Sáng tạo (CHỈ khi truyền `extras`, headless không truyền):
  - `extras.early_close`: cạnh `close_shift` khi quán không còn khách -> đóng ca sớm, quan_end reason "early".
  - `extras.collide`: không đi xuyên bếp/quầy (hộp chặn quanh vị trí), chỉ chặn trục bị va.
  - `extras.prep`: `inp.prep = {stove_id, quality ∈ [0,1]}` (minigame băm/chặt ở client) cho món đang nấu
    -> bớt tối đa 40% thời gian nấu, mỗi món một lần, phát `prep_done`.
"""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import item_out, to_fraction, validate_items
from .ramp import ramp_velocity

TICK = 60
CUSTOMER_PREFIX = "C"
CUSTOMER_KEYS = ("id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip")


def _ticks(seconds) -> int:
    return int(round(seconds * TICK))


_exact = to_fraction


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, plan_dishes=None,
                 money=0, earned=0, reputation=None, extras=None):
        self.extras = extras or {}
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        fr = tuning["freshness"]
        self.decay = to_fraction(fr["quan_decay_per_s"]) / TICK
        self.spoil_at = to_fraction(fr["spoiled_below"])
        self.plan_dishes = sorted(plan_dishes) if plan_dishes is not None else None
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        if inventory is not None:
            self.stock = [dict(it) for it in inventory]
        else:
            self.stock = validate_items(scenario.get("stock", []))
        for it in self.stock:
            ids.reserve(it["id"])
        self.hand = scenario.get("hand")
        self.duration_ticks = _ticks(t["duration_s"])
        self.time_left_ticks = scenario.get("time_left_ticks", self.duration_ticks)
        rep = reputation if reputation is not None else scenario.get("reputation", t["reputation_initial"])
        self.reputation = float(rep)
        self.random_customers = scenario.get("random_customers", True)
        self.patience_max = _ticks(t["patience_s"])
        self.eat_ticks = _ticks(t["eat_s"])
        self.interval_ticks = _ticks(t["customer_interval_s"])
        self.phase_tick = 0
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [self._fixture_customer(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
            if self.plan_dishes is not None and e["dish_id"] not in self.plan_dishes:
                raise BadInput(f"customers.{e['id']}: món không thuộc kế hoạch Ngày")
        self._fill_reserved()
        self._validate_links()
        self.money = money
        self.earned = earned
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # --- dựng fixture -----------------------------------------------------------------
    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _fixture_customer(self, c):
        cust = {
            "id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
            "order_tick": c.get("order_tick", 0), "state": c.get("state", "waiting"),
            "patience_ticks_left": c.get("patience_ticks_left", self.patience_max),
            "eat_ticks_left": c.get("eat_ticks_left", 0), "order_status": c.get("order_status", "reserved"),
            "reserved": list(c["reserved"]) if "reserved" in c else None,
            "base_price": c.get("base_price"), "tip": c.get("tip"),
        }
        if cust["patience_ticks_left"] > self.patience_max:
            raise BadInput(f"customers.{c['id']}: patience_ticks_left vượt kiên nhẫn tối đa")
        if cust["eat_ticks_left"] > self.eat_ticks:
            raise BadInput(f"customers.{c['id']}: eat_ticks_left vượt thời gian ăn")
        return cust

    def _fill_reserved(self):
        """Kiểm phần giữ khai sẵn; đơn reserved thiếu `reserved` -> cấp theo (order_tick, id bàn), tươi nhất rồi id."""
        by_id = {it["id"]: it for it in self.stock}
        used = set()
        for c in self.customers:
            if c["reserved"] is None:
                continue
            for iid in c["reserved"]:
                it = by_id.get(iid)
                if it is None:
                    raise BadInput(f"customers.{c['id']}: reserved trỏ tới cá thể không có trong kho: {iid}")
                if iid in used:
                    raise BadInput(f"cá thể {iid} bị giữ bởi hai đơn")
                if it["fresh"] < self.spoil_at:
                    raise BadInput(f"customers.{c['id']}: không được giữ cá thể đã ươn {iid}")
                used.add(iid)
        order = sorted(self.customers, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        for c in order:
            if c["reserved"] is not None:
                continue
            if c["order_status"] != "reserved":
                c["reserved"] = []
                continue
            got = self._pick(self.menu[c["dish_id"]]["recipe"])
            if got is None:
                raise BadInput(f"customers.{c['id']}: kho không đủ để giữ công thức")
            c["reserved"] = got
        for c in self.customers:
            c["reserved"] = sorted(c["reserved"], key=id_key)

    def _validate_links(self):
        by_id = {c["id"]: c for c in self.customers}
        stock_by_id = {it["id"]: it for it in self.stock}
        holders = {}

        def check_payload(where, d):
            if not isinstance(d, dict) or set(d) != {"order_id", "dish_id", "base_price"}:
                raise BadInput(f"{where}: món phải là {{order_id, dish_id, base_price}}")
            c = by_id.get(d["order_id"])
            if c is None:
                raise BadInput(f"{where}: order_id {d['order_id']!r} không có khách tương ứng")
            if d["dish_id"] != c["dish_id"]:
                raise BadInput(f"{where}: món không khớp đơn {c['id']}")
            bp = d["base_price"]
            if isinstance(bp, bool) or not isinstance(bp, int) or bp <= 0:
                raise BadInput(f"{where}: base_price phải là số nguyên dương")
            if c["order_status"] != "assigned":
                raise BadInput(f"{where}: đơn {c['id']} phải ở trạng thái assigned")
            if d["order_id"] in holders:
                raise BadInput(f"đơn {d['order_id']} có món ở cả {holders[d['order_id']]} và {where}")
            holders[d["order_id"]] = where

        for s in self.stoves:
            st = s["state"]
            if st == "idle":
                if s["dish"] is not None or s["cook_ticks_left"] != 0 or s["ready_ticks"] != 0:
                    raise BadInput(f"bếp {s['id']} idle không được có món/bộ đếm")
            else:
                if s["dish"] is None:
                    raise BadInput(f"bếp {s['id']} {st} phải có món")
                check_payload(f"bếp {s['id']}", s["dish"])
                if st == "cooking" and (s["cook_ticks_left"] <= 0 or s["ready_ticks"] != 0):
                    raise BadInput(f"bếp {s['id']} cooking cần cook_ticks_left > 0 và ready_ticks = 0")
                if st == "ready" and s["cook_ticks_left"] != 0:
                    raise BadInput(f"bếp {s['id']} ready phải có cook_ticks_left = 0")
        if self.hand is not None:
            check_payload("tay", self.hand)
        for c in self.customers:
            cid, status, state = c["id"], c["order_status"], c["state"]
            if status == "reserved":
                kinds = {}
                for iid in c["reserved"]:
                    k = stock_by_id[iid]["kind"]
                    kinds[k] = kinds.get(k, 0) + 1
                if kinds != dict(self.menu[c["dish_id"]]["recipe"]):
                    raise BadInput(f"customers.{cid}: giữ chỗ khác công thức")
            elif c["reserved"]:
                raise BadInput(f"customers.{cid}: đơn {status} phải có reserved rỗng")
            if status == "assigned" and cid not in holders:
                raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món ở bếp hoặc tay")
            if state == "eating":
                if status != "served" or c["eat_ticks_left"] <= 0:
                    raise BadInput(f"customers.{cid}: khách eating phải served và có eat_ticks_left > 0")
                for k in ("base_price", "tip"):
                    v = c[k]
                    if isinstance(v, bool) or not isinstance(v, int) or v < 0 or (k == "base_price" and v == 0):
                        raise BadInput(f"customers.{cid}: khách eating phải khai {k} đã chốt")
            else:
                if status == "served":
                    raise BadInput(f"customers.{cid}: đơn served phải đang eating")
                if c["eat_ticks_left"] != 0:
                    raise BadInput(f"customers.{cid}: khách chờ không có eat_ticks_left")

    # --- kho ------------------------------------------------------------------------------
    def _reserved_ids(self):
        out = set()
        for c in self.customers:
            out.update(c["reserved"] or ())
        return out

    def available_items(self):
        held = self._reserved_ids()
        return [it for it in self.stock if it["id"] not in held and it["fresh"] >= self.spoil_at]

    def available(self) -> dict:
        out = {}
        for it in self.available_items():
            out[it["kind"]] = out.get(it["kind"], 0) + 1
        return out

    def _pick(self, recipe):
        """Chọn id cá thể khả dụng tươi nhất (hòa theo id) cho công thức; thiếu -> None."""
        avail = self.available_items()
        got = []
        for kind in sorted(recipe):
            cands = sorted((it for it in avail if it["kind"] == kind), key=lambda it: (-it["fresh"], id_key(it["id"])))
            n = recipe[kind]
            if len(cands) < n:
                return None
            got.extend(it["id"] for it in cands[:n])
        return got

    # --- snapshot ------------------------------------------------------------------------
    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        custs = []
        for c in sort_by_id(self.customers):
            row = {k: c[k] for k in CUSTOMER_KEYS}
            row["reserved"] = list(c["reserved"])
            custs.append(row)
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": [item_out(it) for it in sort_by_id(self.stock)],
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": custs,
        }

    # --- một bước --------------------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, nấu, ăn, kiên nhẫn
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # 2. hao tươi + giữ chỗ bị ươn
        self._decay(events)
        # 3. bếp chín
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", self._dish_data(s)))
        # 3b. (sáng tạo) sơ chế nhanh
        prep = getattr(inp, "prep", None)
        if self.extras.get("prep") and isinstance(prep, dict):
            self._prep(prep, events)
        # 4. di chuyển rồi tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # 5. thanh toán / khách rời / đóng ca
        early = (self.extras.get("early_close") and inp.pressed("close_shift") and not self.customers)
        closing = self.time_left_ticks <= 0 or early
        for tb in self.tables:
            c = self._at_table(tb["id"])
            if c is None:
                continue
            if c["state"] == "eating":
                if c["eat_ticks_left"] == 0:
                    self._pay(c, "finished_eating", events)
                elif closing:
                    self._pay(c, "closing", events)
            elif closing:
                self._leave(c, "closing", events)
            elif c["patience_ticks_left"] == 0:
                self._leave(c, "patience", events)
        if closing:
            # dọn món và phần giữ của đơn đã rời (stock giữ nguyên hàng thô còn lại)
            for s in self.stoves:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
            self.hand = None
            reason = "time" if self.time_left_ticks <= 0 else "early"
            self.done, self.reason = True, reason
            events.append(("quan_end", {"reason": reason, "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 6. khách mới theo lịch
        if self.random_customers and self._customer_due():
            self._spawn(events)
        return events

    def _prep(self, prep, events):
        st = next((s for s in self.stoves if s["id"] == prep.get("stove_id")), None)
        q = prep.get("quality")
        if st is None or st["state"] != "cooking" or st.get("_prepped") or not isinstance(q, (int, float)):
            return
        q = min(1.0, max(0.0, float(q)))
        total = _ticks(self.menu[st["dish"]["dish_id"]]["cook_s"])
        saved = min(st["cook_ticks_left"] - 1, int(total * 0.4 * q))
        st["_prepped"] = True
        if saved > 0:
            st["cook_ticks_left"] -= saved
        events.append(("prep_done", {"stove_id": st["id"], "dish_id": st["dish"]["dish_id"], "quality": round(q, 2),
                                     "saved_ticks": max(0, saved)}))

    def _decay(self, events):
        spoiled = []
        for it in self.stock:
            before = it["fresh"]
            it["fresh"] = max(Fraction(0), before - self.decay)
            if before >= self.spoil_at > it["fresh"]:
                spoiled.append(it)
        if not spoiled:
            return
        for it in sorted(spoiled, key=lambda i: id_key(i["id"])):
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))
        bad = {it["id"] for it in spoiled}
        hit = [c for c in self.customers if c["order_status"] == "reserved" and bad & set(c["reserved"])]
        for c in sorted(hit, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            c["reserved"] = []
            got = self._pick(self.menu[c["dish_id"]]["recipe"])
            if got is None:
                c["order_status"] = "unfulfillable"
            else:
                c["reserved"] = sorted(got, key=id_key)

    # --- tương tác ---------------------------------------------------------------------------
    def _interact(self, events):
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                cands.append(((d, 0, id_key(s["id"])), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                cands.append(((d, 1, id_key(tb["id"])), "table", tb))
        if not cands:
            return
        _, kind, obj = min(cands, key=lambda x: x[0])
        if kind == "stove":
            if obj["state"] == "idle":
                self._start_cooking(obj, events)
            elif obj["state"] == "ready" and self.hand is None:
                self.hand = obj["dish"]
                events.append(("dish_picked", self._dish_data(obj)))
                obj.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        else:
            c = self._at_table(obj["id"])
            if c and c["state"] == "waiting" and self.hand and self.hand["order_id"] == c["id"]:
                self._serve(c, events)

    def _start_cooking(self, stove, events):
        waiting = [c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"]
        if not waiting:
            return
        c = min(waiting, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        ids = set(c["reserved"])
        used = [it for it in self.stock if it["id"] in ids]
        self.stock = [it for it in self.stock if it["id"] not in ids]
        dish = self.menu[c["dish_id"]]
        mean = sum((it["fresh"] for it in used), Fraction(0)) / len(used)
        price = math.floor(int(dish["price"]) * mean / 100)
        c["reserved"], c["order_status"], c["base_price"] = [], "assigned", price
        stove.update(state="cooking", dish={"order_id": c["id"], "dish_id": c["dish_id"], "base_price": price},
                     cook_ticks_left=_ticks(dish["cook_s"]), ready_ticks=0)
        items = [item_out(it) for it in sorted(used, key=lambda it: (it["kind"], id_key(it["id"])))]
        events.append(("cook_started", dict(self._dish_data(stove), items=items, base_price=price)))

    def _serve(self, c, events):
        payload, self.hand = self.hand, None
        base = int(payload["base_price"])
        ratio = Fraction(c["patience_ticks_left"], self.patience_max)
        tip = math.floor(base * _exact(self.t["tip_rate"])) if ratio >= _exact(self.t["tip_min_patience_ratio"]) else 0
        c.update(state="eating", order_status="served", eat_ticks_left=self.eat_ticks, base_price=base, tip=tip)
        events.append(("served", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"], "base_price": base, "tip": tip}))

    # --- tiền / uy tín / khách rời --------------------------------------------------------------
    def _pay(self, c, reason, events):
        base, tip = int(c["base_price"]), int(c["tip"])
        amount = base + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if tip > 0:
            self._add_reputation(self.t["tip_reputation"])
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"],
                                "base_price": base, "tip": tip, "amount": amount, "reason": reason}))
        self._remove(c)

    def _leave(self, c, reason, events):
        if reason == "patience":
            self._add_reputation(self.t["left_reputation_delta"])
        for s in self.stoves:
            if s["dish"] and s["dish"]["order_id"] == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand and self.hand["order_id"] == c["id"]:
            self.hand = None
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))
        self._remove(c)

    def _add_reputation(self, delta):
        lo, hi = self.t["reputation_min"], self.t["reputation_max"]
        self.reputation = float(min(hi, max(lo, round(self.reputation + delta, 9))))

    def _remove(self, c):
        self.customers = [x for x in self.customers if x is not c]

    # --- khách mới ----------------------------------------------------------------------------
    def _customer_due(self) -> bool:
        first = int(self.t["first_customer_tick"])
        k = self.phase_tick - first
        return k >= 0 and k % self.interval_ticks == 0

    def _spawn(self, events):
        taken = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in taken]
        if not free:
            return
        table = free[0]
        avail = self.available()
        pool = self.plan_dishes if self.plan_dishes is not None else sorted(self.menu)
        dishes = [d for d in pool if all(avail.get(k, 0) >= n for k, n in self.menu[d]["recipe"].items())]
        if not dishes:
            events.append(("no_dish", {}))
            return
        dish_id = dishes[self.rng.get("customers").randrange(len(dishes))]
        cid = self.ids.new(CUSTOMER_PREFIX)
        reserved = sorted(self._pick(self.menu[dish_id]["recipe"]), key=id_key)
        self.customers.append({
            "id": cid, "table_id": table["id"], "dish_id": dish_id, "order_tick": self.phase_tick,
            "state": "waiting", "patience_ticks_left": self.patience_max, "eat_ticks_left": 0,
            "order_status": "reserved", "reserved": reserved, "base_price": None, "tip": None,
        })
        events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    # --- tiện ích ---------------------------------------------------------------------------------
    def _at_table(self, table_id):
        for c in self.customers:
            if c["table_id"] == table_id:
                return c
        return None

    @staticmethod
    def _dish_data(stove):
        d = stove["dish"]
        return {"stove_id": stove["id"], "order_id": d["order_id"], "dish_id": d["dish_id"]}

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        boxes = self._obstacles() if self.extras.get("collide") else ()
        for i, axis in enumerate(("x", "z")):
            old = self.pos[i]
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
            if boxes and any(self._inside(bx) for bx in boxes):
                self.pos[i], self.vel[i] = old, 0.0

    # hộp chặn (nửa rộng x, nửa sâu z) + bán kính người chơi; vẫn trong tầm tương tác 1.5 m
    STOVE_HALF, COUNTER_HALF, BODY = (1.1, 0.4), (1.45, 0.4), 0.25

    def _obstacles(self):
        out = [(s["pos"], self.STOVE_HALF) for s in self.stoves]
        out += [(t["pos"], self.COUNTER_HALF) for t in self.tables]
        return out

    def _inside(self, box):
        (cx, cz), (hx, hz) = box
        return abs(self.pos[0] - cx) < hx + self.BODY and abs(self.pos[1] - cz) < hz + self.BODY
