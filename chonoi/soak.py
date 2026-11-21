"""Soak headless (Test Contract v1.3, Ticket-04 mục 2 — giảng viên chạy để báo cáo).

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy `days` Ngày trong MỘT tiến trình headless, mỗi Ngày đi qua gather → quan → shop, bằng một
BOT TẤT ĐỊNH (không dùng đồng hồ hệ thống, không ngẫu nhiên ngoài `Streams`). Kế hoạch D1–D5 lặp ở
Ngày 6–10. Tiền, tổng thu, uy tín, cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt.

soak.json: {days, days_completed, crashes, results, duration_s}. Mỗi results[] = {day, earned,
reputation, score} ghi tại lúc Shop đóng. Đạt khi days_completed == days và crashes == 0.

Mã thoát: 0 chạy xong; 2 tham số/đầu vào sai; 1 lỗi ghi.
"""

import argparse
import json
import math
import sys
import time
import traceback

from .contract import load_contract
from .errors import BadInput
from .ids import sort_by_id
from .inputs import InputState
from .runner import build_sim

IDLE = InputState((0.0, 0.0), {}, set())


def score_of(tuning, earned, reputation) -> int:
    return int(earned) + int(tuning["score"]["reputation_multiplier"]) * math.floor(reputation)


class SoakBot:
    """Bot tất định: sáng hái từng nút rồi cập bến; tối nấu/bưng/phục vụ; chợ đóng ngay."""

    def __init__(self, tuning):
        self.g = tuning["gather"]
        self.q = tuning["quan"]
        self.nodes = sort_by_id(tuning["gather"]["nodes"], key=lambda n: n["id"])
        self.day = None
        self._reset()

    def _reset(self):
        self.target = 0
        self.to_dock = False

    def input_for(self, sim) -> InputState:
        if sim.day != self.day:
            self.day = sim.day
            self._reset()
        sub = sim.sub
        phase = sub.phase
        if phase == "gather":
            return self._gather(sub)
        if phase == "quan":
            return self._quan(sub)
        if phase == "shop":
            return InputState((0.0, 0.0), {}, {"shop_done"})
        return IDLE

    @staticmethod
    def _dir(dx):
        return 1.0 if dx > 0 else (-1.0 if dx < 0 else 0.0)

    def _gather(self, gs) -> InputState:
        p = gs.pos
        if self.to_dock:
            dp = self.g["dock_pos"]
            if math.dist(p, dp) <= self.g["dock_radius"]:
                return InputState((0.0, 0.0), {}, {"interact"})
            return InputState((self._dir(dp[0] - p[0]), 0.0), {}, set())
        node = self.nodes[self.target]
        dx = node["pos"][0] - p[0]
        if abs(dx) <= self.g["interact_radius"] * 0.9:
            self.target += 1
            if self.target >= len(self.nodes):
                self.to_dock = True
            return InputState((0.0, 0.0), {}, {"interact"})
        return InputState((self._dir(dx), 0.0), {}, set())

    def _quan(self, qs) -> InputState:
        r = self.q["interact_radius"]
        if qs.hand is not None:  # bưng món tới bàn của đơn
            c = next((c for c in qs.customers if c["id"] == qs.hand["order_id"]), None)
            if c is not None:
                tb = next((t for t in qs.tables if t["id"] == c["table_id"]), None)
                if tb is not None:
                    return self._go(qs.pos, tb["pos"], r)
            return IDLE
        ready = [s for s in qs.stoves if s["state"] == "ready"]
        if ready:
            return self._go(qs.pos, min(ready, key=lambda s: math.dist(qs.pos, s["pos"]))["pos"], r)
        waiting = [c for c in qs.customers if c["state"] == "waiting" and c["order_status"] == "reserved" and c["reserved"]]
        idle = [s for s in qs.stoves if s["state"] == "idle"]
        if waiting and idle:
            return self._go(qs.pos, min(idle, key=lambda s: math.dist(qs.pos, s["pos"]))["pos"], r)
        return IDLE

    def _go(self, pos, target, r) -> InputState:
        if math.dist(pos, target) <= r * 0.8:
            return InputState((0.0, 0.0), {}, {"interact"})
        return InputState((self._dir(target[0] - pos[0]), self._dir(target[1] - pos[1])), {}, set())


def _write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak", description="Soak headless nhiều Ngày (bot tất định).")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if a.days < 1:
            raise BadInput("--days phải >= 1")
        tuning = load_contract()["tuning"]
        sim = build_sim("day", tuning, {}, a.seed, None, days=a.days, plan_repeat=True)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2

    bot = SoakBot(tuning)
    results, crashes = [], 0
    cap = a.days * 30000 + 5000
    t0 = time.perf_counter()
    steps = 0
    try:
        while not sim.done and steps < cap:
            steps += 1
            rows = sim.step(bot.input_for(sim))
            for row in rows:
                if row[1] == "phase_start" and row[0] == "shop":
                    results.append({"day": sim.day, "earned": int(sim.earned),
                                    "reputation": round(sim.reputation, 3),
                                    "score": score_of(tuning, sim.earned, sim.reputation)})
    except Exception:  # noqa: BLE001 — soak phải sống sót và ĐẾM lỗi luật thay vì sập
        crashes += 1
        sys.stderr.write(traceback.format_exc())
    duration = time.perf_counter() - t0

    data = {"days": a.days, "days_completed": int(sim.days_completed), "crashes": crashes,
            "results": results, "duration_s": round(duration, 3)}
    try:
        _write_json(a.out, data)
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
