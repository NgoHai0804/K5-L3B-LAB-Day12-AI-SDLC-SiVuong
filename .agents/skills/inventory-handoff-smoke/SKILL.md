---
name: inventory-handoff-smoke
description: Verify the Day 12 gather-to-quan inventory handoff when changing inventory loading, gather docking, or integration behavior.
---

# Inventory handoff smoke

Use the repository's frozen inventory contract; do not edit `game.contract.json`, `docs/contracts/`, or the framework merely to make this check pass.

Run from the repository root:

```bash
python3 .agents/skills/inventory-handoff-smoke/scripts/run_smoke.py
```

On Windows, use `python` instead of `python3` if needed. The script creates isolated temporary fixtures, runs `gather` then `quan`, and requires the tick-0 restaurant snapshot to contain exactly `{"bong_sung":2,"ca_loc":1}`.

If it fails, report which process failed and keep its stderr. Fix the owned gameplay code, or notify the team before changing a locked contract/framework file. Record a pass in `docs/proof/phase-1/` only after the script exits with code 0.
