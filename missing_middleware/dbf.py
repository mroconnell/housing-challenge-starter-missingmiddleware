"""Read the attribute table (.dbf) of a shapefile with the standard library only.

The contest allows permissively licensed dependencies only, and the geo stack (shapely's bundled GEOS is LGPL;
pyproj and pyogrio pull in certifi, MPL-2.0) is not. Parking only needs attributes such as a metro area's type,
so it reads the dBASE III table directly (format: https://www.clicketyclick.dk/databases/xbase/format/dbf.html).
"""
from __future__ import annotations

import struct
import zipfile
from pathlib import Path

import pandas as pd


def read_dbf_bytes(data: bytes, encoding: str = "latin-1") -> pd.DataFrame:
    n_rec, header_len, rec_len = struct.unpack("<IHH", data[4:12])
    fields, pos = [], 32
    while data[pos] != 0x0D:
        name = data[pos:pos + 11].split(b"\x00")[0].decode("ascii")
        ftype, flen = chr(data[pos + 11]), data[pos + 16]
        fields.append((name, ftype, flen))
        pos += 32
    rows = []
    for i in range(n_rec):
        start = header_len + i * rec_len
        rec = data[start:start + rec_len]
        if rec[:1] == b"*":  # deleted record
            continue
        off, row = 1, {}
        for name, ftype, flen in fields:
            raw = rec[off:off + flen].decode(encoding).strip()
            off += flen
            if ftype in ("N", "F"):
                row[name] = pd.to_numeric(raw, errors="coerce") if raw else float("nan")
            else:
                row[name] = raw
        rows.append(row)
    return pd.DataFrame(rows, columns=[f[0] for f in fields])


def read_shapefile_attributes(zip_path: Path | str) -> pd.DataFrame:
    """The .dbf attribute table of the (single) shapefile inside a zip, as text and numbers; no geometry."""
    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".dbf"))
        return read_dbf_bytes(z.read(name))
