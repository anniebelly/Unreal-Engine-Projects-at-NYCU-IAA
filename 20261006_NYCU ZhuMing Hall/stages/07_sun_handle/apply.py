# CM_3DGS_PP: swaps the depth blur (CustomBlur) for a dark outline, and the depth mosaic (CustomBrick) for the
# same outline, so the whole frame gets outlines and no mosaic. The graph wiring is untouched; only the two
# Custom nodes' HLSL changes. First run saves the original as CM_3DGS_PP_backup.
# MONET = True adds Impressionist colour on top. Re-runnable; tunables below.
# RESTORE = True puts the original blur + mosaic code back.
import json
import math
import random
import unreal

THICKNESS = 1.5          # line width in pixels
DEPTH_THRESHOLD = 0.03   # relative depth jump that starts a line (smaller = more lines)
COLOR_THRESHOLD = 0.25   # brightness jump that starts a line, for edges the depth misses (bigger = fewer)
LINE_COLOR = (0.02, 0.02, 0.02)
RESTORE = False

# Monet-style colour (Impressionist): soft painted dabs, lifted violet-blue shadows, warm sunlit highlights,
# pastel saturation, and outlines tinted from the paint instead of black.
MONET = True
PAINT_RADIUS = 2         # brush-dab samples per side (Kuwahara filter radius; 0 = off)
PAINT_SCALE = 0.3        # brush-dab size multiplier (smaller = finer patches)
FLOW = False             # paint patches keep flowing along "life veins":
                         # trunks + leaves stream bottom-to-top, the soil circles in place
FLOW_UP_SPEED = 0.35     # upward stream cycles per second (trunks)
LEAF_SPEED = 4.68        # leaves flow this many times faster than trunks
FLOW_UP_LENGTH = 7.2     # pixels a patch travels upward per cycle
FLOW_CIRCLE_SPEED = 1.2  # soil circling, radians per second
FLOW_CIRCLE_RADIUS = 3.0 # pixels
SWAY = True              # big trees' leaves and the rows of shrubs move in the wind; everything else stays put
# Seaside-shrub wind: calm, then a big gust sweeps through and everything green swings left and right in rhythm,
# then it settles. Foliage shifts as whole masses (no small-scale warping, which melts the leaves).
SWAY_AMOUNT = 0.03       # peak swing in a gust, fraction of screen width (48 px on a 1600 px screen)
SWAY_RHYTHM = 2.6        # seconds per left-right swing
SWAY_RATE_SPREAD = 0.25  # each tree's rhythm differs by up to this fraction
TREE_GUST_SPREAD = 0.7   # how far apart in the gust cycle trees are hit (0 = together, 1 = fully scattered)
GUST_PERIOD = 7.0        # seconds between gusts
GUST_SHARPNESS = 3.0     # higher = shorter gusts with longer calm between them
SWAY_CALM = 0.12         # strength left between gusts (0 = fully still)
GUST_SPEED = 400.0       # cm per second the gust front travels, reaching one tree after another
PLANT_MIN_HEIGHT = 35.0  # cm above the ground; green lower than this (grass, moss on the soil) stays still
SHRUB_SCALE = 0.5        # shrub swing relative to SWAY_AMOUNT
TREE_SPEED = 0.5         # tree motion speed: their swing and gusts run at this fraction of the base timing
TRUNK_RADIUS = 90.0      # cm around each detected trunk that never moves, and that leaves can't drag along
LOW_SHRUB_SWING = 0.75   # low shrubs from low_shrubs.png swing at least this much of the shrub setting, despite being short
LOW_SHRUB_FILE = unreal.Paths.project_saved_dir() + "CMgit/low_shrubs.png"
LOW_SHRUB_NAME = "T_LowShrubs"
SHRUB_TOP = 250.0        # cm; below this counts as shrub, which ripples along its row instead of following a tree
SHRUB_BEND_HEIGHT = 150.0  # cm; shrubs are rooted: the foot stays put, full swing from this height up
ROW_RIPPLE = 0.012       # how quickly the swing changes along a shrub row, radians per cm
# Ground of the scan as a smooth cubic surface, least-squares fit to zhuming_ground.json within 30 m
# (x, y in scan-local units of 10 m, height out in cm; median error 8 cm): 1, x, y, xx, xy, yy, xxx, xxy, xyy, yyy
GROUND_FIT = (174.82, -72.22, -49.3, 11.34, 14.51, 5.02, -1.05, -1.46, -3.94, -1.19)
LEAF_MASK_RADIUS = 0.032 # how far leaves may swing over their surroundings; keep at least SWAY_AMOUNT
LEAF_STREAM = 0.0        # bottom-to-top colour stream kept on green areas (1 = full)
CROWN_RADIUS = 300.0     # cm; how far around a trunk that tree's own sway reaches
TREE_COUNT = 48          # strongest trunks from zhuming_trunks.json that get their own sway
TREE_SPACING = 300.0     # cm; trunk detections closer than this count as the same tree
WIND_DIR = (0.8, 0.6)    # gusts travel this way, reaching one tree after another
TRUNKS_JSON = unreal.Paths.project_saved_dir() + "CMgit/zhuming_trunks.json"
GROUND_HEIGHT = 50.0     # cm above the ground plane still counted as soil
ALIVE_SAT = (0.12, 0.25) # saturation range where things start to count as living (green/brown);
                         # grey/white/black things (buildings, iron gates) stay still
