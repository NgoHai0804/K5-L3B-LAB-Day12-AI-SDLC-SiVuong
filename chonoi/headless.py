"""Điểm vào headless: python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl

Mã thoát: 0 bình thường; 2 tham số/đầu vào sai (kiểm TRƯỚC khi ghi đầu ra); 1 lỗi chạy/ghi.
"""

import argparse
import math
import os
import sys

from .contract import load_contract
from .errors import BadInput
from .inputs import load_frames
from .inventory import read_inventory
from .leaderboard import record, validate_name
from .runner import run
from .scenario import load_scenario

FULL_DAYS = 5


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.headless")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])  # `day` có từ v1.1
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--ticks", required=True, type=_int("ticks"))
    p.add_argument("--out", required=True)
    p.add_argument("--scenario")
    p.add_argument("--inputs")
    p.add_argument("--inventory")
    p.add_argument("--inventory-out", dest="inventory_out")
    p.add_argument("--snapshot-every", dest="snapshot_every", type=_int("snapshot-every"), default=10)
    p.add_argument("--days", type=_int("days"))
    p.add_argument("--leaderboard", help="mode day: lưu bảng xếp hạng cục bộ khi xong đủ 5 Ngày chuẩn")
    p.add_argument("--player-name", dest="player_name", help="mode day: tên người chơi (Unicode khác rỗng)")
    a = p.parse_args(argv)
    try:
        if (a.leaderboard is None) != (a.player_name is None):
            raise BadInput("--leaderboard và --player-name phải đi cùng nhau")
        if a.leaderboard is not None:
            if a.mode != "day":
                raise BadInput("--leaderboard/--player-name chỉ dùng với --mode day")
            validate_name(a.player_name)
        if a.days is not None and a.mode != "day":
            raise BadInput("--days chỉ dùng với --mode day")
        days = 1 if a.days is None else a.days
        if not (1 <= days <= 5):
            raise BadInput("--days phải là số nguyên từ 1 đến 5")
        if a.ticks < 0:
            raise BadInput("--ticks phải >= 0")
        if a.snapshot_every <= 0:
            raise BadInput("--snapshot-every phải > 0")
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        outs = [x for x in (a.out, a.inventory_out) if x]
        ins = [x for x in (a.scenario, a.inputs, a.inventory) if x]
        paths = [os.path.abspath(x) for x in outs + ins]
        if len(set(paths)) != len(paths):
            raise BadInput("các đường dẫn đầu vào/đầu ra phải khác nhau")
        contract = load_contract()
        tuning = contract["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning)
        frames = load_frames(a.inputs)
        inventory = read_inventory(a.inventory) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    try:
        sim = run(a.mode, tuning, scenario, a.seed, frames, a.ticks, a.out, a.snapshot_every,
                  inventory=inventory, inventory_out=a.inventory_out, days=days)
        if (a.leaderboard is not None and a.mode == "day" and a.scenario is None
                and days == FULL_DAYS and getattr(sim, "reason", None) == "days_complete"):
            mult = contract["tuning"]["score"]["reputation_multiplier"]
            score = int(sim.earned) + int(mult) * math.floor(sim.reputation)
            record(a.leaderboard, a.player_name, score, int(sim.days_completed), a.seed)
    except BadInput as e:  # lỗi mức luật phát hiện lúc dựng sim
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
