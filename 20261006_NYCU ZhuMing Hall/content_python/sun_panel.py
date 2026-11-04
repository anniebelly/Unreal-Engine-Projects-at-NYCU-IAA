# Sun control panel: sliders for the level's SunHandle, shown in the Details panel. Opened from the "太陽把手"
# menu at the top of the editor (added by init_unreal.py). The panel is a temporary actor that never gets saved;
# what it changes is the SunHandle light. Editor only, needs no Blueprint.
import math
import unreal

SUN_LABEL = "SunHandle"
PANEL_LABEL = "太陽把手面板"
BASE_INTENSITY = 3.0        # the light's Intensity at 100 % brightness
NOON_ELEVATION = 78.0       # degrees above the horizon at 12:00
WARM_COLOR = (1.0, 0.62, 0.36)
PRESETS = (("清晨 07:00", 7.0), ("上午 09:30", 9.5), ("正午 12:00", 12.0), ("下午 15:00", 15.0), ("黃昏 17:30", 17.5))


def _slider(name, low, high):
    return dict(DisplayName=name, Category="太陽把手", ClampMin=str(low), ClampMax=str(high), UIMin=str(low), UIMax=str(high))


@unreal.uclass()
class SunPanel(unreal.Actor):
    time_of_day = unreal.uproperty(float, meta=_slider("時間（幾點）", 5, 20))
    direction = unreal.uproperty(float, meta=_slider("太陽方位（度）", -180, 180))
    brightness = unreal.uproperty(float, meta=_slider("亮度（1 = 正常）", 0, 2))
    warmth = unreal.uproperty(float, meta=_slider("暖色（0 = 白光，1 = 橘光）", 0, 1))


_state = {"panel": None, "last": None, "tick": None}


def _find_sun(actors):
    return next((a for a in actors if a.get_actor_label() == SUN_LABEL or isinstance(a, unreal.DirectionalLight)), None)


def _apply_to(sun, values, mark_dirty):
    time_of_day, direction, brightness, warmth = values
    comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    elevation = NOON_ELEVATION * math.sin(math.pi * (time_of_day - 6.0) / 12.0)
    yaw = direction + (time_of_day - 12.0) * 15.0   # the sun crosses 15 degrees an hour
    if mark_dirty:
        sun.modify()
        comp.modify()
    sun.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-elevation, yaw=yaw), False)
    comp.set_intensity(BASE_INTENSITY * brightness)
    r, g, b = (1.0 + (w - 1.0) * warmth for w in WARM_COLOR)
    comp.set_light_color(unreal.LinearColor(r, g, b, 1.0))


def _tick(_dt):
    panel = _state["panel"]
    if panel is None:
        return
    if not unreal.SystemLibrary.is_valid(panel):   # the level was closed
        _state["panel"] = None
        return
    values = (panel.time_of_day, panel.direction, panel.brightness, panel.warmth)
    if values == _state["last"]:
        return
    _state["last"] = values
    sun = _find_sun(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    if sun:
        _apply_to(sun, values, True)
    game = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if game:   # also the running game, while in Play
        for light in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.DirectionalLight):
            _apply_to(light, values, False)


def open_panel(hour=None):
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    panel = _state["panel"]
    if panel is None or not unreal.SystemLibrary.is_valid(panel):
        sun = _find_sun(actor_sub.get_all_level_actors())
        if sun is None:
            unreal.log_warning("[SUN] no sun in this level")
            return
        comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
        panel = actor_sub.spawn_actor_from_class(SunPanel, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0), True)
        panel.set_actor_label(PANEL_LABEL)
        # start from the sun as it stands now, so opening the panel changes nothing
        panel.time_of_day = 12.0
        panel.direction = sun.get_actor_rotation().yaw
        panel.brightness = comp.get_editor_property("intensity") / BASE_INTENSITY
        panel.warmth = 0.0
        _state["panel"] = panel
        _state["last"] = (panel.time_of_day, panel.direction, panel.brightness, panel.warmth)
    if hour is not None:
        panel.time_of_day = hour
    actor_sub.set_selected_level_actors([panel])
    unreal.log("[SUN] panel open")


def install_menu():
    if _state["tick"] is None:
        _state["tick"] = unreal.register_slate_post_tick_callback(_tick)
    menus = unreal.ToolMenus.get()
    main = menus.find_menu("LevelEditor.MainMenu")
    sub = main.add_sub_menu(main.menu_name, "SunPanelSection", "SunPanelMenu", "太陽把手", "調整太陽光")
    entries = [("Open", "打開滑桿面板", "open_panel()")]
    entries += [("Preset{}".format(i), label, "open_panel({})".format(hour)) for i, (label, hour) in enumerate(PRESETS)]
    for name, label, call in entries:
        entry = unreal.ToolMenuEntry(name=name, type=unreal.MultiBlockType.MENU_ENTRY)
        entry.set_label(label)
        entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, "", "import sun_panel; sun_panel." + call)
        sub.add_menu_entry("Main", entry)
    menus.refresh_all_widgets()
    unreal.log("[SUN] menu ready")