BRIGHTNESS = 1.1         # overall brightness (1.1 = +10 %)
LIGHT_TINT = (1.0, 0.93, 0.76)      # warm sunlight in the highlights
SATURATION = 1.4
CONTRAST = 1.36          # light/dark separation (1 = unchanged)
PIVOT = 0.3              # brightness that contrast pivots around
BANDS = 12               # tonal steps for clear 濃淡 (0 = smooth)
PASTEL = 0.10            # mix toward white, only in the lit areas
DARK_LO, DARK_HI = 0.08, 0.224  # darks below DARK_HI fade into the line colour, fully at DARK_LO
MONET_LINE_COLOR = (0.05, 0.05, 0.11)   # deep blue-violet ink shared by outlines and darks
LINE_STRENGTH = 1.0      # outline opacity in Monet mode
HIGHLIGHT_BOOST = 0.4    # extra brightness in the lit areas (0 = off)

# "Grand avenue": a spotlight-like warm pool along the central road, from the PlayerStart to the preview
# mesh (both read from the level), lit in world space so it stays on the road as the camera moves.
ROAD = True
ROAD_HALF_WIDTH = 170.0  # cm, fully lit half width
ROAD_SOFT = 140.0        # cm, soft falloff beyond that
ROAD_HEIGHT = 120.0      # cm above the road that still gets light (keeps trees/fence out)
ROAD_BOOST = 1.1         # how much brighter the road gets
ROAD_TINT = (1.0, 0.94, 0.80)

# Sun handle: the level's DirectionalLight drives everything live, no script needed. Rotate it to move the sun,
# its Intensity and Light Color set the strength and tint. The scan ignores real lights, so the material redoes
# the sunlight: for each ground pixel it looks toward the sun through the canopy map baked by bake_canopy.py.
SUN = True
SUN_LABEL = "SunHandle"
SUN_NOON_PITCH = -78.0   # set once, on the first run: the light points almost straight down
SUN_BASE_INTENSITY = 3.0 # the light's Intensity that counts as normal; fixed, so the brightness slider stays meaningful
SUN_RESET_INTENSITY = True   # put Intensity back to SUN_BASE_INTENSITY when this runs; False keeps the slider's value
SKY_KEEP = 0.7           # how much the sky keeps its own colour instead of the grade, so it doesn't blow out
DAY_RANGE = 0.6          # sun height (sine of elevation) where full daylight is reached; below it the scene dims
DAY_DIM = 0.3            # scene brightness at sunrise and sunset
SUNSET_WARMTH = 0.8      # how orange the scene turns when the sun is low
SUN_POOL = 0.6           # how much brighter open ground gets; same soft multiply as the road light, kept below it
SUN_SOFTNESS = 0.06      # blur of the pool edges, per cm of canopy height (bigger = softer)
CANOPY_ABSORB = 2.5      # how much sun the canopy blocks (bigger = smaller, sharper pools)
SUN_MAP_FILE = unreal.Paths.project_saved_dir() + "CMgit/sun_canopy.png"
SUN_MAP_PATH = "/Game/ZhuMingClean"
SUN_MAP_NAME = "T_SunCanopy"
SUN_MAP_MIN, SUN_MAP_SPAN = -3200.0, 8000.0   # same as bake_canopy.py
SUN_BANDS = (425.0, 800.0, 1400.0)            # middle height of each baked band, cm above ground

# God rays: light shafts streaming from the sun (the level's DirectionalLight) through the gaps in the canopy.
# Screen-space, so they show whenever the view faces the sun; the splat scan ignores real lights/fog.
RAYS = True
RAY_SAMPLES = 48
RAY_LENGTH = 0.9         # how far toward the sun each pixel looks (0-1 of the way)
RAY_DECAY = 0.965        # falloff along a shaft
RAY_INTENSITY = 2.2
RAY_COLOR = (1.0, 0.9, 0.68)
RAY_SKY_DEPTH = 3000.0   # cm; only gaps farther than this (sky) let light through

SHOT_COUNT = 0           # review frames taken after each run (each pops an editor notification); 8 to review motion
SHOT_GAP = 1.0           # seconds between them

MAT = "/Game/_CMgit/_HLSL/CM_3DGS_PP"
BACKUP = MAT + "_backup"
LEVEL = "Lvl_ZhuMingHall"

