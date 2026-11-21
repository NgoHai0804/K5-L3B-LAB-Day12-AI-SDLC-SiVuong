"""Black-box smoke for gather -> inventory file -> quan stock."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[4]
EXPECTED = {"bong_sung": 2, "ca_loc": 1}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "chonoi.headless", *args],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )


def require_ok(label: str, result: subprocess.CompletedProcess[str]) -> None:
    if result.returncode == 0:
        return
    details = result.stderr.strip() or result.stdout.strip() or "không có thông báo"
    raise RuntimeError(f"{label} thoát mã {result.returncode}: {details}")


def snapshots(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return [row for row in rows if row.get("type") == "snapshot"]


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="chonoi-smoke-") as raw:
            work = Path(raw)
            scenario = work / "dock.json"
            inputs = work / "dock-inputs.json"
            gather_out = work / "gather.jsonl"
            inventory = work / "catch.json"
            quan_out = work / "quan.jsonl"

            write_json(scenario, {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}})
            write_json(inputs, {"frames": [{"tick": 0, "interact": True}]})

            gather = run(
                "--mode", "gather", "--seed", "42", "--scenario", str(scenario),
                "--inputs", str(inputs), "--ticks", "1", "--out", str(gather_out),
                "--inventory-out", str(inventory),
            )
            require_ok("gather", gather)

            saved = json.loads(inventory.read_text(encoding="utf-8"))
            if saved != {"items": EXPECTED}:
                raise RuntimeError(f"file kho sai: nhận {saved!r}, cần {{'items': {EXPECTED!r}}}")

            quan = run(
                "--mode", "quan", "--seed", "42", "--inventory", str(inventory),
                "--ticks", "0", "--out", str(quan_out),
            )
            require_ok("quan", quan)
            rows = snapshots(quan_out)
            stock = rows[0].get("stock") if rows else None
            if stock != EXPECTED:
                raise RuntimeError(f"snapshot stock sai: nhận {stock!r}, cần {EXPECTED!r}")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL inventory handoff: {exc}", file=sys.stderr)
        return 1

    print("PASS inventory handoff: gather -> catch.json -> quan stock")
    print(json.dumps(EXPECTED, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
