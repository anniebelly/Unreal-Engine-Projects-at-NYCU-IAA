# Bakes where low shrubs stand in the Zhu Ming Hall scan into a top-down mask for CM_3DGS_PP: green points that rise
# clearly above the local ground, as opposed to flat grass and moss. Run with plain python3 (not in the editor).
import math, struct, zlib

PLY = "path/to/your_scan.ply"
OUT = "low_shrubs.png"
SIZE = 512
MAP_MIN, MAP_SPAN = -3200.0, 8000.0       # same area as sun_canopy.png
MIN_OPACITY_LOGIT = -0.5
GROUND_CELL = 100.0                       # cm; local ground = low percentile of the points around here
SHRUB_RANGE = (15.0, 35.0)                # cm above local ground where green starts / fully counts as a shrub
GROW = 3                                  # cells (about 47 cm) a shrub spreads to cover its whole body
SHRUB_MAX = 250.0                         # cm; taller is tree canopy, handled elsewhere

cell = MAP_SPAN / SIZE
low = {}
green = {}
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
        if not (MAP_MIN <= x < MAP_MIN + MAP_SPAN and MAP_MIN <= y < MAP_MIN + MAP_SPAN):
            continue
        low.setdefault((int(x // GROUND_CELL), int(y // GROUND_CELL)), []).append(z)
        r, g, b = 0.5 + 0.282 * v[11], 0.5 + 0.282 * v[12], 0.5 + 0.282 * v[13]
        top = max(r, g, b)
        sat = (top - min(r, g, b)) / max(top, 0.001)
        if sat > 0.22 and g > r * 0.85 and g > b * 1.08:
            green.setdefault((int((x - MAP_MIN) / cell), int((y - MAP_MIN) / cell)), []).append((x, y, z))

base = {}
for k, zs in low.items():
    zs.sort()
    base[k] = zs[len(zs) // 10]


def local_ground(x, y):
    i, j = int(x // GROUND_CELL), int(y // GROUND_CELL)
    near = [base[(i + a, j + b)] for a in (-1, 0, 1) for b in (-1, 0, 1) if (i + a, j + b) in base]
    near.sort()
    return near[len(near) // 4]


def ramp(v, a, b):
    t = min(max((v - a) / (b - a), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


g = [0.0] * (SIZE * SIZE)
for (i, j), pts in green.items():
    if len(pts) < 2:
        continue
    hs = sorted(p[2] - local_ground(p[0], p[1]) for p in pts)
    h = hs[int(len(hs) * 0.9)]
    if h < SHRUB_MAX and 0 <= i < SIZE and 0 <= j < SIZE:
        g[j * SIZE + i] = ramp(h, *SHRUB_RANGE)


def blur(g):
    o = g[:]
    for y in range(1, SIZE - 1):
        for x in range(1, SIZE - 1):
            k = y * SIZE + x
            o[k] = (g[k] * 4 + (g[k - 1] + g[k + 1] + g[k - SIZE] + g[k + SIZE]) * 2 + g[k - SIZE - 1] + g[k - SIZE + 1]
                    + g[k + SIZE - 1] + g[k + SIZE + 1]) / 16.0
    return o


def grow(g, n):
    # fills the gaps inside a bush: each cell takes the strongest value within n cells
    for axis in (1, SIZE):
        o = g[:]
        for k in range(len(g)):
            for d in range(-n, n + 1):
                q = k + d * axis
                if 0 <= q < len(g) and g[q] > o[k]:
                    o[k] = g[q]
        g = o
    return g


g = blur(blur(grow(g, GROW)))
rows = []
for y in range(SIZE):
    row = bytearray([0])
    for x in range(SIZE):
        row.extend((min(int(g[y * SIZE + x] * 1.6 * 255), 255),) * 3)
    rows.append(bytes(row))


def chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)


open(OUT, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
                      + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))
print("shrub cover", sum(1 for v in g if v > 0.3) / len(g), "green cells", len(green))