OUTLINE = """const float2 ScreenMult = View.ViewSizeAndInvSize.xy * View.BufferSizeAndInvSize.zw;
ScreenUV *= ScreenMult;
const int TexIndex = 14;
const float Thickness = {th};
const float Threshold = {dt};
const float ColorThreshold = {ct};
const float3 LineColor = float3({lc});
float2 px = View.BufferSizeAndInvSize.zw * Thickness;
float4 c = SceneTextureLookup(ScreenUV, TexIndex, false);
// depth edges
float d = SceneTextureLookup(ScreenUV, 1, false).r;
float dL = SceneTextureLookup(ScreenUV - float2(px.x, 0.0), 1, false).r;
float dR = SceneTextureLookup(ScreenUV + float2(px.x, 0.0), 1, false).r;
float dU = SceneTextureLookup(ScreenUV - float2(0.0, px.y), 1, false).r;
float dD = SceneTextureLookup(ScreenUV + float2(0.0, px.y), 1, false).r;
float diff = (abs(dL - d) + abs(dR - d) + abs(dU - d) + abs(dD - d)) / max(d, 1.0);
float edge = smoothstep(Threshold, 2.0 * Threshold, diff);
// brightness edges, for the splat scan where depth has no lines
const float3 W = float3(0.3, 0.59, 0.11);
float l = dot(c.rgb, W);
float lL = dot(SceneTextureLookup(ScreenUV - float2(px.x, 0.0), TexIndex, false).rgb, W);
float lR = dot(SceneTextureLookup(ScreenUV + float2(px.x, 0.0), TexIndex, false).rgb, W);
float lU = dot(SceneTextureLookup(ScreenUV - float2(0.0, px.y), TexIndex, false).rgb, W);
float lD = dot(SceneTextureLookup(ScreenUV + float2(0.0, px.y), TexIndex, false).rgb, W);
float ldiff = abs(lL - l) + abs(lR - l) + abs(lU - l) + abs(lD - l);
edge = max(edge, smoothstep(ColorThreshold, 2.0 * ColorThreshold, ldiff));
c.rgb = lerp(c.rgb, LineColor, edge);
return c;""".format(th=THICKNESS, dt=DEPTH_THRESHOLD, ct=COLOR_THRESHOLD, lc=", ".join(str(v) for v in LINE_COLOR))


def f3(v):
    return "float3({})".format(", ".join(str(x) for x in v))


# Monet: paint dabs (4-sector Kuwahara), then the grade, then soft tinted outlines.
MONET_PAINT = """const int R = {r};
// Life-vein flow: soil = near the ground plane (PlayerStart -> preview mesh) and not green; everything above
// (trunks, leaves) streams upward. Grey/white/black (non-living: buildings, iron gates) stays still. The upward stream uses two crossfaded phases so it loops without a jump.
float soil = 0.0;
float green = 0.0;
float tt = View.GameTime;
float2 circ = float2(0.0, 0.0);
float upPhase = 0.0;
float alive = 0.0;
if ({flow})
{{
    const float3 GA = {ra};
    const float3 GB = {rb};
    float2 gab = GB.xy - GA.xy;
    float gt = dot(WorldPos.xy - GA.xy, gab) / max(dot(gab, gab), 1.0);
    float above = WorldPos.z - lerp(GA.z, GB.z, gt);
    green = saturate((c.g - max(c.r, c.b)) * 4.0);
    float cmax = max(c.r, max(c.g, c.b));
    float sat = (cmax - min(c.r, min(c.g, c.b))) / max(cmax, 0.001);
    float brown = smoothstep(0.02, 0.1, c.r - c.b);
    alive = smoothstep({as0}, {as1}, sat) * max(green, brown);
    soil = (1.0 - smoothstep({gh}, {gh} * 1.6, above)) * (1.0 - green);
    float ph = dot(WorldPos.xy, float2(0.013, 0.017));
    circ = float2(cos(tt * {cs} + ph), sin(tt * {cs} + ph)) * {cr};
    upPhase = tt * {us} * lerp(1.0, {lf}, green) + sin(dot(WorldPos.xy, float2(0.004, 0.003))) * 0.25;
}}
float3 res[2] = {{ c.rgb, c.rgb }};
float wsum[2] = {{ 0.5, 0.5 }};
const float2 ox[4] = {{ float2(-1,-1), float2(1,-1), float2(-1,1), float2(1,1) }};
float n = (R + 1) * (R + 1);
for (int layer = 0; layer < ({flow} ? 2 : 1); layer++)
{{
    float p = frac(upPhase + layer * 0.5);
    wsum[layer] = {flow} ? 1.0 - abs(2.0 * p - 1.0) : 1.0;
    float2 off = lerp(float2(0.0, p * {ul} * lerp(1.0, {ls2}, green)), circ, soil) * alive * View.BufferSizeAndInvSize.zw;
    float3 m[4] = {{ float3(0,0,0), float3(0,0,0), float3(0,0,0), float3(0,0,0) }};
    float3 s[4] = {{ float3(0,0,0), float3(0,0,0), float3(0,0,0), float3(0,0,0) }};
    for (int k = 0; k < 4; k++)
    {{
        for (int i = 0; i <= R; i++)
        {{
            for (int j = 0; j <= R; j++)
            {{
                float3 t = SceneTextureLookup(ScreenUV + off + float2(i, j) * {ps} * ox[k] * View.BufferSizeAndInvSize.zw, TexIndex, false).rgb;
                m[k] += t;
                s[k] += t * t;
            }}
        }}
    }}
    float best = 1e9;
    for (int q = 0; q < 4; q++)
    {{
        float3 mu = m[q] / n;
        float3 v = abs(s[q] / n - mu * mu);
        float vs = v.r + v.g + v.b;
        if (vs < best) {{ best = vs; res[layer] = mu; }}
    }}
}}
c.rgb = {flow} ? (res[0] * wsum[0] + res[1] * wsum[1]) / max(wsum[0] + wsum[1], 0.001) : res[0];
"""
MONET_GRADE = """c.rgb = saturate((c.rgb - {pivot}) * {contrast} + {pivot});
float lum = dot(c.rgb, W);
if ({bands} > 0)
{{
    float b = lum * {bands};
    float q = (floor(b) + smoothstep(0.3, 0.7, frac(b))) / {bands};
    c.rgb *= q / max(lum, 0.001);
    lum = q;
}}
c.rgb = lerp(float3(lum, lum, lum), c.rgb, {sat});
c.rgb = lerp(c.rgb, c.rgb * {lt} * 1.08, saturate(lum * 1.5));
c.rgb = lerp(c.rgb, float3(1, 1, 1), {pastel} * saturate(lum * 1.5));
c.rgb *= 1.0 + {hb} * smoothstep(0.4, 0.85, lum);
c.rgb *= {br};
c.rgb = max(c.rgb, 0.0);
float road = 0.0;
if ({road})
{{
    const float3 A = {ra};
    const float3 B = {rb};
    float2 ab = B.xy - A.xy;
    float t = saturate(dot(WorldPos.xy - A.xy, ab) / max(dot(ab, ab), 1.0));
    float dist = length(WorldPos.xy - (A.xy + ab * t));
    float above = WorldPos.z - lerp(A.z, B.z, t);
    road = (1.0 - smoothstep({rw}, {rw} + {rs}, dist)) * (1.0 - smoothstep({rh} * 0.5, {rh}, above));
    road *= 1.0 - 0.35 * saturate(dist / {rw});  // hotter down the middle, like a spotlight
}}
// road light and sun pools are one soft light: the stronger of the two, set by the sun handle
float boost = max(road * {rb_}, sunPool * {pl}) * sunGain;
float3 lightTint = {rt} * sunTint;
c.rgb = c.rgb * (1.0 + boost) * lerp(float3(1.0, 1.0, 1.0), lightTint, saturate(boost)) + lightTint * 0.06 * boost;
// the sky skips most of the grade, or contrast and highlight boosts wash it to white
float skyM = smoothstep(2500.0, 6000.0, d) * smoothstep(-0.03, 0.03, skyOrig.b - skyOrig.g);
c.rgb = lerp(c.rgb, skyOrig, skyM * {sk});
LineColor = {lc};
c.rgb = lerp(c.rgb, LineColor, smoothstep({dhi}, {dlo}, lum) * (1.0 - saturate(max(road, sunPool * sunGain))));
edge *= {ls};
"""


