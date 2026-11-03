"""Tests for missing_middleware/tiff_window.py on small synthetic GeoTIFFs (no network)."""
from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

import numpy as np

from missing_middleware.tiff_window import GeoTiff, lzw_decode


def lzw_encode(data: bytes) -> bytes:
    """TIFF LZW encoder (MSB-first, early change), used only to build test files."""
    width, out_bits, nbits = 9, 0, 0
    table = {bytes([i]): i for i in range(256)}
    nxt = 258

    def emit(c):
        nonlocal out_bits, nbits
        out_bits = (out_bits << width) | c
        nbits += width

    emit(256)
    w = b""
    for b in data:
        wc = w + bytes([b])
        if wc in table:
            w = wc
            continue
        emit(table[w])
        table[wc] = nxt
        nxt += 1
        # the decoder lags one entry behind, so its table holds nxt - 1 entries; it widens at (1 << width) - 1
        if nxt >= (1 << width) and width < 12:
            width += 1
        if nxt >= 4094:
            emit(256)
            table = {bytes([i]): i for i in range(256)}
            nxt, width = 258, 9
        w = bytes([b])
    if w:
        emit(table[w])
        if nxt >= (1 << width) - 1 and width < 12:  # the decoder adds one entry for this last code
            width += 1
    emit(257)
    pad = (-nbits) % 8
    return (out_bits << pad).to_bytes((nbits + pad) // 8, "big")


def write_tiff(path: Path, a: np.ndarray, tile: int | None, comp: int, pred: int, big: bool, endian: str = "<",
               origin=(1000.0, 5000.0), px=30.0, nodata="250") -> None:
    h, w = a.shape
    if tile:
        bw = bh = tile
        across, down = -(-w // bw), -(-h // bh)
        blocks = []
        for r in range(down):
            for c in range(across):
                b = np.zeros((bh, bw), np.uint8)
                part = a[r * bh:(r + 1) * bh, c * bw:(c + 1) * bw]
                b[:part.shape[0], :part.shape[1]] = part
                blocks.append(b)
    else:
        bw, bh = w, 3
        blocks = [a[r:r + bh] for r in range(0, h, bh)]
    enc = []
    for b in blocks:
        if pred == 2:
            b = np.diff(np.c_[np.zeros((b.shape[0], 1), np.uint8), b].astype(np.int16), axis=1).astype(np.uint8)
        raw = np.ascontiguousarray(b).tobytes()
        enc.append({1: raw, 5: lzw_encode(raw) if comp == 5 else None, 8: zlib.compress(raw)}[comp])
    body = bytearray()
    head = 16 if big else 8
    offsets = []
    for e in enc:
        offsets.append(head + len(body))
        body += e
    counts = [len(e) for e in enc]
    extra = bytearray()
    base_extra = head + len(body)

    long_t, long_f = (16, "Q") if big else (4, "I")
    tags = [(256, 3, [w]), (257, 3, [h]), (258, 3, [8]), (259, 3, [comp]), (262, 3, [1]), (277, 3, [1]),
            (284, 3, [1]), (317, 3, [pred]), (339, 3, [1])]
    if tile:
        tags += [(322, 3, [bw]), (323, 3, [bh]), (324, long_t, offsets), (325, long_t, counts)]
    else:
        tags += [(273, long_t, offsets), (278, 3, [bh]), (279, long_t, counts)]
    tags += [(33550, 12, [px, px, 0.0]), (33922, 12, [0.0, 0.0, 0.0, origin[0], origin[1], 0.0]),
             (42113, 2, nodata.encode() + b"\x00")]
    inline = 8 if big else 4
    fmt_of = {3: "H", 4: "I", 16: "Q", 12: "d"}
    entries = []
    for tag, typ, vals in sorted(tags):
        if typ == 2:
            data, count = vals, len(vals)
        else:
            data, count = struct.pack(endian + fmt_of[typ] * len(vals), *vals), len(vals)
        if len(data) <= inline:
            field = data.ljust(inline, b"\x00")
        else:
            off = base_extra + len(extra)
            extra.extend(data)
            field = struct.pack(endian + ("Q" if big else "I"), off)
        entries.append((tag, typ, count, field))
    ifd_off = base_extra + len(extra)
    if big:
        hdr = (b"II" if endian == "<" else b"MM") + struct.pack(endian + "HHHQ", 43, 8, 0, ifd_off)
        ifd = struct.pack(endian + "Q", len(entries)) + b"".join(
            struct.pack(endian + "HHQ", t, ty, c) + f for t, ty, c, f in entries) + struct.pack(endian + "Q", 0)
    else:
        hdr = (b"II" if endian == "<" else b"MM") + struct.pack(endian + "HI", 42, ifd_off)
        ifd = struct.pack(endian + "H", len(entries)) + b"".join(
            struct.pack(endian + "HHI", t, ty, c) + f for t, ty, c, f in entries) + struct.pack(endian + "I", 0)
    path.write_bytes(hdr + bytes(body) + bytes(extra) + ifd)


class TestTiffWindow(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        a = rng.integers(0, 101, size=(70, 90)).astype(np.uint8)
        a[::5] = 0  # runs, so LZW codes repeat and widths grow
        a[10:20, 30:60] = 250
        self.a = a
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, **kw):
        p = Path(self.tmp.name) / "t.tif"
        write_tiff(p, self.a, **kw)
        g = GeoTiff.open(p)
        self.assertEqual((g.width, g.height), (90, 70))
        self.assertEqual(g.nodata, 250)
        np.testing.assert_array_equal(g.read_window(0, 0, 90, 70), self.a)
        np.testing.assert_array_equal(g.read_window(13, 7, 41, 29), self.a[7:36, 13:54])
        w = g.read_window(-5, -3, 20, 10, fill=250)  # partly outside: filled
        self.assertTrue((w[:3] == 250).all() and (w[:, :5] == 250).all())
        np.testing.assert_array_equal(w[3:, 5:], self.a[0:7, 0:15])
        g.close()

    def test_layouts(self):
        for tile in (16, 32, None):
            for comp in (1, 5, 8):
                for pred in (1, 2):
                    for big in (False, True):
                        with self.subTest(tile=tile, comp=comp, pred=pred, big=big):
                            self.check(tile=tile, comp=comp, pred=pred, big=big)

    def test_big_endian(self):
        self.check(tile=16, comp=8, pred=2, big=False, endian=">")

    def test_geo(self):
        p = Path(self.tmp.name) / "g.tif"
        write_tiff(p, self.a, tile=32, comp=8, pred=1, big=False, origin=(1000.0, 5000.0))
        g = GeoTiff.open(p)
        self.assertEqual(g.window_for_bounds(1000.0 + 30 * 3 + 1, 5000.0 - 30 * 9, 1000.0 + 30 * 8, 5000.0 - 30 * 2 - 5),
                         (3, 2, 5, 7))
        xs, ys = g.pixel_centers(3, 2, 2, 2)
        self.assertEqual((xs[0, 0], ys[0, 0]), (1000.0 + 105.0, 5000.0 - 75.0))

    def test_lzw_long_input(self):
        rng = np.random.default_rng(1)
        data = bytes(rng.integers(0, 4, 60000).astype(np.uint8))  # forces code-width changes and table resets
        self.assertEqual(lzw_decode(lzw_encode(data)), data)

    def test_lzw_matches_libtiff(self):
        # tests/fixtures/lzw_libtiff.tif was written by libtiff (through Pillow) from this same array
        rng = np.random.default_rng(11)
        a = rng.integers(0, 4, (120, 100)).astype(np.uint8)
        a[40:60] = rng.integers(0, 101, (20, 100))
        g = GeoTiff.open(Path(__file__).parent / "fixtures" / "lzw_libtiff.tif", require_geo=False)
        self.assertEqual(g.compression, 5)
        np.testing.assert_array_equal(g.read_window(0, 0, 100, 120), a)
        g.close()

    def test_rejects_unsupported(self):
        p = Path(self.tmp.name) / "bad.tif"
        p.write_bytes(b"XX" + b"\x00" * 30)
        with self.assertRaises(ValueError):
            GeoTiff.open(p)


if __name__ == "__main__":
    unittest.main()
