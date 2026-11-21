"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .errors import BadInput
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=None, version="1.1"):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids, version=version)
    if mode == "quan":
        return QuanSim(tuning, scenario, streams, ids, inventory=inventory)
    try:
        from .sim.day import DaySim
    except ImportError as exc:
        if exc.name != "chonoi.sim.day":
            raise
        raise BadInput("mode day cần chonoi/sim/day.py của lát Day + Shop") from exc
    return DaySim(tuning, scenario, streams, ids, days=days)


def _common(sim, tick, sim_tick, phase_tick, tuning, state, paused=False):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation), "paused": paused,
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=None, version="1.1"):
        self.mode = mode
        self.tuning = tuning
        self.version = version
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days=days, version=version)
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        sim_tick = getattr(self.sim, "sim_tick", self.sim_tick)
        phase_tick = getattr(self.sim, "phase_tick", self.phase_tick)
        state = "finished" if self.sim.done else "playing"
        s = _common(self.sim, self.tick, sim_tick, phase_tick, self.tuning, state, self.paused)
        s.update(self.sim.snapshot())
        s["paused"] = self.paused
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        events = []
        run_gameplay = not self.paused
        if inp.pressed("pause"):
            if self.paused:
                self.paused = False
                run_gameplay = True
                events.append(("resumed", {}))
            else:
                self.paused = True
                run_gameplay = False
                events.append(("paused", {}))
        if run_gameplay:
            events.extend(self.sim.step(inp))
            self.sim_tick += 1
            self.phase_tick += 1
        self.tick += 1
        rows = []
        for name, data in events:
            row = {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}
            if self.mode == "day":
                row["day"] = getattr(self.sim, "day", 1)
            rows.append(row)
        return rows

    def end_row(self) -> dict:
        sim = self.sim
        sim_tick = getattr(sim, "sim_tick", self.sim_tick)
        phase_tick = getattr(sim, "phase_tick", self.phase_tick)
        score = _common(sim, self.tick, sim_tick, phase_tick, self.tuning, "", self.paused)["score"]
        return {"type": "end", "ticks": self.tick, "sim_tick": sim_tick, "mode": sim.mode,
                "state": "finished" if sim.done else "playing",
                "reason": sim.reason if sim.done else "tick_limit",
                "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items(), version=self.version)


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every,
        inventory=None, inventory_out=None, days=None, version="1.1"):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days, version=version)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