# Moves the sampling position before anything is read, so colour and outlines shift together. A pixel moves only
# if it shows, or is about to show, a leaf standing clear of the ground; trunks, soil, grass, fence, walls and sky
# hold still. Trees are hit at scattered points of the gust cycle so only some of them swing at any moment.
GROUND_CODE = """// clamped to the fitted area, so far pixels and the sky don't send the cubic off to infinity
float2 gxy = clamp((WorldPos.xy - float2({ox}, {oy})) / 1000.0, -2.5, 3.8);
const float gc[10] = {{ {gf} }};
float groundZ = gc[0] + gc[1] * gxy.x + gc[2] * gxy.y + gc[3] * gxy.x * gxy.x + gc[4] * gxy.x * gxy.y + gc[5] * gxy.y * gxy.y
              + gc[6] * gxy.x * gxy.x * gxy.x + gc[7] * gxy.x * gxy.x * gxy.y + gc[8] * gxy.x * gxy.y * gxy.y + gc[9] * gxy.y * gxy.y * gxy.y;
float aboveG = WorldPos.z - ({oz} + groundZ);
"""
SWAY_CODE = """if ({on})
{{
    float2 fuv0 = ScreenUV / ScreenMult;
    float2 ndc = (fuv0 * 2.0 - 1.0) * float2(1.0, -1.0);
    float3 ray = normalize(mul(float4(ndc * 1000.0, 1000.0, 1.0), View.ScreenToTranslatedWorld).xyz - View.TranslatedWorldCameraOrigin);
    float aspect = View.ViewSizeAndInvSize.x * View.ViewSizeAndInvSize.w;
    // low shrubs are too short to tell from grass by height, so they come from a mask baked out of the scan
    float2 shrubUV = (WorldPos.xy - float2({ox}, {oy}) - {mn}) / {sp};
    float lowShrub = smoothstep(0.1, 0.4, Texture2DSampleLevel(ShrubTex, ShrubTexSampler, shrubUV, 0.0).r) * (1.0 - smoothstep(150.0, 260.0, aboveG));
    float plant = max(smoothstep({ph}, {ph} * 1.6, aboveG), lowShrub);
    float leafNear = 0.0;
    if (plant > 0.001)
    {{
        for (int st = 0; st < 16; st++)
        {{
            float ang = st * 2.39996;
            float rr = {rad} * sqrt((st + 0.5) / 16.0);
            float3 tc = SceneTextureLookup(ScreenUV + float2(cos(ang), sin(ang) * aspect) * rr * ScreenMult, TexIndex, false).rgb;
            float tmax = max(tc.r, max(tc.g, tc.b));
            float tsat = (tmax - min(tc.r, min(tc.g, tc.b))) / max(tmax, 0.001);
            leafNear += smoothstep(0.22, 0.38, tsat) * smoothstep(0.82, 0.95, tc.g / max(tc.r, 0.01)) * smoothstep(1.05, 1.25, tc.g / max(tc.b, 0.01));
        }}
        leafNear /= 16.0;
    }}
    if (leafNear > 0.01)
    {{
        const float4 TREES[{n}] = {{ {trees} }};
        float swt = View.GameTime;
        float2 rayH = ray.xy / max(length(ray.xy), 0.001);
        float wsum = 0.0001;
        float wave = 0.0;
        float envSum = 0.0;
        float trunkD = 0.0;
        for (int ti = 0; ti < {n}; ti++)
        {{
            float4 tr = TREES[ti];
            float2 toT = tr.xy - CamPos.xy;
            float dist = max(length(toT), 100.0);
            float sigma = atan2({crown}, dist);
            float w = exp(-6.0 * (1.0 - dot(rayH, toT / dist)) / (sigma * sigma)) * sigma;
            // this tree's place in the gust cycle: the front's arrival plus its own scattered delay
            float gt = swt * {ts} - dot(tr.xy, float2({wx}, {wy})) / {gv} - frac(tr.w * 3.17) * {gp} * {tg};
            float pulse = sin(3.14159 * gt / {gp});
            float env = lerp({calm}, 1.0, pow(pulse * pulse, {gs2}) * (0.65 + 0.35 * sin(gt * 0.37)));
            wave += w * env * sin(swt * {ts} * 6.2832 / {rh} * tr.z + tr.w);
            envSum += w * env;
            wsum += w;
            trunkD = max(trunkD, 1.0 - smoothstep({tk}, {tk} * 1.3, length(WorldPos.xy - tr.xy)));
        }}
        wave /= wsum;
        // shrub rows: the swing ripples along the row, at the strength of the gust nearby
        float rowWave = (envSum / wsum) * sin(swt * 6.2832 / {rh} - dot(WorldPos.xy, float2({wx}, {wy})) * {rr});
        float shrub = 1.0 - smoothstep({st0}, {st0} * 1.3, aboveG);
        wave = lerp(wave, rowWave, shrub);
        float3 camR = normalize(mul(float4(1000.0, 0.0, 1000.0, 1.0), View.ScreenToTranslatedWorld).xyz - mul(float4(-1000.0, 0.0, 1000.0, 1.0), View.ScreenToTranslatedWorld).xyz);
        float windS = dot(float3({wx}, {wy}, 0.0), camR);
        windS = (windS < 0.0 ? -1.0 : 1.0) * max(abs(windS), 0.5);
        float rooted = max(lerp(0.2, 1.0, saturate(aboveG / {sb})), lowShrub * {ls});
        // swings sideways, dipping slightly at the far ends of the swing
        float2 bend = float2(windS * wave, -0.2 * wave * wave) * {amt} * rooted * lerp(1.0, {ss}, shrub);
        float2 src = clamp(ScreenUV + bend * float2(1.0, aspect) * ScreenMult, float2(0.0, 0.0), ScreenMult);
        float3 cd = SceneTextureLookup(ScreenUV, TexIndex, false).rgb;
        float3 cs = SceneTextureLookup(src, TexIndex, false).rgb;
        float dmax = max(cd.r, max(cd.g, cd.b));
        float smax = max(cs.r, max(cs.g, cs.b));
        float leafD = smoothstep(0.22, 0.38, (dmax - min(cd.r, min(cd.g, cd.b))) / max(dmax, 0.001)) * smoothstep(0.82, 0.95, cd.g / max(cd.r, 0.01)) * smoothstep(1.05, 1.25, cd.g / max(cd.b, 0.01));
        float leafS = smoothstep(0.22, 0.38, (smax - min(cs.r, min(cs.g, cs.b))) / max(smax, 0.001)) * smoothstep(0.82, 0.95, cs.g / max(cs.r, 0.01)) * smoothstep(1.05, 1.25, cs.g / max(cs.b, 0.01));
        // dark leaves inside dense foliage count too, but not bark or blue gaps (red or blue at least equal to green)
        float notBark = 1.0 - smoothstep(0.95, 1.05, max(cd.r, cd.b) / max(cd.g, 0.01));
        notBark *= smoothstep(0.12, 0.25, (dmax - min(cd.r, min(cd.g, cd.b))) / max(dmax, 0.001));
        // Where the pixel would read from: if that is a trunk, stay put, or the trunk's edge would swing with the leaves.
        float2 ndcS = ((src / ScreenMult) * 2.0 - 1.0) * float2(1.0, -1.0);
        float depthS = SceneTextureLookup(src, 1, false).r;
        float2 srcXY = mul(float4(ndcS * depthS, depthS, 1.0), View.ScreenToTranslatedWorld).xy - View.TranslatedWorldCameraOrigin.xy + CamPos.xy;
        float trunkS = 0.0;
        for (int tj = 0; tj < {n}; tj++)
        {{
            trunkS = max(trunkS, 1.0 - smoothstep({tk}, {tk} * 1.3, length(srcXY - TREES[tj].xy)));
        }}
        float moveIt = max(max(leafD, leafS), smoothstep(0.45, 0.7, leafNear) * notBark) * plant * (1.0 - max(trunkD, trunkS));
        ScreenUV = lerp(ScreenUV, src, moveIt);
    }}
}}
"""
SUN_CODE = """float sunPool = 0.0;
float sunGain = 1.0;
float3 sunTint = float3(1.0, 1.0, 1.0);
float3 skyOrig = c.rgb;
if ({on})
{{
    float3 sunD = View.AtmosphereLightDirection[0].xyz;
    float3 sunI = View.AtmosphereLightIlluminanceOnGroundPostTransmittance[0].rgb;
    float sunL = dot(sunI, W);
    float day = smoothstep(-0.05, {dr}, sunD.z);
    sunGain = clamp(sunL / {ref}, 0.0, 1.5) * day;
    sunTint = lerp(float3(1.0, 1.0, 1.0), sunI / max(sunL, 0.001), 0.5);
    // the whole picture follows the sun: dim and orange when low, full and neutral when high
    c.rgb *= lerp({dd}, 1.0, day) * lerp(float3(1.0, 1.0, 1.0), float3(1.15, 0.9, 0.62), {wm} * (1.0 - saturate(sunD.z / {dr})));
    skyOrig = c.rgb;
    float gw = 1.0 - smoothstep(60.0, 220.0, aboveG);
    if (gw > 0.001 && sunD.z > 0.05)
    {{
        // walk from this point toward the sun through the three canopy bands; the higher the leaves, the softer
        // their shadow, so each band is averaged over a wider patch
        float2 slope = sunD.xy / max(sunD.z, 0.15);
        float2 lp = WorldPos.xy - float2({ox}, {oy}) - {mn};
        const float2 tap[5] = {{ float2(0, 0), float2(1, 0), float2(-1, 0), float2(0, 1), float2(0, -1) }};
        float3 dens = float3(0.0, 0.0, 0.0);
        for (int sk = 0; sk < 5; sk++)
        {{
            dens.r += Texture2DSampleLevel(CanopyTex, CanopyTexSampler, (lp + slope * ({b0} - aboveG) + tap[sk] * {b0} * {sf}) / {sp}, 0.0).r;
            dens.g += Texture2DSampleLevel(CanopyTex, CanopyTexSampler, (lp + slope * ({b1} - aboveG) + tap[sk] * {b1} * {sf}) / {sp}, 0.0).g;
            dens.b += Texture2DSampleLevel(CanopyTex, CanopyTexSampler, (lp + slope * ({b2} - aboveG) + tap[sk] * {b2} * {sf}) / {sp}, 0.0).b;
        }}
        sunPool = gw * smoothstep(0.1, 0.9, exp(-{ab} * (dens.r + dens.g + dens.b) / 5.0));
    }}
}}
"""
RAYS_CODE = """if ({on})
{{
    const float3 SunDir = View.AtmosphereLightDirection[0].xyz;
    float4 sc = mul(float4(View.TranslatedWorldCameraOrigin + SunDir * 1000000.0, 1.0), View.TranslatedWorldToClip);
    if (sc.w > 0.0)
    {{
        float2 sunUV = ((sc.xy / sc.w) * float2(0.5, -0.5) + 0.5) * ScreenMult;
        float2 delta = (sunUV - ScreenUV) * {ln} / {n};
        float2 ruv = ScreenUV;
        float illum = 1.0;
        float acc = 0.0;
        for (int r = 0; r < {n}; r++)
        {{
            ruv += delta;
            float rl = dot(SceneTextureLookup(ruv, TexIndex, false).rgb, W);
            float rd = SceneTextureLookup(ruv, 1, false).r;
            acc += smoothstep(0.45, 0.85, rl) * smoothstep({sky}, {sky} * 2.5, rd) * illum;
            illum *= {dc};
        }}
        acc /= {n};
        float fade = 1.0 - smoothstep(0.6, 1.4, length(sunUV / ScreenMult - 0.5));
        c.rgb += {rc} * acc * {it} * fade * {rk};
    }}
}}
"""


