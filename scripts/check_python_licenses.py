#!/usr/bin/env python3
"""Check the licences of every Python distribution installed in the project's uv environment.

Run with ``uv run --all-extras python scripts/check_python_licenses.py`` (``bash scripts/test.sh`` does this).
It reads each installed distribution's metadata with ``importlib.metadata`` (the SPDX
``License-Expression`` field, else the ``License`` field, else the ``License ::`` trove classifiers)
and fails if any licence is outside the permissive allowlist below, or cannot be read.

Flagged exceptions (``EXCEPTIONS``) are reviewed and justified in docs/DISCLOSURES.md
("Dependency Licenses"); they are printed but do not fail the check. The npm counterpart is
``ui/scripts/check-licenses.mjs``.
"""
from __future__ import annotations

import importlib.metadata as md
import re
import sys

# Permissive SPDX identifiers accepted for dependencies (Official Rules 7(b)).
ALLOWED = {
    "MIT", "MIT-0", "BSD-2-Clause", "BSD-3-Clause", "0BSD", "Apache-2.0", "ISC", "PSF-2.0",
    "Python-2.0", "Zlib", "BlueOak-1.0.0", "Unicode-3.0", "HPND",
}
# CC0-1.0 is accepted only as a component of an expression that is otherwise permissive (numpy bundles
# a CC0-1.0 sub-file); it is never accepted as a package's sole licence. See docs/DISCLOSURES.md.
COMPONENT_ONLY = {"CC0-1.0"}
# Trove classifiers and free-text "License" values that map to permissive licences.
CLASSIFIER_MAP = {
    "MIT License": "MIT",
    "BSD License": "BSD-3-Clause",
    "Apache Software License": "Apache-2.0",
    "ISC License (ISCL)": "ISC",
    "Python Software Foundation License": "PSF-2.0",
    "zlib/libpng License": "Zlib",
}
TEXT_MAP = {"mit": "MIT", "apache-2.0": "Apache-2.0", "apache 2.0": "Apache-2.0", "bsd": "BSD-3-Clause",
            "bsd-3-clause": "BSD-3-Clause", "isc": "ISC", "psf": "PSF-2.0"}
# Reviewed exceptions: name -> reason (full justification in docs/DISCLOSURES.md).
EXCEPTIONS = {
    "certifi": "MPL-2.0; transitive runtime dependency of pyproj and pyogrio (geo extra), used unmodified "
               "as a CA bundle, not distributed with the submission code (docs/DISCLOSURES.md)",
}


def licence_ids(dist: md.Distribution) -> tuple[list[str], str]:
    """Return (SPDX ids that must all be acceptable, source of the answer)."""
    meta = dist.metadata
    expr = (meta.get("License-Expression") or "").strip()
    if expr:
        # "A AND B" needs all; "A OR B" needs one: keep the permissive choice when there is one.
        ids = []
        for part in re.split(r"\s+AND\s+", expr.strip("() ")):
            choices = [c.strip("() ") for c in re.split(r"\s+OR\s+", part)]
            ok = [c for c in choices if c in ALLOWED]
            ids.append(ok[0] if ok else choices[0])
        return ids, "License-Expression"
    classifiers = [c.split(" :: ")[-1] for c in (meta.get_all("Classifier") or []) if c.startswith("License ::")]
    mapped = [CLASSIFIER_MAP[c] for c in classifiers if c in CLASSIFIER_MAP]
    if mapped:
        return mapped[:1], "classifier"  # several license classifiers mean a choice (e.g. dual BSD/Apache)
    text = (meta.get("License") or "").strip().splitlines()
    first = text[0].strip().lower() if text else ""
    for key, spdx in TEXT_MAP.items():
        if first == key or first.startswith(key + " license"):
            return [spdx], "License"
    if first in {s.lower() for s in ALLOWED}:
        return [next(s for s in ALLOWED if s.lower() == first)], "License"
    if classifiers:
        return classifiers, "classifier"
    return [meta.get("License") or "UNKNOWN"], "License"


def main() -> int:
    seen: dict[str, md.Distribution] = {}
    for dist in md.distributions():
        name = (dist.metadata.get("Name") or "").lower()
        if name and name not in seen:
            seen[name] = dist
    failures, flagged = [], []
    for name in sorted(seen):
        dist = seen[name]
        ids, source = licence_ids(dist)
        bad = [i for i in ids if i not in ALLOWED and not (i in COMPONENT_ONLY and len(ids) > 1)]
        line = f"{name} {dist.version}: {' AND '.join(ids)} ({source})"
        if bad and name in EXCEPTIONS:
            flagged.append(f"{line}  [flagged exception: {EXCEPTIONS[name]}]")
        elif bad:
            failures.append(f"{line}  [not in allowlist: {', '.join(bad)}]")
        else:
            print(f"ok    {line}")
    for f in flagged:
        print(f"FLAG  {f}")
    for f in failures:
        print(f"FAIL  {f}")
    print(f"{len(seen)} Python distributions checked: {len(seen) - len(failures) - len(flagged)} permissive, "
          f"{len(flagged)} flagged exception(s), {len(failures)} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
