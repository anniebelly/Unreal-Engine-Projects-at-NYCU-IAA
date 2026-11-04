# Stores the final exposure in the level. The look was tuned in a viewport with exposure locked to EV100 1, which is a
# per-user editor setting and doesn't travel with the project, so a fresh copy (and Play) fell back to auto exposure
# and came out much brighter. Manual exposure with a bias of -1 is the same brightness as EV100 1.
import unreal

EXPOSURE_BIAS = -1.0

ppv = next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
           if isinstance(a, unreal.PostProcessVolume))
ppv.modify()
s = ppv.get_editor_property("settings")
s.set_editor_property("override_auto_exposure_method", True)
s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
s.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
s.set_editor_property("override_auto_exposure_bias", True)
s.set_editor_property("auto_exposure_bias", EXPOSURE_BIAS)
ppv.set_editor_property("settings", s)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
s = ppv.get_editor_property("settings")
unreal.log("[EXPOSURE] method {} physical {} bias {} saved".format(s.get_editor_property("auto_exposure_method"),
           s.get_editor_property("auto_exposure_apply_physical_camera_exposure"), s.get_editor_property("auto_exposure_bias")))
