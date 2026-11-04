# Bakes what blocks the sun in the Zhu Ming Hall scan into an RGB top-down map for CM_3DGS_PP: R/G/B = density of
# everything standing in three height bands above the ground. Run with plain python3 (not in the editor).
import json, math, struct, sys, zlib

PLY = "path/to/your_scan.ply"
OUT = "sun_canopy.png"
SIZE = 512
MAP_MIN, MAP_SPAN = -3200.0, 8000.0       # scan-local cm covered by the map, on both axes
BANDS = ((250.0, 600.0), (600.0, 1000.0), (1000.0, 1800.0))  # cm above ground; higher = sky splats, ignored
MIN_OPACITY_LOGIT = -0.5
DENSITY_SCALE = 1.2                       # bigger = more solid canopy, smaller pools of light
GROUND_FIT = (174.82, -72.22, -49.3, 11.34, 14.51, 5.02, -1.05, -1.46, -3.94, -1.19)


def ground(x, y):
    x = min(max(x / 1000.0, -2.5), 3.8)
    y = min(max(y / 1000.0, -2.5), 3.8)
    g = GROUND_FIT
    return (g[0] + g[1] * x + g[2] * y + g[3] * x * x + g[4] * x * y + g[5] * y * y
            + g[6] * x ** 3 + g[7] * x * x * y + g[8] * x * y * y + g[9] * y ** 3)


cell = MAP_SPAN / SIZE
grids = [[0.0] * (SIZE * SIZE) for _ in BANDS]
f = open(PLY, "rb")
while f.readline().strip() != b"end_header":
    pass
st = struct.Struct("<14f")
while True:
    block = f.read(56 * 200000)
    if not block:
        break
    for v in st.iter_unpack(block):
        if v[10] < MIN_OPACITY_LOGIT:
            continue
        x, y, z = v[2] * 100.0, v[0] * 100.0, -v[1] * 100.0     # same axes as NanoGS's importer
        i, j = int((x - MAP_MIN) / cell), int((y - MAP_MIN) / cell)
        if not (0 <= i < SIZE and 0 <= j < SIZE):
            continue
        h = z - ground(x, y)
        for b, (lo, hi) in enumerate(BANDS):
            if lo <= h < hi:
                # a big splat shades more than its one cell; opacity weights it
                r = math.exp(max(v[7], v[8], v[9])) * 100.0
                w = 1.0 / (1.0 + math.exp(-v[10]))
                n = min(int(r / cell), 3)
                g = grids[b]
                for a in range(max(i - n, 0), min(i + n + 1, SIZE)):
                    for c in range(max(j - n, 0), min(j + n + 1, SIZE)):
                        g[c * SIZE + a] += w
                break


def blur(g):
    o = g[:]
    for y in range(1, SIZE - 1):
        for x in range(1, SIZE - 1):
            k = y * SIZE + x
            o[k] = (g[k] * 4 + (g[k - 1] + g[k + 1] + g[k - SIZE] + g[k + SIZE]) * 2 + g[k - SIZE - 1] + g[k - SIZE + 1]
                    + g[k + SIZE - 1] + g[k + SIZE + 1]) / 16.0
    return o


grids = [blur(g) for g in grids]
rows = []
for y in range(SIZE):
    row = bytearray([0])
    for x in range(SIZE):
        for g in grids:
            row.append(int(255 * (1.0 - math.exp(-g[y * SIZE + x] * DENSITY_SCALE / 4.0))))
    rows.append(bytes(row))


def chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)


open(OUT, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
                      + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))
for b, g in enumerate(grids):
    print(b, sum(1 for v in g if v > 0.5) / len(g))
