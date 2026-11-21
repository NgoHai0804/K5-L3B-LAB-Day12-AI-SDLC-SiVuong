"""Buổi tối — Mở Quán (`quan`), hỗ trợ Test Contract v1.0 / v1.1 (kho đếm) và v1.2 (kho cá thể + độ tươi).

Chế độ nội bộ (chuyển đổi an toàn theo TICKET-03 §3):
- Khi `tuning` có khối `freshness` hoặc `stock`/`inventory` là mảng cá thể `[{id, kind, fresh}]`:
  chạy luật **v1.2** (độ tươi chính xác bằng `Fraction`, hao 0.25/s = 1/240 mỗi tick, ngưỡng ươn < 30,
  phát `spoiled` đúng 1 lần theo id, giữ chỗ theo mảng id cá thể tươi nhất hòa theo id, thử giữ lại 1 lần
  khi có cá thể vừa ươn, chốt `base_price = floor(giá × avg_fresh / 100)` và `cook_started.items` là mảng cá thể).
- Khi `tuning` chưa có `freshness` và `stock` là map đếm `{kind: int}`: giữ nguyên tương thích v1.0/v1.1.
"""

from fractions import Fraction
import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, allowed_dishes=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        # Trong chế độ `day`, lọc menu theo tập id món của kế hoạch ngày; chạy riêng dùng toàn bộ menu.
        self.allowed_dishes = set(allowed_dishes) if allowed_dishes is not None else None
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0

        # Phát hiện chế độ v1.2 (độ tươi + kho cá thể) hay v1.0/v1.1 (kho đếm).
        fresh_cfg = tuning.get("freshness")
        src_stock = inventory if inventory is not None else scenario.get("stock", [] if fresh_cfg else {})
        self.freshness_mode = (fresh_cfg is not None) or isinstance(src_stock, list)
        if self.freshness_mode:
            cfg = fresh_cfg or {}
            self.fresh_initial = Fraction(str(cfg.get("initial", 100)))
            self.quan_decay_per_tick = Fraction(str(cfg.get("quan_decay_per_s", 0.25))) / 60
            self.spoiled_below = Fraction(str(cfg.get("spoiled_below", 30)))
            self.stock_items = self._init_stock_items(src_stock)
            self.stock = {}
        else:
            self.fresh_initial = Fraction(100)
            self.quan_decay_per_tick = Fraction(0)
            self.spoiled_below = Fraction(30)
            self.stock_items = []
            self.stock = {k: int(v) for k, v in src_stock.items() if v > 0}

        self.hand = dict(scenario["hand"]) if scenario.get("hand") is not None else None
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.random_customers = scenario.get("random_customers", True)
        self.burn_ticks = int(round(t["burn_s"] * TICK)) if t.get("burn_s") is not None else None
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

    def _init_stock_items(self, raw_items):
        if not isinstance(raw_items, list):
            raise BadInput("v1.2 yêu cầu stock là mảng cá thể [{id, kind, fresh}]")
        items = []
        seen = set()
        for raw in raw_items:
            if not isinstance(raw, dict):
                raise BadInput("phần tử stock phải là object")
            iid = raw.get("id")
            kind = raw.get("kind")
            fresh = raw.get("fresh")
            if not isinstance(iid, str) or not iid or iid in seen:
                raise BadInput(f"id cá thể không hợp lệ hoặc trùng: {iid!r}")
            if not isinstance(kind, str) or not kind:
                raise BadInput(f"kind cá thể không hợp lệ: {kind!r}")
            if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not math.isfinite(fresh):
                raise BadInput(f"fresh không hợp lệ cho {iid}: {fresh!r}")
            f_exact = Fraction(str(fresh))
            if f_exact < 0 or f_exact > 100:
                raise BadInput(f"fresh ngoài miền [0, 100] cho {iid}: {fresh!r}")
            seen.add(iid)
            self.ids.reserve(iid)
            items.append({"id": iid, "kind": kind, "fresh_exact": f_exact})
        return sort_by_id(items)

    def _init_customers(self, raw_customers):
        pat_max = int(round(self.t["patience_s"] * TICK))
        customers = []
        for raw in raw_customers:
            state = raw.get("state", "waiting")
            default_status = "served" if state == "eating" else "reserved"
            order_status = raw.get("order_status", default_status)
            default_pat = 0 if state == "eating" else pat_max
            has_reserved = "reserved" in raw and raw["reserved"] is not None
            if self.freshness_mode:
                reserved_val = list(raw["reserved"]) if has_reserved else None
            else:
                reserved_val = {k: int(v) for k, v in raw["reserved"].items() if v > 0} if has_reserved else None
            c = {
                "id": raw["id"],
                "table_id": raw["table_id"],
                "dish_id": raw.get("dish_id"),
                "order_tick": int(raw.get("order_tick", 0)),
                "state": state,
                "patience_ticks_left": int(raw.get("patience_ticks_left", default_pat)),
                "eat_ticks_left": int(raw.get("eat_ticks_left", 0)),
                "order_status": order_status,
                "reserved": reserved_val,
                "base_price": raw.get("base_price"),
                "tip": raw.get("tip"),
            }
            customers.append(c)

        if self.freshness_mode:
            by_id = {it["id"]: it for it in self.stock_items}
            used_ids = set()
            # Kiểm tra các đơn có khai reserved tường minh trước.
            for c in customers:
                if c["reserved"] is not None:
                    if not isinstance(c["reserved"], list):
                        raise BadInput(f"customers.{c['id']}.reserved phải là mảng id cá thể ở v1.2")
                    for iid in c["reserved"]:
                        if iid not in by_id:
                            raise BadInput(f"customers.{c['id']}.reserved trỏ tới id không tồn tại: {iid}")
                        if iid in used_ids:
                            raise BadInput(f"cá thể {iid} bị giữ trùng giữa các đơn")
                        if by_id[iid]["fresh_exact"] < self.spoiled_below:
                            raise BadInput(f"customers.{c['id']}.reserved không được giữ cá thể đã ươn: {iid}")
                        used_ids.add(iid)
                    if c["order_status"] == "reserved" and c["dish_id"] in self.menu:
                        counts = {}
                        for iid in c["reserved"]:
                            k = by_id[iid]["kind"]
                            counts[k] = counts.get(k, 0) + 1
                        if counts != self.menu[c["dish_id"]]["recipe"]:
                            raise BadInput(f"customers.{c['id']}.reserved không khớp công thức {c['dish_id']}")
            # Thiếu reserved ở đơn reserved -> cấp theo (order_tick, id bàn), tươi nhất rồi id nhỏ.
            for c in sorted(customers, key=lambda x: (x["order_tick"], id_key(x["table_id"]))):
                if c["reserved"] is None:
                    if c["order_status"] == "reserved" and c["dish_id"] in self.menu:
                        chosen = self._allocate_fresh_recipe(c["dish_id"], exclude_ids=used_ids)
                        if chosen is None:
                            raise BadInput(f"không đủ cá thể tươi để tự cấp reserved cho {c['id']}")
                        c["reserved"] = chosen
                        used_ids.update(chosen)
                    else:
                        c["reserved"] = []
        else:
            # v1.0 / v1.1: thiếu reserved ở đơn reserved -> cấp theo công thức theo (order_tick, id bàn)
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
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    @staticmethod
    def _item_view(it: dict) -> dict:
        return {"id": it["id"], "kind": it["kind"], "fresh": float(it["fresh_exact"])}

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        if self.freshness_mode:
            stock_snap = [self._item_view(it) for it in sort_by_id(self.stock_items)]
        else:
            stock_snap = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel)},
            "stock": stock_snap,
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
                    "reserved": (
                        list(c["reserved"])
                        if self.freshness_mode
                        else {k: c["reserved"][k] for k in sorted(c["reserved"]) if c["reserved"][k] > 0}
                    ),
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

        # 1b. (v1.2) Hao tươi kho thô, phát hết `spoiled` theo id rồi xử lý giữ chỗ bị ươn.
        if self.freshness_mode:
            self._decay_stock_and_refresh_reservations(events)

        # 2. Xét bếp theo id: món nấu xong -> ready (ready_ticks = 0); nếu bật cháy -> xét ready_ticks > burn_ticks.
        self._update_stoves(events)

        # 3. Di chuyển rồi xét tối đa một interact theo (khoảng cách, bếp trước bàn, id).
        self._move(inp)
        if inp.pressed("interact"):
            self._handle_interact(events)

        # 4. Theo id bàn: ăn xong trả tiền; còn giờ -> hết kiên nhẫn rời; hết ca -> đóng ca & quan_end.
        if self._resolve_customers_and_closing(events):
            return events

        # 5. Nếu còn giờ, xét lượt khách mới theo lịch (lọc theo kế hoạch ngày nếu có).
        self._maybe_spawn_customer(events)
        return events

    # --- v1.2: Hao tươi, phát spoiled, giữ chỗ theo cá thể tươi nhất -----------
    def _reserved_item_ids(self) -> set:
        ids = set()
        for c in self.customers:
            if isinstance(c.get("reserved"), list):
                ids.update(c["reserved"])
        return ids

    def _allocate_fresh_recipe(self, dish_id: str, exclude_ids=None):
        if dish_id not in self.menu:
            return None
        recipe = self.menu[dish_id]["recipe"]
        excluded = set(exclude_ids) if exclude_ids is not None else self._reserved_item_ids()
        chosen = []
        for kind in sorted(recipe):
            qty = int(recipe[kind])
            if qty <= 0:
                continue
            pool = [
                it for it in self.stock_items
                if it["kind"] == kind
                and it["id"] not in excluded
                and it["fresh_exact"] >= self.spoiled_below
            ]
            # Lấy các cá thể khả dụng tươi nhất, hòa theo id nhỏ.
            pool.sort(key=lambda it: (-it["fresh_exact"], id_key(it["id"])))
            if len(pool) < qty:
                return None
            picked = [it["id"] for it in pool[:qty]]
            chosen.extend(picked)
            excluded.update(picked)
        chosen.sort(key=id_key)
        return chosen

    def _decay_stock_and_refresh_reservations(self, events):
        newly_spoiled = set()
        for it in sort_by_id(self.stock_items):
            was_fresh = it["fresh_exact"] >= self.spoiled_below
            it["fresh_exact"] = max(Fraction(0), it["fresh_exact"] - self.quan_decay_per_tick)
            if was_fresh and it["fresh_exact"] < self.spoiled_below:
                newly_spoiled.add(it["id"])
                events.append((
                    "spoiled",
                    {"item_id": it["id"], "kind": it["kind"], "location": "stock"},
                ))
        if not newly_spoiled:
            return
        affected = [
            c for c in self.customers
            if c["state"] == "waiting"
            and c["order_status"] == "reserved"
            and any(iid in newly_spoiled for iid in c["reserved"])
        ]
        affected.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        for c in affected:
            # Nhả toàn bộ phần giữ của đơn rồi thử giữ lại đúng một lần.
            c["reserved"] = []
            re_alloc = self._allocate_fresh_recipe(c["dish_id"])
            if re_alloc is not None:
                c["reserved"] = re_alloc
                c["order_status"] = "reserved"
            else:
                c["reserved"] = []
                c["order_status"] = "unfulfillable"

    # --- Kho khả dụng (v1.0 / v1.1) --------------------------------------------
    def _available_stock(self) -> dict:
        avail = dict(self.stock)
        for c in self.customers:
            for k, qty in c["reserved"].items():
                avail[k] = avail.get(k, 0) - qty
        return {k: v for k, v in avail.items() if v > 0}

    def _can_reserve(self, recipe: dict, avail: dict) -> bool:
        return all(avail.get(k, 0) >= qty for k, qty in recipe.items())

    # --- Bếp: chín và mở rộng cháy món (Phase 2 burn) ---------------------------
    def _update_stoves(self, events):
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                dish = s["dish"]
                events.append((
                    "dish_ready",
                    {"stove_id": s["id"], "order_id": dish["order_id"], "dish_id": dish["dish_id"]},
                ))
            elif (
                s["state"] == "ready"
                and self.burn_ticks is not None
                and s["ready_ticks"] > self.burn_ticks
            ):
                dish = s["dish"]
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
                order_status = "unfulfillable"
                cust = next((c for c in self.customers if c["id"] == dish["order_id"]), None)
                if cust is not None and dish["dish_id"] in self.menu:
                    if self.freshness_mode:
                        re_alloc = self._allocate_fresh_recipe(dish["dish_id"])
                        if re_alloc is not None:
                            cust["reserved"] = re_alloc
                            cust["order_status"] = "reserved"
                        else:
                            cust["reserved"] = []
                            cust["order_status"] = "unfulfillable"
                    else:
                        recipe = self.menu[dish["dish_id"]]["recipe"]
                        avail = self._available_stock()
                        if self._can_reserve(recipe, avail):
                            cust["reserved"] = {k: int(v) for k, v in recipe.items() if v > 0}
                            cust["order_status"] = "reserved"
                        else:
                            cust["reserved"] = {}
                            cust["order_status"] = "unfulfillable"
                    order_status = cust["order_status"]
                events.append((
                    "dish_burnt",
                    {
                        "stove_id": s["id"],
                        "order_id": dish["order_id"],
                        "dish_id": dish["dish_id"],
                        "order_status": order_status,
                    },
                ))

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
        list_price = int(dish_cfg["price"])

        if self.freshness_mode:
            reserved_set = set(cust["reserved"])
            consumed = [it for it in self.stock_items if it["id"] in reserved_set]
            self.stock_items = [it for it in self.stock_items if it["id"] not in reserved_set]
            consumed.sort(key=lambda it: (it["kind"], id_key(it["id"])))
            avg_fresh = sum((it["fresh_exact"] for it in consumed), Fraction(0)) / len(consumed)
            base_price = math.floor(Fraction(list_price) * avg_fresh / 100)
            items_payload = [self._item_view(it) for it in consumed]
            cust["reserved"] = []
        else:
            used = dict(cust["reserved"])
            items_payload = []
            for k in sorted(used):
                qty = int(used[k])
                if qty <= 0:
                    continue
                rem = self.stock.get(k, 0) - qty
                if rem > 0:
                    self.stock[k] = rem
                else:
                    self.stock.pop(k, None)
                items_payload.extend([k] * qty)
            base_price = list_price
            cust["reserved"] = {}

        cust["order_status"] = "assigned"
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
                "items": items_payload,
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
            tip = math.floor(Fraction(base_price) * Fraction(str(self.t["tip_rate"])))
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
        cust["reserved"] = [] if self.freshness_mode else {}
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

    # --- Lịch khách & lọc menu kế hoạch ngày (P1 Lát 3 + P2 day_plan + P3 fresh) -
    def _maybe_spawn_customer(self, events):
        if not self.random_customers:
            return
        first_tick = int(self.t["first_customer_tick"])
        interval_ticks = int(round(self.t["customer_interval_s"] * TICK))
        if self.phase_tick < first_tick:
            return
        if (self.phase_tick - first_tick) % interval_ticks != 0:
            return
        occupied = {c["table_id"] for c in self.customers}
        empty_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not empty_tables:
            return
        table = empty_tables[0]
        menu_ids = sorted(self.menu.keys())
        if self.allowed_dishes is not None:
            menu_ids = [d for d in menu_ids if d in self.allowed_dishes]

        if self.freshness_mode:
            cookable = [d for d in menu_ids if self._allocate_fresh_recipe(d) is not None]
        else:
            avail = self._available_stock()
            cookable = [d for d in menu_ids if self._can_reserve(self.menu[d]["recipe"], avail)]

        if not cookable:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_spawn").choice(cookable)
        order_id = self.ids.new("C")
        if self.freshness_mode:
            reserved = self._allocate_fresh_recipe(dish_id)
        else:
            reserved = {k: int(v) for k, v in self.menu[dish_id]["recipe"].items() if v > 0}
        self.customers.append({
            "id": order_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "order_tick": self.phase_tick,
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": 0,
            "order_status": "reserved",
            "reserved": reserved,
            "base_price": None,
            "tip": None,
        })
        events.append((
            "customer_arrived",
            {"order_id": order_id, "table_id": table["id"], "dish_id": dish_id},
        ))

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
