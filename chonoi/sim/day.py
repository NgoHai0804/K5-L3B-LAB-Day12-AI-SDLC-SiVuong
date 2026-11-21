"""Vòng Ngày (`--mode day`, Ticket-02 mục 2 + Ticket-03 bàn giao kho cá thể).

day_start -> day_plan -> phase_start(gather) -> ... gather_end -> phase_start(quan) [cùng tick]
-> ... quan_end -> phase_start(shop) [cùng tick] -> ... shop_end -> (Ngày kế: day_start ... | hết: days_complete)

Pha mới chỉ chạy gameplay từ bước sau. Event kết thúc mang pha cũ. Tiền, earned, uy tín và cấp nâng cấp
giữ qua Ngày. Cấp vừa mua chỉ có hiệu lực (active_upgrades) khi dựng Ngày mới. Bàn giao kho trong cùng tick,
hàng không hao thêm; hàng dư ở Shop không hao và bị bỏ khi sang Ngày mới.
"""

import copy

from ..contract import plan_ingredients
from ..errors import BadInput
from ..inventory import item_out, to_fraction
from .gather import GatherSim
from .quan import QuanSim

UPGRADE_FIELDS = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


class ShopSim:
    mode = "shop"
    phase = "shop"

    def __init__(self, tuning, day_state, stock):
        s = tuning["shop"]
        self.ups = s["upgrades"]
        self.day = day_state
        self.stock = stock
        self.time_left_ticks = int(s["max_ticks"])
        self.phase_tick = 0
        self.done = False
        self.reason = None

    @property
    def money(self):
        return self.day.money

    @property
    def earned(self):
        return self.day.earned

    @property
    def reputation(self):
        return self.day.reputation

    def snapshot(self):
        return {"stock": [item_out(it) for it in self.stock],
                "shop": {kind: {"level": self.day.upgrades.get(kind, 0), "max_level": len(levels),
                                "next_price": levels[self.day.upgrades.get(kind, 0)]["price"]
                                if self.day.upgrades.get(kind, 0) < len(levels) else None}
                         for kind, levels in sorted(self.ups.items()) if kind in UPGRADE_FIELDS}}

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy is not None:
            self._buy(inp.buy, events)
        if inp.pressed("shop_done"):
            self.done, self.reason = True, "done"
        elif self.time_left_ticks <= 0:
            self.done, self.reason = True, "time"
        if self.done:
            events.append(("shop_end", {"reason": self.reason}))
        return events

    def _buy(self, action, events):
        if action not in UPGRADE_FIELDS or action not in self.ups:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        levels = self.ups[action]
        cur = self.day.upgrades.get(action, 0)
        if cur >= len(levels):
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        nxt = levels[cur]
        if self.day.money < nxt["price"]:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.day.money -= nxt["price"]
        self.day.upgrades[action] = cur + 1
        events.append(("bought", {"upgrade": action, "level": cur + 1, "price": nxt["price"],
                                  "money": self.day.money}))


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1, extras=None, day_tuning=None, start_day=1):
        if not (1 <= days <= len(tuning["day_plan"])):
            raise BadInput(f"--days phải trong [1, {len(tuning['day_plan'])}]")
        self.base_tuning = tuning
        self.rng = streams
        self.ids = ids
        self.days_total = days
        self.extras = extras
        self.day_tuning = day_tuning  # sáng tạo (bản chơi): tuning riêng theo Ngày; headless = None
        blk = scenario.get("day", {})
        self.money = blk.get("money", 0)
        self.earned = blk.get("earned", 0)
        self.reputation = float(blk.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(blk.get("upgrades", {}))
        self.plan = copy.deepcopy(tuning["day_plan"])
        for o in blk.get("day_plan", []):
            dishes = o["dishes"]
            ing = plan_ingredients(dishes, tuning["menu"])
            if "ingredients" in o and o["ingredients"] != ing:
                raise BadInput(f"day.day_plan ngày {o['day']}: ingredients khác tổng công thức × số suất")
            self.plan[o["day"] - 1] = {"day": o["day"], "dishes": dict(dishes), "ingredients": ing}
        self.gather_tpl = scenario.get("gather", {})
        self.quan_tpl = scenario.get("quan", {})
        self.day = start_day - 1  # bản chơi tiếp tục từ Ngày đã lưu; headless luôn từ Ngày 1
        self.days_completed = start_day - 1
        self.active = {}
        self.sub = None
        self.done = False
        self.reason = None
        self.pending = []
        self._first_day = start_day
        self._start_day(self.pending)

    # --- thuộc tính chung cho runner -------------------------------------------------
    @property
    def phase(self):
        return self.sub.phase

    @property
    def phase_tick(self):
        return self.sub.phase_tick

    @property
    def time_left_ticks(self):
        return self.sub.time_left_ticks

    @property
    def tuning(self):
        return self.day_tuning(self.day, dict(self.active)) if self.day_tuning else self.base_tuning

    def plan_today(self):
        p = self.plan[self.day - 1]
        return {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}

    def _active_values(self):
        out = {}
        for kind, field in UPGRADE_FIELDS.items():
            lv = self.active.get(kind, 0)
            if lv > 0:
                out[field] = self.base_tuning["shop"]["upgrades"][kind][lv - 1][field]
        return out

    # --- dựng pha ----------------------------------------------------------------------
    def _start_day(self, out):
        self.day += 1
        self.active = dict(self.upgrades)
        t = self.tuning
        tpl = self.gather_tpl
        hold = None
        if self.day > self._first_day and "hold" in tpl:
            hold = [{"id": self.ids.new("I"), "kind": h["kind"], "fresh": to_fraction(h["fresh"])} for h in tpl["hold"]]
        self.sub = GatherSim(t, tpl, self.rng, self.ids, day=self.day, active=self._active_values(),
                             hold=hold, extras=self.extras)
        self._sync()
        out.append(("gather", "day_start", {}))
        out.append(("gather", "day_plan", self.plan_today()))
        out.append(("gather", "phase_start", {}))

    def _sync(self):
        s = self.sub
        if isinstance(s, GatherSim):
            s.money, s.earned, s.reputation = self.money, self.earned, self.reputation

    def _open_quan(self, out, inventory):
        t = self.tuning
        if "stock" in self.quan_tpl or "reputation" in self.quan_tpl:
            raise BadInput("chạy day không nhận quan.stock / quan.reputation")
        self.sub = QuanSim(t, self.quan_tpl, self.rng, self.ids, inventory=inventory,
                           plan_dishes=list(self.plan[self.day - 1]["dishes"]),
                           money=self.money, earned=self.earned, reputation=self.reputation)
        out.append(("quan", "phase_start", {}))

    # --- một bước --------------------------------------------------------------------------
    def step(self, inp):
        out = []
        sub = self.sub
        for name, data in sub.step(inp):
            out.append((sub.phase, name, data))
        if not sub.done:
            return out
        if isinstance(sub, GatherSim):
            self._open_quan(out, sub.hold)  # cùng tick, hàng không hao thêm
        elif isinstance(sub, QuanSim):
            self.money, self.earned, self.reputation = sub.money, sub.earned, sub.reputation
            self.sub = ShopSim(self.tuning, self, sub.stock)
            out.append(("shop", "phase_start", {}))
        else:
            self.days_completed += 1
            if self.days_completed >= self.days_total:
                self.done, self.reason = True, "days_complete"
            else:
                self._start_day(out)
        return out

    def snapshot(self):
        snap = {"day": self.day, "day_plan": self.plan_today(), "upgrades": dict(self.upgrades),
                "active_upgrades": dict(self.active), "days_completed": self.days_completed,
                "days_total": self.days_total}
        snap.update(self.sub.snapshot())
        return snap

    @property
    def money_now(self):
        return self.sub.money
