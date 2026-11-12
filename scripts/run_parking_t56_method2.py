"""Test 56: run_parking_method2.py under the outcome switch, with D's pools and existing-homes counts kept on all
permits (parking_t56_common.patch_method2) and South Bend's scale guarded (patch_rebuild). Same arguments as
run_parking_method2.py; with MM_BPS_OUTCOME unset it is run_parking_method2.py unchanged.

    MM_BPS_OUTCOME=units_2_4 ... uv run --all-extras python scripts/run_parking_t56_method2.py --corrected --stage 2
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import parking_t56_common as c56  # noqa: E402
import run_parking_method2 as m  # noqa: E402

if __name__ == "__main__":
    c56.patch_method2(m)
    c56.patch_rebuild(m.t46)
    m.main()
