"""Two independent 2D stacks with explicit, configurable display linking.

Only commands propagate. Render completions and restored state must never be
interpreted as new gestures (which would create feedback and stale requests).
"""
import uuid
from dataclasses import replace
from functools import wraps

from PySide6.QtCore import Property, Signal, Slot

from qt_dicom_viewer.core.compare import SYNC_OPERATIONS, relative_slice
from qt_dicom_viewer.model import ViewportConfig, TwoDViewType, WindowLevelChange
from qt_dicom_viewer.ui.controller.viewport.image_2d.stack_viewport_controller import StackViewportController
from .tab_controller import TabController


def display_command(method):
    """Report changed display fields once, including compound reset commands."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        outer = self._command_depth == 0
        before = self.display_values() if outer else None
        self._command_depth += 1
        try:
            return method(self, *args, **kwargs)
        finally:
            self._command_depth -= 1
            if outer:
                after = self.display_values()
                changed = [key for key in SYNC_OPERATIONS if before[key] != after[key]]
                if changed:
                    self.displayCommand.emit(changed)
    return wrapped


class CompareStackViewportController(StackViewportController):
    displayCommand = Signal(object)

    def __init__(self, *args, **kwargs):
        self._command_depth = 0
        super().__init__(*args, **kwargs)

    def display_values(self):
        state = self._state
        window = self._pet_display.target.window if self.isPetViewport and self._pet_display.target else state.window
        return dict(scroll=state.slice_index, window=window, pan=(state.pan_x, state.pan_y),
                    zoom=state.zoom, rotate=state.rotation_degrees,
                    flip=(state.horizontal_flip, state.vertical_flip),
                    pseudocolor=state.display_style, invert=state.inverted,
                    viewport=state.display_settings)

    @Property(str, constant=True)
    def compareLabel(self):
        meta = self.viewport_config.series_meta
        return " · ".join(str(value) for value in (meta.modality, meta.series_description,
                              meta.acquisition_datetime) if value)

    # Reuse every standard 2D operation; measurements/annotations are deliberately
    # absent. Qt slots need to remain registered on these overriding methods.
    apply_slice_index = display_command(StackViewportController.apply_slice_index)
    apply_pan = display_command(StackViewportController.apply_pan)
    apply_zoom = display_command(StackViewportController.apply_zoom)
    apply_window_level = display_command(StackViewportController.apply_window_level)
    reset_tool_state = display_command(StackViewportController.reset_tool_state)
    reset_all_view_state = display_command(StackViewportController.reset_all_view_state)
    applyTransformAction = Slot(str)(display_command(StackViewportController.applyTransformAction))
    applyColorMap = Slot(str)(display_command(StackViewportController.applyColorMap))
    setViewportSetting = Slot(str, bool)(display_command(StackViewportController.setViewportSetting))
    setPetDisplayUpper = Slot(float)(display_command(StackViewportController.setPetDisplayUpper))
    setPetControlUpper = Slot(float)(display_command(StackViewportController.setPetControlUpper))
    setPetUnit = Slot(str)(display_command(StackViewportController.setPetUnit))
    resetPetDisplay = Slot()(display_command(StackViewportController.resetPetDisplay))


class CompareTabController(TabController):
    settingsChanged = Signal()
    navigationChanged = Signal()

    def __init__(self, config, parent=None):
        if len(config.series_metas) != 2 or config.series_metas[0].series_uid == config.series_metas[1].series_uid:
            raise ValueError("Compare 2D requires two distinct image series")
        self._sync_operations = dict.fromkeys(SYNC_OPERATIONS, True)
        self._syncing = False
        self._initialized = False
        super().__init__(config, parent)
        self.activeViewportChanged.connect(self.navigationChanged)

    @Slot(str)
    def activateViewport(self, viewport_id):
        if viewport_id not in self._viewport_dict:
            return
        tools = self.toolController
        modality = self._viewport_dict[viewport_id].viewport_config.series_meta.modality.upper()
        if modality != tools._modality:
            from .tool_controller import tool_available
            from qt_dicom_viewer.model import ToolType
            tools._modality = modality
            tools._i18n_tools.emit()
            tools.windowPresetsChanged.emit()
            tools.resetStateChanged.emit()
            if not tool_available(ToolType(tools.activeTool), tools._tab_type, modality):
                tools.activateTool("window")
        super().activateViewport(viewport_id)

    def _create_viewport_dict(self):
        for role, meta in zip(("left", "right"), self.tab_config.series_metas):
            uid = str(uuid.uuid4())
            view = CompareStackViewportController(ViewportConfig(uid, self.tab_config.tab_id,
                TwoDViewType.STACK, meta.series_uid, meta, role=role), self.toolController, parent=self)
            self._viewport_dict[uid] = view
            self.connect_signal(view)
            view.displayCommand.connect(lambda operations, source=view: self._sync_from(source, operations))
            view.sliceChanged.connect(self.navigationChanged)
        self._active_viewport_id = next(iter(self._viewport_dict))

    @Property('QVariantMap', notify=settingsChanged)
    def syncOperations(self):
        return dict(self._sync_operations)

    @Property(str, constant=True)
    def viewportType(self):
        return "stack"

    def _slider_view(self):
        if not self._sync_operations["scroll"]:
            return self.activeViewport
        left, right = self._viewport_dict.values()
        return right if left.sliceCount <= 1 < right.sliceCount else left

    @Property(int, notify=navigationChanged)
    def sliceCount(self):
        return self._slider_view().sliceCount

    @Property(int, notify=navigationChanged)
    def sliceIndex(self):
        return max(0, self._slider_view().sliceIndex)

    @Slot(int)
    def setSliceIndex(self, index):
        self._slider_view().setSliceIndex(index)

    @Slot(str, bool)
    def setSyncOperation(self, operation, enabled):
        if operation not in self._sync_operations or self._sync_operations[operation] == enabled:
            return
        self._sync_operations[operation] = enabled
        if enabled:
            self._sync_from(self.activeViewport, [operation])
        self.settingsChanged.emit()
        self.navigationChanged.emit()

    def restore_sync(self, values):
        self._sync_operations = {key: values.get(key, True) for key in SYNC_OPERATIONS}
        self.settingsChanged.emit()
        self.navigationChanged.emit()

    def handleRenderResult(self, result):
        super().handleRenderResult(result)
        if not self._initialized and all(view._frame_meta is not None for view in self._viewport_dict.values()):
            self._initialized = True
            self._sync_from(next(iter(self._viewport_dict.values())), ["window", "pseudocolor", "invert"])

    def _sync_from(self, source, operations):
        if self._syncing:
            return
        operations = [key for key in operations if self._sync_operations.get(key)]
        if not operations:
            return
        self._syncing = True
        try:
            values = source.display_values()
            for target in self._viewport_dict.values():
                if target is source:
                    continue
                if "scroll" in operations and source.sliceCount and target.sliceCount:
                    target.setSliceIndex(relative_slice(source.sliceIndex, source.sliceCount, target.sliceCount))
                if "pan" in operations:
                    # Pan is in viewport pixels. Normalize for unequal cell sizes.
                    target.apply_pan(values["pan"][0] * target._state.width / max(source._state.width, 1),
                                     values["pan"][1] * target._state.height / max(source._state.height, 1))
                if "zoom" in operations:
                    target.apply_zoom(values["zoom"])
                transforms = {}
                if "rotate" in operations:
                    transforms["rotation_degrees"] = values["rotate"]
                if "flip" in operations:
                    transforms.update(horizontal_flip=values["flip"][0], vertical_flip=values["flip"][1])
                if transforms:
                    target._state = replace(target._state, **transforms)
                    target.transformChanged.emit()
                    target.directionLabelsChanged.emit()
                    target.overlayChanged.emit()
                if "viewport" in operations:
                    target._state = replace(target._state, display_settings=values["viewport"])
                    target.viewportSettingsChanged.emit()
                if "pseudocolor" in operations:
                    target.applyColorMap(values["pseudocolor"].color_map)
                if "window" in operations or "invert" in operations:
                    window = values["window"] if "window" in operations else target.display_values()["window"]
                    inverted = values["invert"] if "invert" in operations else target.inverted
                    if window is not None:
                        target.apply_window_level(WindowLevelChange(window, inverted))
            self.navigationChanged.emit()
        finally:
            self._syncing = False
