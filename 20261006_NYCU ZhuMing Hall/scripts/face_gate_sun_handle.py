# Stands the viewport on the ground facing the fence and gate, puts the SunHandle where it can be seen in that view
# (a directional light's position doesn't change the light), and selects it so its gizmo is ready.
import math
import unreal

FEET = unreal.Vector(256.31994059888535, -72.11163603319427, -20.0)
YAW = 40.0
EYE_HEIGHT = 160.0
BACK = 330.0              # cm behind the standing spot, same as the start view
HANDLE_AHEAD = 700.0      # cm in front of the eye
HANDLE_UP = 220.0         # cm above the eye

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
fx, fy = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
eye = unreal.Vector(FEET.x - fx * BACK, FEET.y - fy * BACK, FEET.z + EYE_HEIGHT)
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
    eye, unreal.Rotator(roll=0.0, pitch=-3.0, yaw=YAW))

sun = next(a for a in actor_sub.get_all_level_actors() if a.get_actor_label() == "SunHandle")
sun.modify()
sun.set_actor_location(unreal.Vector(eye.x + fx * HANDLE_AHEAD, eye.y + fy * HANDLE_AHEAD, eye.z + HANDLE_UP), False, False)
actor_sub.set_selected_level_actors([sun])
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[VIEW] eye {} handle {}".format(eye, sun.get_actor_location()))
