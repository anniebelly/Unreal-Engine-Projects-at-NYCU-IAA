# CM_3DGS_PP: swaps the depth blur (CustomBlur) for a dark outline, and the depth mosaic (CustomBrick) for the
# same outline, so the whole frame gets outlines and no mosaic. The graph wiring is untouched; only the two
# Custom nodes' HLSL changes. First run saves the original as CM_3DGS_PP_backup.
# MONET = True adds Impressionist colour on top. Re-runnable; tunables below.
# RESTORE = True puts the original blur + mosaic code back.
import unreal

THICKNESS = 1.5          # line width in pixels
DEPTH_THRESHOLD = 0.03   # relative depth jump that starts a line (smaller = more lines)
COLOR_THRESHOLD = 0.25   # brightness jump that starts a line, for edges the depth misses (bigger = fewer)
LINE_COLOR = (0.02, 0.02, 0.02)
RESTORE = False

# Monet-style colour (Impressionist): soft painted dabs, lifted violet-blue shadows, warm sunlit highlights,
# pastel saturation, and outlines tinted from the paint instead of black.
MONET = True
PAINT_RADIUS = 3         # brush-dab samples per side (Kuwahara filter radius; 0 = off)
PAINT_SCALE = 0.4        # brush-dab size multiplier (smaller = finer patches)
BRIGHTNESS = 1.1         # overall brightness (1.1 = +10 %)
LIGHT_TINT = (1.0, 0.93, 0.76)      # warm sunlight in the highlights
SATURATION = 1.4
CONTRAST = 1.36          # light/dark separation (1 = unchanged)
PIVOT = 0.3              # brightness that contrast pivots around
BANDS = 6                # tonal steps for clear 濃淡 (0 = smooth)
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
float3 m[4] = {{ float3(0,0,0), float3(0,0,0), float3(0,0,0), float3(0,0,0) }};
float3 s[4] = {{ float3(0,0,0), float3(0,0,0), float3(0,0,0), float3(0,0,0) }};
const float2 ox[4] = {{ float2(-1,-1), float2(1,-1), float2(-1,1), float2(1,1) }};
float n = (R + 1) * (R + 1);
for (int k = 0; k < 4; k++)
{{
    for (int i = 0; i <= R; i++)
    {{
        for (int j = 0; j <= R; j++)
        {{
            float3 t = SceneTextureLookup(ScreenUV + float2(i, j) * {ps} * ox[k] * View.BufferSizeAndInvSize.zw, TexIndex, false).rgb;
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
    if (vs < best) {{ best = vs; c.rgb = mu; }}
}}
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
    c.rgb = lerp(c.rgb, c.rgb * (1.0 + {rb_}) * {rt} + {rt} * 0.06 * {rb_}, road);
}}
LineColor = {lc};
c.rgb = lerp(c.rgb, LineColor, smoothstep({dhi}, {dlo}, lum) * (1.0 - road));
edge *= {ls};
"""


def build_code():
    if not MONET:
        return OUTLINE
    code = OUTLINE.replace("const float3 LineColor", "float3 LineColor")
    paint = MONET_PAINT.format(r=int(PAINT_RADIUS), ps=PAINT_SCALE) if PAINT_RADIUS > 0 else ""
    grade = MONET_GRADE.format(pivot=PIVOT, contrast=CONTRAST, bands=int(BANDS), sat=SATURATION,
                               lt=f3(LIGHT_TINT), pastel=PASTEL, lc=f3(MONET_LINE_COLOR),
                               dlo=DARK_LO, dhi=DARK_HI, ls=LINE_STRENGTH, hb=HIGHLIGHT_BOOST, br=BRIGHTNESS,
                               road=int(ROAD), ra=f3(ROAD_A), rb=f3(ROAD_B), rw=ROAD_HALF_WIDTH, rs=ROAD_SOFT,
                               rh=ROAD_HEIGHT, rb_=ROAD_BOOST, rt=f3(ROAD_TINT))
    # Edges are found on the photo; the paint dabs and grade then go on before the lines are drawn.
    return code.replace("c.rgb = lerp(c.rgb, LineColor, edge);", paint + grade + "c.rgb = lerp(c.rgb, LineColor, edge);")


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


def ensure_world_pin(material, node):
    # The road needs each pixel's world position: a WorldPos input on the Custom node, fed by Absolute World Position.
    pins = list(node.get_editor_property("inputs"))
    if any(str(p.get_editor_property("input_name")) == "WorldPos" for p in pins):
        return
    pin = unreal.CustomInput()
    pin.set_editor_property("input_name", "WorldPos")
    pins.append(pin)
    node.set_editor_property("inputs", pins)
    wp = mel.create_material_expression(material, unreal.MaterialExpressionWorldPosition,
                                        node.get_editor_property("material_expression_editor_x") - 300,
                                        node.get_editor_property("material_expression_editor_y") + 200)
    mel.connect_material_expressions(wp, "", node, "WorldPos")
    log("added WorldPos input")


nodes = custom_nodes(mat)
backup_nodes = custom_nodes(unreal.load_asset(BACKUP)) if RESTORE else {}
for name in ("CustomBlur", "CustomBrick"):
    n = nodes.get(name)
    if n is None:
        log(name + " not found in graph")
        continue
    code = backup_nodes[name].get_editor_property("code") if RESTORE else build_code()
    n.modify()
    if not RESTORE and MONET and ROAD:
        ensure_world_pin(mat, n)
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

if world.get_name() == LEVEL:
    unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, "ZhuMingHall_monet.png" if MONET else "ZhuMingHall_outline.png")