def build_code():
    rays = RAYS_CODE.format(on=int(RAYS), ln=RAY_LENGTH, n=int(RAY_SAMPLES), sky=RAY_SKY_DEPTH,
                            dc=RAY_DECAY, rc=f3(RAY_COLOR), it=RAY_INTENSITY,
                            rk="(1.0 - skyM * {})".format(SKY_KEEP) if MONET else "1.0")
    sway = SWAY_CODE.format(on=int(SWAY), rad=LEAF_MASK_RADIUS, amt=SWAY_AMOUNT, n=len(TREE_LIST), crown=CROWN_RADIUS,
                            wx=WIND_DIR[0], wy=WIND_DIR[1], gv=GUST_SPEED, gp=GUST_PERIOD, gs2=GUST_SHARPNESS,
                            tg=TREE_GUST_SPREAD, ts=TREE_SPEED, ox=SPLAT_OFFSET[0], oy=SPLAT_OFFSET[1], mn=SUN_MAP_MIN,
                            sp=SUN_MAP_SPAN, ls=LOW_SHRUB_SWING, tk=TRUNK_RADIUS, ss=SHRUB_SCALE, calm=SWAY_CALM, rh=SWAY_RHYTHM, ph=PLANT_MIN_HEIGHT, st0=SHRUB_TOP,
                            sb=SHRUB_BEND_HEIGHT, rr=ROW_RIPPLE,
                            trees=", ".join("float4({:.1f}, {:.1f}, {:.3f}, {:.3f})".format(*t) for t in TREE_LIST))
    ground = GROUND_CODE.format(ox=SPLAT_OFFSET[0], oy=SPLAT_OFFSET[1], oz=SPLAT_OFFSET[2],
                                gf=", ".join(str(v) for v in GROUND_FIT))
    base = OUTLINE.replace("float2 px =", ground + sway + "float2 px =")
    sunc = SUN_CODE.format(on=int(SUN), ref=SUN_BASE_INTENSITY * 0.8, dr=DAY_RANGE, dd=DAY_DIM, wm=SUNSET_WARMTH, ox=SPLAT_OFFSET[0], oy=SPLAT_OFFSET[1], b0=SUN_BANDS[0],
                           b1=SUN_BANDS[1], b2=SUN_BANDS[2], mn=SUN_MAP_MIN, sp=SUN_MAP_SPAN, ab=CANOPY_ABSORB,
                           sf=SUN_SOFTNESS)
    if not MONET:
        return base.replace("return c;", rays + "return c;")
    code = base.replace("const float3 LineColor", "float3 LineColor")
    paint = MONET_PAINT.format(r=int(PAINT_RADIUS), ps=PAINT_SCALE, flow=int(FLOW), ra=f3(ROAD_A), rb=f3(ROAD_B),
                               gh=GROUND_HEIGHT, cs=FLOW_CIRCLE_SPEED, cr=FLOW_CIRCLE_RADIUS,
                               us=FLOW_UP_SPEED, ul=FLOW_UP_LENGTH, as0=ALIVE_SAT[0], as1=ALIVE_SAT[1], lf=LEAF_SPEED, ls2=LEAF_STREAM) if PAINT_RADIUS > 0 else ""
    grade = MONET_GRADE.format(pivot=PIVOT, contrast=CONTRAST, bands=int(BANDS), sat=SATURATION,
                               lt=f3(LIGHT_TINT), pastel=PASTEL, lc=f3(MONET_LINE_COLOR),
                               dlo=DARK_LO, dhi=DARK_HI, ls=LINE_STRENGTH, hb=HIGHLIGHT_BOOST, br=BRIGHTNESS,
                               road=int(ROAD), ra=f3(ROAD_A), rb=f3(ROAD_B), rw=ROAD_HALF_WIDTH, rs=ROAD_SOFT,
                               rh=ROAD_HEIGHT, rb_=ROAD_BOOST, rt=f3(ROAD_TINT), pl=SUN_POOL, sk=SKY_KEEP)
    # Edges are found on the photo; the paint dabs and grade then go on before the lines are drawn.
    return code.replace("c.rgb = lerp(c.rgb, LineColor, edge);", paint + sunc + grade + "c.rgb = lerp(c.rgb, LineColor, edge);").replace(
        "return c;", rays + "return c;")


