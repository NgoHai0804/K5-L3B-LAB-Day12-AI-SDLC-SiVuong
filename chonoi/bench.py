"""Benchmark có render (Test Contract v1.3, Ticket-04 mục 1).

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: BUỔI SÁNG LÕI (`gather`, seed cho) với độ tươi (freshness), cá bơi + sinh theo lịch,
Cá Sấu Năm Chèo (từ Ngày 1) và hiệu ứng mặc định. Út Sen ĐỨNG YÊN ở bến (không input), cửa sổ 1280×720.
Làm nóng 3 s rồi đo 30 s (mặc định). Mỗi khung: 1 tick mô phỏng + dựng snapshot + vẽ cảnh vào
framebuffer w×h (rasterizer CPU dùng slice/memcpy), nên phép đo gồm cả chi phí render.

Xuất đúng 5 trường JSON:
  frames, measured_s  — số khung và số giây thực tế trong khoảng đo (sau làm nóng).
  avg_fps             — frames / measured_s.
  p1_low_fps          — nghịch đảo thời gian trung bình của max(1, ceil(0.01×frames)) khung chậm nhất.
  load_ms             — mili giây từ lúc khởi chạy đến khung hình đầu tiên của cảnh đo.

Mã thoát: 0 bình thường; 2 tham số sai; 1 lỗi ghi.
"""

import argparse
import json
import math
import sys
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import build_sim

IDLE = InputState((0.0, 0.0), {}, set())
URGENT_RED = (200, 40, 40)
WATER = (12, 78, 138)


def _blit(buf, w, h, x, y, rw, rh, color):
    """Vẽ hình chữ nhật đặc vào framebuffer RGB (mỗi hàng một slice)."""
    r, g, b = color
    row = bytes((r, g, b)) * rw
    y0 = max(0, y - rh // 2)
    y1 = min(h, y + rh // 2)
    x0 = max(0, x - rw // 2)
    span = min(rw, w - x0)
    if span <= 0 or y1 <= y0:
        return
    for yy in range(y0, y1):
        base = (yy * w + x0) * 3
        buf[base:base + span * 3] = row[:span * 3]


def render_scene(buf, w, h, water, snap, bounds):
    """Nền nước (memcpy cả khung) + chiếu và vẽ Út Sen, cá, nút hái, thủy quái."""
    buf[:] = water
    X = bounds["x"][1] or 1.0
    D = bounds["d"][1] or 1.0

    def proj(x, d):
        return int(x / X * (w - 1)), int(d / D * (h - 1))

    for f in snap.get("fish", []):
        px, py = proj(f["pos"][0], f["pos"][1])
        _blit(buf, w, h, px, py, 6, 4, (208, 236, 255))
    for n in snap.get("nodes", []):
        px, py = proj(n["pos"][0], 0.0)
        _blit(buf, w, h, px, py, 5, 5, (96, 200, 96) if n.get("ready") else (70, 120, 70))
    for m in snap.get("monsters", []):
        px, py = proj(m["pos"][0], m["pos"][1])
        _blit(buf, w, h, px, py, 11, 6, URGENT_RED if m.get("state") == "chase" else (120, 160, 70))
    p = snap["player"]["pos"]
    px, py = proj(p[0], p[1])
    _blit(buf, w, h, px, py, 8, 10, (240, 210, 170))


def _frame(sim, buf, w, h, water, tuning, seed):
    """Một khung: tick mô phỏng (dựng lại cảnh nếu buổi sáng đã hết) rồi render."""
    if sim.done:
        sim = build_sim("gather", tuning, {}, seed, None)
    sim.step(IDLE)
    snap = sim.snapshot()
    render_scene(buf, w, h, water, snap, tuning["gather"]["bounds"])
    return sim


def main(argv=None) -> int:
    t_start = time.perf_counter()
    p = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark cảnh sáng (gather) có render.")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, default=30.0)
    p.add_argument("--warmup", type=float, default=3.0)
    p.add_argument("--out", required=True)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    a = p.parse_args(argv)
    try:
        if a.duration < 0 or a.warmup < 0:
            raise BadInput("--duration và --warmup phải >= 0")
        if a.width <= 0 or a.height <= 0:
            raise BadInput("--width/--height phải > 0")
        tuning = load_contract()["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2

    w, h = a.width, a.height
    water = bytes(WATER) * (w * h)
    buf = bytearray(w * h * 3)
    sim = build_sim("gather", tuning, {}, a.seed, None)
    sim = _frame(sim, buf, w, h, water, tuning, a.seed)
    load_ms = (time.perf_counter() - t_start) * 1000.0

    t = time.perf_counter()
    while time.perf_counter() - t < a.warmup:
        sim = _frame(sim, buf, w, h, water, tuning, a.seed)

    frames, durs = 0, []
    t0 = t_last = time.perf_counter()
    while True:
        sim = _frame(sim, buf, w, h, water, tuning, a.seed)
        t1 = time.perf_counter()
        durs.append(t1 - t_last)
        t_last = t1
        frames += 1
        if t_last - t0 >= a.duration:
            break
    measured = t_last - t0
    avg_fps = frames / measured if measured > 0 else float(frames)
    k = max(1, math.ceil(0.01 * frames))
    slowest = sorted(durs)[-k:]
    mean_slow = sum(slowest) / len(slowest) if slowest else 0.0
    p1_low_fps = (1.0 / mean_slow) if mean_slow > 1e-12 else avg_fps

    out = {"avg_fps": round(avg_fps, 3), "p1_low_fps": round(p1_low_fps, 3), "frames": int(frames),
           "measured_s": round(measured, 3), "load_ms": round(load_ms, 1)}
    try:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
