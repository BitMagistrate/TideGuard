"""Local Lighthouse runner wrapping the LHCI CLI.

Spins up the production-built Next.js app on localhost:3000, runs the
LHCI CLI over a small set of routes, and prints a one-line summary.

CLI::

    python scripts/lighthouse_audit.py

Requires Node + `npx`. Returns non-zero if any audit category falls
below 0.85 (configurable via `--min-score`).
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROUTES = ("/", "/method", "/learn", "/jury-pilot", "/about")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Lighthouse against built web app.")
    parser.add_argument("--min-score", type=float, default=0.85,
                        help="fail if any category mean is below this threshold")
    parser.add_argument("--keep-artifacts", action="store_true",
                        help="don't clean LHCI reports on success")
    args = parser.parse_args(argv)

    if shutil.which("npx") is None:
        print("npx not available — install Node 20+ first", file=sys.stderr)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="lhci-"))
    print(f"[lhci] outdir={tmp}")
    urls = " ".join(f"--collect.url=http://localhost:3000{r}" for r in ROUTES)
    cmd = (
        "npx --yes @lhci/cli@0.13.x autorun "
        "--collect.startServerCommand='pnpm --filter @tideguard/web start' "
        f"{urls} "
        f"--upload.outputDir={tmp} "
        "--upload.target=filesystem"
    )
    print(f"[lhci] $ {cmd}")
    rc = subprocess.call(shlex.split(cmd), env={**os.environ, "CI": "1"})
    if rc != 0:
        print(f"[lhci] exited with rc={rc}")
        return rc

    manifest_path = tmp / "manifest.json"
    if not manifest_path.exists():
        print("[lhci] no manifest produced", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text())

    fail = False
    for entry in manifest:
        scores = entry.get("summary", {})
        bad = {k: v for k, v in scores.items() if v < args.min_score}
        url = entry.get("url", "?")
        if bad:
            print(f"[lhci] {url}: below threshold: {bad}")
            fail = True
        else:
            print(f"[lhci] {url}: OK  ({scores})")

    if not args.keep_artifacts and not fail:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
