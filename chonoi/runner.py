"""Vòng tick (Contract B, v1.2). Sửa khung: thêm pause, sim_tick tách tick ngoài, mode `day`, event tick 0.

Thứ tự ghi: event dựng pha ở tick 0 (mode day) -> snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự
xử lý) rồi snapshot (nếu tới lượt hoặc lượt kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

Pause (Ticket-02 mục 4.2): xét cạnh `pause` trước. Vào pause chỉ tăng tick ngoài và phát `paused`;
khi còn pause, bỏ qua cạnh hành động và buy, sim_tick / phase_tick / timer đứng yên. Cạnh kế tiếp phát
`resumed` và chạy gameplay ngay trong bước đó.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi (`chonoi.live`/`chonoi.play`).
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1, extras=None, day_tuning=None, start_day=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids, extras=extras)
    if mode == "quan":
        return QuanSim(tuning, scenario, streams, ids, inventory=inventory)
    return DaySim(tuning, scenario, streams, ids, days=days, extras=extras, day_tuning=day_tuning, start_day=start_day)


def _vals(sim):
    s = sim.sub if sim.mode == "day" else sim
    return s.money, s.earned, s.reputation


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1, extras=None, day_tuning=None,
                 start_day=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days, extras, day_tuning, start_day)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _row(self, phase, name, data):
        row = {"type": "event", "tick": self.tick, "phase": phase}
        if self.mode == "day":
            row["day"] = self.sim.day
        row["name"] = name
        row["data"] = data
        return row

    def initial_events(self) -> list:
        """Event dựng pha ở tick 0 (chỉ mode day)."""
        pend = getattr(self.sim, "pending", None)
        if not pend:
            return []
        self.sim.pending = []
        return [self._row(ph, n, d) for ph, n, d in pend]

    def state(self):
        if self.sim.done:
            return "finished"
        return "paused" if self.paused else "playing"

    def snapshot(self) -> dict:
        sim = self.sim
        money, earned, rep = _vals(sim)
        mult = self.tuning["score"]["reputation_multiplier"]
        s = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
             "phase": sim.phase, "phase_tick": sim.phase_tick, "state": self.state(),
             "time_left_ticks": sim.time_left_ticks, "money": money, "earned": earned, "reputation": rep,
             "score": earned + mult * math.floor(rep)}
        s.update(sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        sim = self.sim
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                return [self._row(sim.phase, "paused", {})]
            self.paused = False
            rows = [self._row(sim.phase, "resumed", {})]
        elif self.paused:
            return []
        else:
            rows = []
        self.sim_tick += 1
        if sim.mode == "day":
            day_before = sim.day
            evs = sim.step(inp)
            for ph, n, d in evs:
                row = self._row(ph, n, d)
                row["day"] = day_before if n not in ("day_start", "day_plan") and not (
                    n == "phase_start" and ph == "gather") else sim.day
                rows.append(row)
        else:
            rows.extend(self._row(sim.phase, n, d) for n, d in sim.step(inp))
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        money, earned, rep = _vals(sim)
        mult = self.tuning["score"]["reputation_multiplier"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else self.state(),
               "reason": sim.reason if sim.done else "tick_limit",
               "money": money, "earned": earned, "reputation": rep, "score": earned + mult * math.floor(rep)}
        if sim.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.hold)


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_events():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            rows = sess.step(inp)
            for row in rows:
                w.write(row)
            phase_change = any(r["name"] == "phase_start" for r in rows)
            if sess.tick % snapshot_every == 0 or sess.done or phase_change:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
