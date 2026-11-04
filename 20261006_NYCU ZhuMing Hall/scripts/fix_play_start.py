# Play setup for Lvl_ZhuMingHall. The scan has no collision, so the player walks on the hidden Floor, which sat about a
# metre above the scanned ground. This tilts the Floor onto the best-fit plane of the ground around the start, stands
# the PlayerStart on it at the building side facing the gate and the big trees, and clears invisible obstacles.
import math
import unreal

START = (103.0, -200.0)   # x, y (cm): in the courtyard, on the building side
YAW = 40.0                # faces the gate and the big trees, same as the start view
FIT_RADIUS = 1400.0       # cm of ground around the start the Floor is fitted to
FLOOR_SIZE = 12000.0      # cm; the Floor is scaled to at least this wide
FEET_TO_START = 100.0     # cm from the ground to the PlayerStart's centre
GROUND_FIT = (174.82, -72.22, -49.3, 11.34, 14.51, 5.02, -1.05, -1.46, -3.94, -1.19)   # as in outline_3dgs_pp.py
NO_COLLISION = ("Cube", "MatPreviewMesh")


def log(msg):
    unreal.log("[PLAY] " + msg)


actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = {a.get_actor_label(): a for a in actor_sub.get_all_level_actors()}
off = next(a for a in actors.values() if a.get_class().get_name() == "GaussianSplatActor").get_actor_location()


def ground(x, y):
    # world x, y (cm) -> world height of the scanned ground
    u = min(max((x - off.x) / 1000.0, -2.5), 3.8)
    v = min(max((y - off.y) / 1000.0, -2.5), 3.8)
    g = GROUND_FIT
    return off.z + (g[0] + g[1] * u + g[2] * v + g[3] * u * u + g[4] * u * v + g[5] * v * v
                    + g[6] * u ** 3 + g[7] * u * u * v + g[8] * u * v * v + g[9] * v ** 3)


# Plane z = z0 + a * dx + b * dy through a grid of ground samples around the start.
sx, sy = START
pts = [(i * 100.0, j * 100.0) for i in range(-14, 15) for j in range(-14, 15) if math.hypot(i, j) * 100.0 <= FIT_RADIUS]
zs = [ground(sx + dx, sy + dy) for dx, dy in pts]
n = len(pts)
z0 = sum(zs) / n
a = sum(dx * z for (dx, _), z in zip(pts, zs)) / sum(dx * dx for dx, _ in pts)
b = sum(dy * z for (_, dy), z in zip(pts, zs)) / sum(dy * dy for _, dy in pts)
worst = max(abs(z - (z0 + a * dx + b * dy)) for (dx, dy), z in zip(pts, zs))
log("ground at start {:.1f}, slope {:.4f} {:.4f}, largest gap to the scan {:.1f} cm".format(z0, a, b, worst))

floor = actors["Floor"]
floor.modify()
floor.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0), False)
origin, ext = floor.get_actor_bounds(False)
if ext.x * 2.0 < FLOOR_SIZE:
    s = floor.get_actor_scale3d()
    k = FLOOR_SIZE / (ext.x * 2.0)
    floor.set_actor_scale3d(unreal.Vector(s.x * k, s.y * k, s.z))
    origin, ext = floor.get_actor_bounds(False)
top = origin.z + ext.z - floor.get_actor_location().z
length = math.sqrt(a * a + b * b + 1.0)
normal = unreal.Vector(-a / length, -b / length, 1.0 / length)
floor.set_actor_rotation(unreal.MathLibrary.make_rot_from_zx(normal, unreal.Vector(1.0, 0.0, a)), False)
floor.set_actor_location(unreal.Vector(sx - normal.x * top, sy - normal.y * top, z0 - normal.z * top), False, False)

start = actors["PlayerStart"]
start.modify()
start.set_actor_location(unreal.Vector(sx, sy, z0 + FEET_TO_START), False, False)
start.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW), False)

for label in NO_COLLISION:
    if label in actors:
        actors[label].modify()
        actors[label].set_actor_enable_collision(False)

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
log("floor at {} rotation {} | start at {}".format(floor.get_actor_location(), floor.get_actor_rotation(), start.get_actor_location()))
