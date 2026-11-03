"""Read a small window from a large single-band GeoTIFF, locally or over HTTP range requests.

Why our own reader: rasterio and GDAL wheels can bundle GEOS (LGPL), and tifffile needs imagecodecs (which bundles
many third-party codec libraries) for LZW. The project accepts permissive licences only. This module uses only the
standard library (zlib, urllib, struct) and numpy (BSD-3-Clause).

Scope (what the USGS Annual NLCD mosaics need, nothing more):
- classic TIFF and BigTIFF, either byte order;
- tiled or striped layout, one band (samples per pixel 1), chunky planar config;
- 8-bit unsigned pixels;
- compression none (1), LZW (5) or Deflate (8, 32946); horizontal predictor (2) or none (1);
- geo-referencing from ModelPixelScale (33550) and ModelTiepoint (33922), north-up only.
Anything else raises an error instead of guessing.

Only the tiles that touch the window are fetched, and only the slice of the tile-offset table that covers them.
"""
from __future__ import annotations

import struct
import urllib.request
import zlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_TYPES = {1: ("B", 1), 2: ("c", 1), 3: ("H", 2), 4: ("I", 4), 5: ("II", 8), 6: ("b", 1), 7: ("B", 1), 8: ("h", 2),
          9: ("i", 4), 10: ("ii", 8), 11: ("f", 4), 12: ("d", 8), 16: ("Q", 8), 17: ("q", 8), 18: ("Q", 8)}
_INT_DTYPE = {1: "u1", 3: "u2", 4: "u4", 16: "u8", 18: "u8", 7: "u1"}
UA = {"User-Agent": "missing-middleware research (public data)"}


class _Source:
    """Byte ranges from a local path or an http(s) URL."""

    def __init__(self, src: str | Path, timeout: int = 120):
        self.src, self.timeout = str(src), timeout
        self.remote = self.src.startswith(("http://", "https://"))
        self.bytes_read = 0
        self._fh = None if self.remote else open(self.src, "rb")

    def read(self, offset: int, length: int) -> bytes:
        if length <= 0:
            return b""
        if self.remote:
            req = urllib.request.Request(self.src, headers={**UA, "Range": f"bytes={offset}-{offset + length - 1}"})
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = r.read()
                if r.status == 200 and len(data) != length:  # server ignored Range: refuse rather than read a 1 GB file
                    raise RuntimeError(f"{self.src}: server does not honour HTTP Range requests")
        else:
            self._fh.seek(offset)
            data = self._fh.read(length)
        if len(data) != length:
            raise RuntimeError(f"{self.src}: short read at {offset} ({len(data)} of {length} bytes)")
        self.bytes_read += len(data)
        return data

    def close(self) -> None:
        if self._fh:
            self._fh.close()


@dataclass
class _Entry:
    type: int
    count: int
    value_offset: int  # file offset of the values (or of the entry's inline value field)


