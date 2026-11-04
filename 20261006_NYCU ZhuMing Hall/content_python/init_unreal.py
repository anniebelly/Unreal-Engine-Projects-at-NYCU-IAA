# Runs automatically when the editor opens this project.
# Keeps the Zhu Ming Hall scan at full detail (also set in Config/DefaultEngine.ini [SystemSettings]).
import unreal


def _apply(_dt=0.0):
    unreal.unregister_slate_post_tick_callback(_handle)
    unreal.SystemLibrary.execute_console_command(None, "gs.DebugForceLODLevel 0")
    unreal.log("[init] gs.DebugForceLODLevel 0")
    import sun_panel
    sun_panel.install_menu()


_handle = unreal.register_slate_post_tick_callback(_apply)
