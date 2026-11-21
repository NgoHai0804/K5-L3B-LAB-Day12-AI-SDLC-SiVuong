"""Small dependency-free Contract v1.1 pause smoke."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


def main():
    tuning = load_contract()["tuning"]
    session = Session("gather", tuning, {"time_left_ticks": 30}, seed=1)
    player = InputPlayer([
        {"tick": 0, "pause": True},
        {"tick": 1, "pause": False},
        {"tick": 2, "pause": True},
    ])

    before = session.snapshot()
    paused = session.step(player.advance(0))
    session.step(player.advance(1))
    frozen = session.snapshot()
    resumed = session.step(player.advance(2))
    after = session.snapshot()

    assert [e["name"] for e in paused] == ["paused"]
    assert [e["name"] for e in resumed][0] == "resumed"
    assert frozen["state"] == "paused"
    assert frozen["sim_tick"] == before["sim_tick"]
    assert frozen["phase_tick"] == before["phase_tick"]
    assert frozen["time_left_ticks"] == before["time_left_ticks"]
    assert after["state"] == "playing"
    assert after["sim_tick"] == before["sim_tick"] + 1
    assert after["phase_tick"] == before["phase_tick"] + 1
    assert after["time_left_ticks"] == before["time_left_ticks"] - 1
    print("PASS: pause freezes gameplay; resume advances in the same step")


if __name__ == "__main__":
    main()
