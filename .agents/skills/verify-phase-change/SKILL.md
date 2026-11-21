---
name: verify-phase-change
description: Verify a Day 12 phase change before commit or push, and record evidence without hiding failures or changing tests to force a pass.
---

# Verify a phase change

Use this after implementing a slice or before pushing it.

1. Read `git diff --check`, `git status --short`, and the diff for the files in scope. Stop if unrelated user changes would be included.
2. Run the complete command from `AGENTS.md`:

   ```bash
   PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
   ```

   In PowerShell, use `$env:PYTHONPATH='tests;.'` for that process and run `python -m unittest discover -s tests -v`.
3. Run any slice-specific smoke named in `TEAM.md`. Do not change a frozen test or contract to turn a failure green.
   For Phase 2 changes touching input/ticks/pause, also run:

   ```bash
   python3 .agents/skills/pause-contract-smoke/scripts/run_smoke.py
   ```

   For `day`, use `--days 1..5`; never pass inventory flags because they remain exclusive to standalone gather/quan.
4. Put the command, date, branch/commit, pass/fail counts, and any honest limitation in `docs/proof/phase-<n>/`. Only claim browser/UI verification when it was actually observed.
5. Review the staged diff before committing. Keep generated JSONL, temporary inventory files, secrets, and local environment files out of the commit.
