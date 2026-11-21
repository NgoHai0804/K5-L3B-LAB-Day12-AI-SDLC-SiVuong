---
name: pause-contract-smoke
description: Verify Contract v1.1 pause freeze and same-step resume when changing inputs, the runner tick loop, Day, Shop, or live controls.
---

# Pause contract smoke

Run from the repository root:

```bash
python3 .agents/skills/pause-contract-smoke/scripts/run_smoke.py
```

On Windows, use `python` instead of `python3` if needed. The script checks a standalone gather session because it is independent of unfinished Day/Shop integration. It requires:

- the pause edge to emit `paused` before gameplay;
- `sim_tick`, `phase_tick`, and `time_left_ticks` to remain frozen while paused;
- the next pause edge to emit `resumed` and execute one gameplay step immediately.

If it fails, fix input edge handling or `runner.Session`; do not compensate by changing gameplay timers or tests. When Day/Shop exists, also exercise pause during Shop with its fixed fixture.
