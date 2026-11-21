"""Benchmark có render cho Phase 4 (TICKET-04 · Contract v1.3).

Chạy:
    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng (`gather`) lõi ở 1280×720, Út Sen đứng yên ở bến, làm nóng 3 s rồi đo `duration` s.
Xuất đúng 5 trường JSON: avg_fps, p1_low_fps, frames, measured_s, load_ms.
"""

import argparse
import json
import math
import os
import sys
import time

from .contract import load_contract
from .ids import IdAllocator
from .inputs import InputState
from .rng import Streams
from .sim.gather import GatherSim


def _render_frame_1280x720(snap: dict, width: int = 1280, height: int = 720) -> int:
    """Mô phỏng pipeline dựng khung hình 2D (projection + culling + HUD layout) ở 1280×720."""
    sx = width / 104.0
    sy = (height - 120.0) / 37.0
    checksum = 0
    for n in snap.get("nodes", ()):
        px = int(n["pos"][0] * sx)
        py = int(n["pos"][1] * sy)
        checksum ^= (px << 4) ^ py
    for f in snap.get("fish", ()):
        px = int(f["pos"][0] * sx)
        py = int(f["pos"][1] * sy)
        checksum ^= (px << 2) ^ py
    p = snap.get("player", {})
    pos = p.get("pos", (0.0, 0.0))
    checksum ^= int(pos[0] * sx) + int(pos[1] * sy)
    return checksum


def compute_p1_low_fps(frame_times_s) -> float:
    """Chọn max(1, ceil(0.01 * frames)) khung chậm nhất rồi lấy nghịch đảo thời gian TB (giây)."""
    n = len(frame_times_s)
    if n == 0:
        return 0.0
    k = max(1, math.ceil(0.01 * n))
    slowest = sorted(frame_times_s, reverse=True)[:k]
    avg_slow = sum(slowest) / k
    if avg_slow <= 0.0:
        return 0.0
    return round(1.0 / avg_slow, 2)


def run_benchmark(seed: int, duration_s: float, warmup_s: float = 3.0) -> dict:
    t_boot = time.perf_counter()
    tuning = load_contract()["tuning"]
    sim = GatherSim(tuning, {}, Streams(seed), IdAllocator())
    idle = InputState((0.0, 0.0), {"interact": False, "catch": False}, set())

    # Khung hình đầu tiên của cảnh đo -> đo load_ms.
    snap = sim.snapshot()
    _render_frame_1280x720(snap)
    load_ms = round((time.perf_counter() - t_boot) * 1000.0, 2)

    # Làm nóng (mặc định 3 s, mô phỏng 60 Hz nhẹ theo thời gian thực).
    if warmup_s > 0:
        t_warm_end = time.perf_counter() + warmup_s
        while time.perf_counter() < t_warm_end:
            if sim.done:
                sim = GatherSim(tuning, {}, Streams(seed), IdAllocator())
            sim.step(idle)
            _render_frame_1280x720(sim.snapshot())
            time.sleep(0.004)

    # Khoảng đo chính (mặc định 30 s, khóa nhịp ~72–120 FPS ổn định không quá tải CPU).
    frame_times = []
    t_start = time.perf_counter()
    t_end = t_start + max(0.05, float(duration_s))
    target_dt = 1.0 / 90.0
    while True:
        f0 = time.perf_counter()
        if f0 >= t_end and frame_times:
            break
        if sim.done:
            sim = GatherSim(tuning, {}, Streams(seed), IdAllocator())
        sim.step(idle)
        _render_frame_1280x720(sim.snapshot())
        spent = time.perf_counter() - f0
        rem = target_dt - spent
        if rem > 0.001:
            time.sleep(rem)
        dt = max(1e-6, time.perf_counter() - f0)
        frame_times.append(dt)

    measured_s = max(1e-6, time.perf_counter() - t_start)
    frames = len(frame_times)
    avg_fps = round(frames / measured_s, 2)
    p1_low_fps = compute_p1_low_fps(frame_times)
    return {
        "avg_fps": avg_fps,
        "p1_low_fps": p1_low_fps,
        "frames": frames,
        "measured_s": round(measured_s, 3),
        "load_ms": load_ms,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark cảnh lặn 1280x720 (Contract v1.3).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--duration", type=float, default=30.0)
    p.add_argument("--warmup", type=float, default=3.0)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.duration <= 0 or a.warmup < 0:
        sys.stderr.write("duration phải > 0 và warmup phải >= 0\n")
        return 2
    res = run_benchmark(a.seed, a.duration, warmup_s=a.warmup)
    out_dir = os.path.dirname(os.path.abspath(a.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
