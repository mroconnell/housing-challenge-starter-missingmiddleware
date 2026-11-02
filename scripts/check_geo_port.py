"""Compare outputs after the open-licence geometry port with the outputs before it (docs/GEOMETRY.md).

For every CSV under reference/ (or the paths given) that differs from the base revision, prints the largest absolute
and relative numeric difference per column and any non-numeric differences. Base: the last commit before the port.

    uv run python scripts/check_geo_port.py [paths...] [--base f30ec96]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BASE = "f30ec96"


def old_text(path: str, base: str) -> str | None:
    r = subprocess.run(["git", "show", f"{base}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def compare(path: str, base: str, rel_tol: float) -> tuple[bool, str]:
    old = old_text(path, base)
    new_p = ROOT / path
    if old is None:
        return True, f"{path}: new file (no base)"
    if not new_p.exists():
        return False, f"{path}: missing now"
    new = new_p.read_text()
    if old == new:
        return True, ""
    a, b = pd.read_csv(io.StringIO(old)), pd.read_csv(io.StringIO(new))
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        return False, f"{path}: shape/columns changed {a.shape} -> {b.shape}"
    lines, ok = [], True
    for c in a.columns:
        x, y = a[c], b[c]
        if pd.api.types.is_bool_dtype(x) or pd.api.types.is_bool_dtype(y):
            if not x.equals(y):
                ok = False
                lines.append(f"  {c}: {int((x != y).sum())} true/false values differ  <-- check")
        elif pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            d = (x - y).abs()
            r = d / x.abs().where(x.abs() > 0)
            mx, mr = float(np.nanmax(d.to_numpy())) if len(d) else 0.0, float(np.nanmax(r.to_numpy())) if r.notna().any() else 0.0
            if mx > 0:
                bad = mr > rel_tol
                ok &= not bad
                lines.append(f"  {c}: max abs {mx:.6g}, max rel {mr:.3g}{'  <-- above tolerance' if bad else ''}")
        elif not x.fillna("").astype(str).equals(y.fillna("").astype(str)):
            ok = False
            n = int((x.fillna("").astype(str) != y.fillna("").astype(str)).sum())
            lines.append(f"  {c}: {n} text values differ  <-- check")
    return ok, f"{path}:\n" + "\n".join(lines)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--rel-tol", type=float, default=1e-6)
    a = ap.parse_args(argv)
    paths = a.paths or [str(p.relative_to(ROOT)) for p in sorted((ROOT / "reference").glob("*.csv"))]
    bad = 0
    for p in paths:
        ok, msg = compare(p, a.base, a.rel_tol)
        if msg:
            print(msg)
        bad += not ok
    print(f"{len(paths)} files compared; {bad} outside tolerance")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