@dataclass
class GeoTiff:
    """Header facts for the first image (full resolution) of a GeoTIFF."""
    width: int
    height: int
    block_w: int
    block_h: int
    tiled: bool
    compression: int
    predictor: int
    origin_x: float  # x of the upper-left corner of pixel (0, 0)
    origin_y: float
    pixel_w: float
    pixel_h: float  # positive; rows go south
    nodata: int | None
    geokeys: tuple
    _src: _Source
    _endian: str
    _offsets: _Entry
    _counts: _Entry

    # ------------------------------------------------------------------ opening
    @classmethod
    def open(cls, src: str | Path, require_geo: bool = True) -> "GeoTiff":
        s = _Source(src)
        head = s.read(0, 16)
        endian = {b"II": "<", b"MM": ">"}.get(head[:2])
        if endian is None:
            raise ValueError("not a TIFF file")
        magic = struct.unpack(endian + "H", head[2:4])[0]
        if magic == 42:
            big, ifd = False, struct.unpack(endian + "I", head[4:8])[0]
        elif magic == 43:
            big, ifd = True, struct.unpack(endian + "Q", head[8:16])[0]
        else:
            raise ValueError(f"unknown TIFF magic {magic}")
        cnt_fmt, ent_size, off_fmt, inline = ("Q", 20, "Q", 8) if big else ("H", 12, "I", 4)
        n = struct.unpack(endian + cnt_fmt, s.read(ifd, struct.calcsize(cnt_fmt)))[0]
        base = ifd + struct.calcsize(cnt_fmt)
        raw = s.read(base, n * ent_size)
        entries: dict[int, _Entry] = {}
        for i in range(n):
            e = raw[i * ent_size:(i + 1) * ent_size]
            tag, typ = struct.unpack(endian + "HH", e[:4])
            count = struct.unpack(endian + ("Q" if big else "I"), e[4:4 + (8 if big else 4)])[0]
            size = _TYPES.get(typ, ("B", 1))[1] * count
            field = base + i * ent_size + (12 if big else 8)
            if size <= inline:
                entries[tag] = _Entry(typ, count, field)
            else:
                entries[tag] = _Entry(typ, count, struct.unpack(endian + off_fmt, e[-inline:])[0])

        def values(tag, default=None):
            if tag not in entries:
                return default
            en = entries[tag]
            fmt, size = _TYPES[en.type]
            data = s.read(en.value_offset, size * en.count)
            if en.type == 2:
                return data.rstrip(b"\x00").decode("ascii", "replace")
            out = struct.unpack(endian + fmt * en.count, data)
            return out

        def one(tag, default=None):
            v = values(tag)
            return default if v is None else v[0]

        if one(277, 1) != 1:
            raise ValueError("only single-band rasters are supported")
        if one(258, 8) != 8 or one(339, 1) != 1:
            raise ValueError("only 8-bit unsigned pixels are supported")
        comp = one(259, 1)
        if comp not in (1, 5, 8, 32946):
            raise ValueError(f"compression {comp} is not supported (only none, LZW, Deflate)")
        pred = one(317, 1)
        if pred not in (1, 2):
            raise ValueError(f"predictor {pred} is not supported")
        width, height = one(256), one(257)
        tiled = 322 in entries
        if tiled:
            bw, bh, offs, cnts = one(322), one(323), entries[324], entries[325]
        else:
            bw, bh, offs, cnts = width, min(one(278, height), height), entries[273], entries[279]
        scale, tie = values(33550), values(33922)
        if scale is None or tie is None:
            if require_geo:
                raise ValueError("no ModelPixelScale/ModelTiepoint tags: not a north-up GeoTIFF")
            scale, tie = (1.0, 1.0, 0.0), (0, 0, 0, 0.0, 0.0, 0.0)
        if tie[0] != 0 or tie[1] != 0:
            ox, oy = tie[3] - tie[0] * scale[0], tie[4] + tie[1] * scale[1]
        else:
            ox, oy = tie[3], tie[4]
        nd = values(42113)
        nodata = int(float(nd)) if nd not in (None, "") else None
        return cls(width, height, bw, bh, tiled, comp, pred, ox, oy, scale[0], scale[1], nodata,
                   values(34735, ()) or (), s, endian, offs, cnts)

    # ------------------------------------------------------------------ reading
    def _table_slice(self, en: _Entry, first: int, n: int) -> np.ndarray:
        dt = np.dtype(_INT_DTYPE[en.type]).newbyteorder(self._endian)
        size = dt.itemsize
        return np.frombuffer(self._src.read(en.value_offset + first * size, n * size), dt).astype(np.int64)

    def _decode(self, data: bytes, rows: int) -> np.ndarray:
        if self.compression == 1:
            raw = data
        elif self.compression == 5:
            raw = lzw_decode(data)
        else:
            raw = zlib.decompress(data)
        need = self.block_w * rows
        a = np.frombuffer(raw[:need], np.uint8)
        if a.size < need:
            a = np.concatenate([a, np.zeros(need - a.size, np.uint8)])
        a = a.reshape(rows, self.block_w)
        if self.predictor == 2:
            a = np.cumsum(a, axis=1, dtype=np.uint8)
        return a

    def read_window(self, col0: int, row0: int, ncols: int, nrows: int, fill: int = 0) -> np.ndarray:
        """Pixels [row0:row0+nrows, col0:col0+ncols]; cells outside the raster get `fill`."""
        out = np.full((nrows, ncols), fill, np.uint8)
        c0, r0 = max(col0, 0), max(row0, 0)
        c1, r1 = min(col0 + ncols, self.width), min(row0 + nrows, self.height)
        if c0 >= c1 or r0 >= r1:
            return out
        across = -(-self.width // self.block_w)
        for br in range(r0 // self.block_h, (r1 - 1) // self.block_h + 1):
            bc0, bc1 = c0 // self.block_w, (c1 - 1) // self.block_w
            first = br * across + bc0
            offs = self._table_slice(self._offsets, first, bc1 - bc0 + 1)
            cnts = self._table_slice(self._counts, first, bc1 - bc0 + 1)
            rows_here = self.block_h if self.tiled else min(self.block_h, self.height - br * self.block_h)
            for k, bc in enumerate(range(bc0, bc1 + 1)):
                if cnts[k] == 0:
                    continue  # sparse tile: nothing stored
                blk = self._decode(self._src.read(int(offs[k]), int(cnts[k])), rows_here)
                y0, x0 = br * self.block_h, bc * self.block_w
                ys, ye = max(r0, y0), min(r1, y0 + rows_here)
                xs, xe = max(c0, x0), min(c1, x0 + self.block_w)
                out[ys - row0:ye - row0, xs - col0:xe - col0] = blk[ys - y0:ye - y0, xs - x0:xe - x0]
        return out

    def window_for_bounds(self, xmin: float, ymin: float, xmax: float, ymax: float) -> tuple[int, int, int, int]:
        """(col0, row0, ncols, nrows) of the pixels that cover a box in the raster's coordinates."""
        col0 = int(np.floor((xmin - self.origin_x) / self.pixel_w))
        col1 = int(np.ceil((xmax - self.origin_x) / self.pixel_w))
        row0 = int(np.floor((self.origin_y - ymax) / self.pixel_h))
        row1 = int(np.ceil((self.origin_y - ymin) / self.pixel_h))
        return col0, row0, col1 - col0, row1 - row0

    def pixel_centers(self, col0: int, row0: int, ncols: int, nrows: int) -> tuple[np.ndarray, np.ndarray]:
        xs = self.origin_x + (col0 + np.arange(ncols) + 0.5) * self.pixel_w
        ys = self.origin_y - (row0 + np.arange(nrows) + 0.5) * self.pixel_h
        return np.meshgrid(xs, ys)

    def close(self) -> None:
        self._src.close()


def lzw_decode(data: bytes) -> bytes:
    """TIFF LZW (MSB-first codes, 256 = clear, 257 = end, early code-width change)."""
    out = bytearray()
    table: list[bytes] = [bytes([i]) for i in range(256)] + [b"", b""]
    width, bitpos, nbits = 9, 0, len(data) * 8
    data = bytes(data) + b"\x00\x00\x00"
    prev = None
    while bitpos + width <= nbits:
        p = bitpos >> 3
        code = (int.from_bytes(data[p:p + 3], "big") >> (24 - (bitpos & 7) - width)) & ((1 << width) - 1)
        bitpos += width
        if code == 256:
            table = table[:258]
            width, prev = 9, None
            continue
        if code == 257:
            break
        if prev is None:
            entry = table[code]
        elif code < len(table):
            entry = table[code]
            table.append(prev + entry[:1])
        else:
            entry = prev + prev[:1]
            table.append(entry)
        out += entry
        prev = entry
        if len(table) >= (1 << width) - 1 and width < 12:
            width += 1
    return bytes(out)
