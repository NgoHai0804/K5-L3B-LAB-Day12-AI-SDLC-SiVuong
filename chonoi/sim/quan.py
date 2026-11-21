"""Buổi tối — Mở Quán (`quan`).

Lát 4 (Nguyễn Thanh Tùng): bếp nấu (cook_started, dish_ready, ready_ticks), bưng món (dish_picked),
phục vụ & tính boa (served), ăn xong trả tiền & uy tín (paid), dọn bàn hết ca (quan_end).
Lát 3 (Quý Anh): khách đến theo lịch (first_customer_tick, customer_interval_s), chọn món đủ kho khả dụng,
giữ chỗ nguyên liệu, no_dish — `_maybe_spawn_customer` (kiên nhẫn / customer_left ở `_resolve_customers_and_closing`).
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = {k: int(v) for k, v in (inventory if inventory is not None else scenario.get("stock", {})).items() if v > 0}
        self.hand = dict(scenario["hand"]) if scenario.get("hand") is not None else None
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.random_customers = scenario.get("random_customers", True)
        self.stoves = [
            {
                "id": s["id"],
                "pos": [float(c) for c in s["pos"]],
                "state": s.get("state", "idle"),
                "dish": dict(s["dish"]) if s.get("dish") is not None else None,
                "cook_ticks_left": int(s.get("cook_ticks_left", 0)),
                "ready_ticks": int(s.get("ready_ticks", 0)),
            }
            for s in self._merge(t["stoves"], scenario.get("stoves", []))
        ]
        self.tables = [
            {"id": tb["id"], "pos": [float(c) for c in tb["pos"]]}
            for tb in self._merge(t["tables"], scenario.get("tables", []))
        ]
        self.customers = self._init_customers(scenario.get("customers", []))
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _init_customers(self, raw_customers):
        pat_max = int(round(self.t["patience_s"] * TICK))
        customers = []
        for raw in raw_customers:
            state = raw.get("state", "waiting")
            default_status = "served" if state == "eating" else "reserved"
            order_status = raw.get("order_status", default_status)
            default_pat = 0 if state == "eating" else pat_max
            has_reserved = "reserved" in raw and raw["reserved"] is not None
            c = {
                "id": raw["id"],
                "table_id": raw["table_id"],
                "dish_id": raw.get("dish_id"),
                "order_tick": int(raw.get("order_tick", 0)),
                "state": state,
                "patience_ticks_left": int(raw.get("patience_ticks_left", default_pat)),
                "eat_ticks_left": int(raw.get("eat_ticks_left", 0)),
                "order_status": order_status,
                "reserved": {k: int(v) for k, v in raw["reserved"].items() if v > 0} if has_reserved else None,
                "base_price": raw.get("base_price"),
                "tip": raw.get("tip"),
            }
            customers.append(c)
        # Thiếu reserved ở đơn reserved -> cấp theo công thức theo (order_tick, id bàn)
        for c in sorted(customers, key=lambda x: (x["order_tick"], id_key(x["table_id"]))):
            if c["reserved"] is None:
                if c["order_status"] == "reserved" and c["dish_id"] in self.menu:
                    c["reserved"] = {k: int(v) for k, v in self.menu[c["dish_id"]]["recipe"].items() if v > 0}
                else:
                    c["reserved"] = {}
        return sort_by_id(customers)

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel)},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": dict(self.hand) if self.hand is not None else None,
            "stoves": [
                {
                    "id": s["id"],
                    "pos": list(s["pos"]),
                    "state": s["state"],
                    "dish": dict(s["dish"]) if s["dish"] is not None else None,
                    "cook_ticks_left": s["cook_ticks_left"],
                    "ready_ticks": s["ready_ticks"],
                }
                for s in sort_by_id(self.stoves)
            ],
            "tables": [
                {"id": tb["id"], "pos": list(tb["pos"]), "customer_id": occupied.get(tb["id"])}
                for tb in sort_by_id(self.tables)
            ],
            "customers": [
                {
                    "id": c["id"],
                    "table_id": c["table_id"],
                    "dish_id": c["dish_id"],
                    "order_tick": c["order_tick"],
                    "state": c["state"],
                    "patience_ticks_left": c["patience_ticks_left"],
                    "eat_ticks_left": c["eat_ticks_left"],
                    "order_status": c["order_status"],
                    "reserved": {k: c["reserved"][k] for k in sorted(c["reserved"]) if c["reserved"][k] > 0},
                    "base_price": c["base_price"],
                    "tip": c["tip"],
                }
                for c in sort_by_id(self.customers)
            ],
        }

    def step(self, inp):
        events = []
        # 1. Tăng đồng hồ, giảm timer ca, nấu, ăn và kiên nhẫn.
        #    Chỉ tăng ready_ticks cho món đã ready ở ĐẦU bước.
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
            elif c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

        # 2. Xét bếp theo id. Món nấu xong chuyển ready với ready_ticks = 0 (burn_s: null).
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                dish = s["dish"]
                events.append((
                    "dish_ready",
                    {"stove_id": s["id"], "order_id": dish["order_id"], "dish_id": dish["dish_id"]},
                ))

        # 3. Di chuyển rồi xét tối đa một interact theo (khoảng cách, bếp trước bàn, id).
        self._move(inp)
        if inp.pressed("interact"):
            self._handle_interact(events)

        # 4. Theo id bàn: ăn xong trả tiền; còn giờ -> hết kiên nhẫn rời; hết ca -> đóng ca & quan_end.
        if self._resolve_customers_and_closing(events):
            return events

        # 5. Nếu còn giờ, xét lượt khách mới theo lịch (Lát 3).
        self._maybe_spawn_customer(events)
        return events

    # --- Lát 4: bếp, bưng, phục vụ, thu tiền, hết ca ---------------------------
    def _handle_interact(self, events):
        radius = float(self.t["interact_radius"])
        candidates = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= radius:
                candidates.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= radius:
                candidates.append((d, 1, id_key(tb["id"]), "table", tb))
        if not candidates:
            return
        candidates.sort(key=lambda x: (x[0], x[1], x[2]))
        _, _, _, kind, target = candidates[0]
        if kind == "stove":
            if target["state"] == "idle":
                self._try_start_cook(target, events)
            elif target["state"] == "ready":
                self._try_pick_dish(target, events)
        else:
            self._try_serve_table(target, events)

    def _try_start_cook(self, stove, events):
        reserved_orders = [
            c for c in self.customers
            if c["state"] == "waiting" and c["order_status"] == "reserved" and c.get("dish_id") in self.menu
        ]
        if not reserved_orders:
            return
        reserved_orders.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        cust = reserved_orders[0]
        dish_id = cust["dish_id"]
        dish_cfg = self.menu[dish_id]
        used = dict(cust["reserved"])
        items = []
        for k in sorted(used):
            qty = int(used[k])
            if qty <= 0:
                continue
            rem = self.stock.get(k, 0) - qty
            if rem > 0:
                self.stock[k] = rem
            else:
                self.stock.pop(k, None)
            items.extend([k] * qty)
        cust["reserved"] = {}
        cust["order_status"] = "assigned"
        base_price = int(dish_cfg["price"])
        cook_ticks = int(round(dish_cfg["cook_s"] * TICK))
        stove["state"] = "cooking"
        stove["dish"] = {"order_id": cust["id"], "dish_id": dish_id, "base_price": base_price}
        stove["cook_ticks_left"] = cook_ticks
        stove["ready_ticks"] = 0
        events.append((
            "cook_started",
            {
                "stove_id": stove["id"],
                "order_id": cust["id"],
                "dish_id": dish_id,
                "items": items,
                "base_price": base_price,
            },
        ))

    def _try_pick_dish(self, stove, events):
        if self.hand is not None or stove["dish"] is None:
            return
        dish = dict(stove["dish"])
        self.hand = dish
        stove["state"] = "idle"
        stove["dish"] = None
        stove["cook_ticks_left"] = 0
        stove["ready_ticks"] = 0
        events.append((
            "dish_picked",
            {"stove_id": stove["id"], "order_id": dish["order_id"], "dish_id": dish["dish_id"]},
        ))

    def _try_serve_table(self, table, events):
        if self.hand is None:
            return
        cust = next((c for c in self.customers if c["table_id"] == table["id"]), None)
        if cust is None or cust["state"] != "waiting" or cust["id"] != self.hand.get("order_id"):
            return
        patience_max = int(round(self.t["patience_s"] * TICK))
        patience_left = cust["patience_ticks_left"]
        base_price = int(self.hand["base_price"])
        ratio = (patience_left / patience_max) if patience_max > 0 else 0.0
        if ratio >= self.t["tip_min_patience_ratio"]:
            tip = math.floor(base_price * self.t["tip_rate"])
        else:
            tip = 0
        cust["state"] = "eating"
        cust["order_status"] = "served"
        cust["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
        cust["base_price"] = base_price
        cust["tip"] = tip
        self.hand = None
        events.append((
            "served",
            {
                "order_id": cust["id"],
                "table_id": table["id"],
                "dish_id": cust["dish_id"],
                "patience_ticks_left": patience_left,
                "base_price": base_price,
                "tip": tip,
            },
        ))

    def _resolve_customers_and_closing(self, events) -> bool:
        by_table = {c["table_id"]: c for c in self.customers}
        removed_ids = set()

        # 4a. Khách ăn xong trả tiền rồi rời bàn ngay (theo id bàn).
        for tb in sort_by_id(self.tables):
            c = by_table.get(tb["id"])
            if c is not None and c["state"] == "eating" and c["eat_ticks_left"] == 0:
                self._collect_payment(c, "finished_eating", events)
                removed_ids.add(c["id"])
                del by_table[tb["id"]]

        # 4b. Còn giờ: khách waiting hết kiên nhẫn rời bàn & cập nhật uy tín.
        if self.time_left_ticks > 0:
            for tb in sort_by_id(self.tables):
                c = by_table.get(tb["id"])
                if c is not None and c["state"] == "waiting" and c["patience_ticks_left"] == 0:
                    self.reputation = self._clamp_rep(self.reputation + self.t["left_reputation_delta"])
                    self._cleanup_customer_order(c)
                    events.append((
                        "customer_left",
                        {
                            "order_id": c["id"],
                            "table_id": c["table_id"],
                            "reason": "patience",
                            "reputation": self.reputation,
                        },
                    ))
                    removed_ids.add(c["id"])
                    del by_table[tb["id"]]
            if removed_ids:
                self.customers = [c for c in self.customers if c["id"] not in removed_ids]
            return False

        # 4c. Hết ca: khách còn ăn trả ngay (reason: closing); khách còn chờ rời (closing, không trừ uy tín).
        for tb in sort_by_id(self.tables):
            c = by_table.get(tb["id"])
            if c is None:
                continue
            if c["state"] == "eating":
                self._collect_payment(c, "closing", events)
            else:
                self._cleanup_customer_order(c)
                events.append((
                    "customer_left",
                    {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "closing",
                        "reputation": self.reputation,
                    },
                ))
            removed_ids.add(c["id"])
        self.customers = [c for c in self.customers if c["id"] not in removed_ids]
        self.done = True
        self.reason = "time"
        events.append((
            "quan_end",
            {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
            },
        ))
        return True

    def _collect_payment(self, cust, reason, events):
        base_price = int(cust["base_price"] or 0)
        tip = int(cust["tip"] or 0)
        amount = base_price + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if tip > 0:
            self.reputation = self._clamp_rep(self.reputation + self.t["tip_reputation"])
        events.append((
            "paid",
            {
                "order_id": cust["id"],
                "table_id": cust["table_id"],
                "base_price": base_price,
                "tip": tip,
                "amount": amount,
                "reason": reason,
            },
        ))

    def _cleanup_customer_order(self, cust):
        # Nhả phần giữ thô (nguyên liệu đã tiêu ở bếp không hoàn lại) và bỏ món trên bếp/tay của đơn này.
        cust["reserved"] = {}
        order_id = cust["id"]
        for s in self.stoves:
            if s["dish"] is not None and s["dish"].get("order_id") == order_id:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
        if self.hand is not None and self.hand.get("order_id") == order_id:
            self.hand = None

    def _clamp_rep(self, value: float) -> float:
        lo = float(self.t["reputation_min"])
        hi = float(self.t["reputation_max"])
        return max(lo, min(hi, value))

    # --- Lát 3 (Quý Anh): khách theo lịch, giữ chỗ nguyên liệu ---------------------
    def _available_stock(self) -> dict:
        """Kho khả dụng = tồn vật lý trừ tổng phần đang giữ của mọi đơn."""
        avail = dict(self.stock)
        for c in self.customers:
            for k, qty in c["reserved"].items():
                avail[k] = avail.get(k, 0) - qty
        return {k: v for k, v in avail.items() if v > 0}

    @staticmethod
    def _can_reserve(recipe: dict, avail: dict) -> bool:
        return all(avail.get(k, 0) >= qty for k, qty in recipe.items())

    def _customer_due(self) -> bool:
        """Lượt khách ở first_customer_tick rồi mỗi customer_interval_s × 60 tick, tính theo phase_tick sau tăng."""
        first_tick = int(self.t["first_customer_tick"])
        interval_ticks = int(round(self.t["customer_interval_s"] * TICK))
        if self.phase_tick < first_tick:
            return False
        return (self.phase_tick - first_tick) % interval_ticks == 0

    def _maybe_spawn_customer(self, events):
        # Gọi ở cuối bước, chỉ khi ca còn giờ (bước 4 đã return nếu đóng ca).
        if not self.random_customers or not self._customer_due():
            return
        occupied = {c["table_id"] for c in self.customers}
        empty_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not empty_tables:
            return  # không còn bàn: bỏ lượt, không phát event
        table = empty_tables[0]  # bàn trống id nhỏ nhất
        avail = self._available_stock()
        # Duyệt id món theo mã Unicode (thứ tự cố định) rồi chọn đều theo seed trong các món đủ kho khả dụng.
        cookable = [d for d in sorted(self.menu) if self._can_reserve(self.menu[d]["recipe"], avail)]
        if not cookable:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_spawn").choice(cookable)
        order_id = self.ids.new("C")
        reserved = {k: int(v) for k, v in self.menu[dish_id]["recipe"].items() if v > 0}
        self.customers.append({
            "id": order_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),  # đầy, giảm từ bước sau
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": reserved,  # giữ đúng công thức ngay khi gọi
            "base_price": None,
            "tip": None,
        })
        self.customers = sort_by_id(self.customers)
        events.append(("customer_arrived", {"order_id": order_id, "table_id": table["id"], "dish_id": dish_id}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