def log(msg):
    unreal.log("[OUTLINE] " + msg)


eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
if not eal.does_asset_exist(BACKUP):
    eal.duplicate_asset(MAT, BACKUP)
    log("backup saved: " + BACKUP)

mat = unreal.load_asset(MAT)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(mat)


def custom_nodes(material):
    # Every Custom node reachable from the material outputs.
    seen, found = set(), {}
    stack = [mel.get_material_property_input_node(material, p) for p in
             (unreal.MaterialProperty.MP_EMISSIVE_COLOR, unreal.MaterialProperty.MP_BASE_COLOR,
              unreal.MaterialProperty.MP_OPACITY)]
    while stack:
        e = stack.pop()
        if e is None or e.get_path_name() in seen:
            continue
        seen.add(e.get_path_name())
        if isinstance(e, unreal.MaterialExpressionCustom):
            found[str(e.get_editor_property("description"))] = e
        stack.extend(mel.get_inputs_for_material_expression(material, e))
    log("graph: {} nodes, custom: {}".format(len(seen), ", ".join(found) or "(none)"))
    return found


# Road end points from the level: PlayerStart (its feet) and the preview mesh (its base).
ROAD_A, ROAD_B = (256.32, -72.11, -10.0), (639.0, 249.0, -137.0)
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if isinstance(a, unreal.PlayerStart):
        l = a.get_actor_location()
        ROAD_A = (l.x, l.y, l.z - 90.0)
    elif a.get_actor_label() == "MatPreviewMesh":
        o, e = a.get_actor_bounds(False)
        ROAD_B = (o.x, o.y, o.z - e.z)
log("road {} -> {}".format(ROAD_A, ROAD_B))

# The sun handle: the level's DirectionalLight, set up once at noon and left alone on later runs.
sun = next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
           if isinstance(a, unreal.DirectionalLight))
sun_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
if sun.get_actor_label() != SUN_LABEL:
    sun.modify()
    sun_comp.modify()
    sun_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    try:
        sun_comp.set_editor_property("atmosphere_sun_light", True)
    except Exception as e:
        log("atmosphere sun flag not set: {}".format(e))
    r = sun.get_actor_rotation()
    sun.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=SUN_NOON_PITCH, yaw=r.yaw), False)
    sun.set_actor_location(unreal.Vector(ROAD_A[0], ROAD_A[1], ROAD_A[2] + 700.0), False, False)
    sun.set_actor_label(SUN_LABEL)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("sun handle set to noon")
# back to normal strength: real sky brightness follows the light's Intensity
if SUN_RESET_INTENSITY:
    sun.modify()
    sun_comp.modify()
    sun_comp.set_intensity(SUN_BASE_INTENSITY)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
log("sun intensity {} rotation {}".format(sun_comp.get_editor_property("intensity"), sun.get_actor_rotation()))

def data_texture(name, source):
    # Baked maps for the material: imported once, as plain data rather than colour.
    path = SUN_MAP_PATH + "/" + name
    if not eal.does_asset_exist(path):
        task = unreal.AssetImportTask()
        task.filename = source
        task.destination_path = SUN_MAP_PATH
        task.destination_name = name
        task.replace_existing = True
        task.automated = True
        task.save = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset(path)
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
        tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
        tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
        eal.save_loaded_asset(tex)
        log("imported " + path)
    return unreal.load_asset(path)


SUN_TEX = data_texture(SUN_MAP_NAME, SUN_MAP_FILE)
SHRUB_TEX = data_texture(LOW_SHRUB_NAME, LOW_SHRUB_FILE)


# Trees for the sway: strongest trunk detections, one per tree, each with its own rate and phase.
splat = next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
             if a.get_class().get_name() == "GaussianSplatActor")
off = splat.get_actor_location()
SPLAT_OFFSET = (off.x, off.y, off.z)
rng = random.Random(1006)
TREE_LIST = []
for t in sorted(json.load(open(TRUNKS_JSON)), key=lambda t: -t["score"]):
    x, y = t["local"][0] + off.x, t["local"][1] + off.y
    if len(TREE_LIST) < TREE_COUNT and all(math.hypot(x - q[0], y - q[1]) >= TREE_SPACING for q in TREE_LIST):
        TREE_LIST.append((x, y, 1.0 + rng.uniform(-SWAY_RATE_SPREAD, SWAY_RATE_SPREAD), rng.uniform(0.0, 2.0 * math.pi)))
log("{} trees sway on their own".format(len(TREE_LIST)))


def ensure_pin(material, node, name, expression_class, dy, setup=None):
    # Adds an input on the Custom node fed by the given expression (pixel world position, camera position).
    pins = list(node.get_editor_property("inputs"))
    if any(str(p.get_editor_property("input_name")) == name for p in pins):
        return
    pin = unreal.CustomInput()
    pin.set_editor_property("input_name", name)
    pins.append(pin)
    node.set_editor_property("inputs", pins)
    e = mel.create_material_expression(material, expression_class,
                                       node.get_editor_property("material_expression_editor_x") - 300,
                                       node.get_editor_property("material_expression_editor_y") + dy)
    if setup:
        setup(e)
    mel.connect_material_expressions(e, "", node, name)
    log("added {} input".format(name))


nodes = custom_nodes(mat)
backup_nodes = custom_nodes(unreal.load_asset(BACKUP)) if RESTORE else {}
for name in ("CustomBlur", "CustomBrick"):
    n = nodes.get(name)
    if n is None:
        log(name + " not found in graph")
        continue
    code = backup_nodes[name].get_editor_property("code") if RESTORE else build_code()
    n.modify()
    if not RESTORE:
        if SWAY or (MONET and (ROAD or FLOW)):
            ensure_pin(mat, n, "WorldPos", unreal.MaterialExpressionWorldPosition, 200)
        if SWAY:
            ensure_pin(mat, n, "CamPos", unreal.MaterialExpressionCameraPositionWS, 300)
        def use_map(tex):
            def setup(e):
                e.set_editor_property("texture", tex)
                e.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            return setup
        if SUN:
            ensure_pin(mat, n, "CanopyTex", unreal.MaterialExpressionTextureObject, 400, use_map(SUN_TEX))
        if SWAY:
            ensure_pin(mat, n, "ShrubTex", unreal.MaterialExpressionTextureObject, 500, use_map(SHRUB_TEX))
    n.set_editor_property("code", code)
    log("{} -> {}".format(name, "original code" if RESTORE else ("outline + Monet" if MONET else "outline")))

mel.recompile_material(mat)
eal.save_loaded_asset(mat)
log("recompiled + saved")

# Make sure the level's PostProcessVolume actually uses it.
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if isinstance(a, unreal.PostProcessVolume):
        objs = [(b.object.get_path_name() if b.object else None, b.weight)
                for b in a.settings.weighted_blendables.array]
        log("{} {} blendables: {}".format(world.get_name(), a.get_actor_label(), objs))

if world.get_name() == LEVEL and SHOT_COUNT == 0:
    unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, "ZhuMingHall_sun.png")
if world.get_name() == LEVEL and SHOT_COUNT > 0:
    # Review frames from the current view (the camera is left alone), spread over one gust so the motion can be
    # compared. Needs Realtime on in the viewport.
    shots = {"left": SHOT_COUNT, "next": 0.0, "time": 0.0}

    def take_shot(dt):
        shots["time"] += dt
        if shots["time"] >= shots["next"]:
            i = SHOT_COUNT - shots["left"]
            unreal.AutomationLibrary.take_high_res_screenshot(960, 540, "ZhuMingHall_wind_{}.png".format(i))
            shots["left"] -= 1
            shots["next"] += SHOT_GAP
            if shots["left"] == 0:
                unreal.unregister_slate_post_tick_callback(shots["handle"])

    shots["handle"] = unreal.register_slate_post_tick_callback(take_shot)
