"""Explicit adapters between live controllers and portable value snapshots."""
from qt_dicom_viewer.i18n import message as _msg
from dataclasses import replace

import numpy as np

from qt_dicom_viewer.model import TabType
from qt_dicom_viewer.model.measure import RoiMeasurement


def view_key(view):
    config = view.viewport_config
    return f"{config.series_uid}|{config.viewport_type.value}|{config.role}"


def editable_state(tab):
    result = {"views": {}}
    for view in tab.viewports_by_id.values():
        state = {}
        measure = getattr(view, "_measure_controller", None)
        if measure is not None:
            state["measurements"] = dict(measure._measurements)
            state["frames"] = dict(measure._measurement_frames)
        annotations = getattr(view, "_text_annotation_controller", None)
        if annotations is not None:
            state["annotations"] = {k: v for k, v in annotations._annotations.items()
                                    if k != annotations._draft_id}
        if hasattr(view, "crop_mask"):
            state["crop"] = view.crop_mask
            state["bed"] = view._bed_mask
            state["bedEnabled"] = view._bed_enabled
        result["views"][view_key(view)] = state
    voi = getattr(tab, "_voi_controller", None)
    if voi is not None:
        result["voi"] = [{k: v for k, v in r.items() if k != "valueRange"}
                         for r in voi.records]
    if hasattr(tab, "matrix"):
        result["registration"] = {"matrix": tab.matrix.copy(), "pivot": tab.pivot.copy()}
    return result


def edit_signature(state):
    """Recomputed ROI statistics are not user edits and must not add undo steps."""
    from qt_dicom_viewer.core.workspace_state import dumps
    state = dict(state, views={k: dict(v) for k, v in state["views"].items()})
    for view in state["views"].values():
        if "measurements" in view:
            view["measurements"] = {k: replace(m, metrics=type(m.metrics)())
                                    if isinstance(m, RoiMeasurement) else m
                                    for k, m in view["measurements"].items()}
    return dumps(state)


def apply_edits(tab, state):
    for view in tab.viewports_by_id.values():
        record = state.get("views", {}).get(view_key(view), {})
        measure = getattr(view, "_measure_controller", None)
        if measure is not None:
            measure.cancel_transaction()
            measure.clear_selection()
            measure._measurements = dict(record.get("measurements", {}))
            measure._measurement_frames = dict(record.get("frames", {}))
            measure.measurementsChanged.emit()
            measure.refresh_roi_metrics(getattr(view, "_modality_pixel", None),
                                        getattr(view, "_frame_meta", None))
        annotations = getattr(view, "_text_annotation_controller", None)
        if annotations is not None:
            annotations.cancelDraft()
            annotations.clearSelection()
            annotations._annotations = dict(record.get("annotations", {}))
            annotations.annotationsChanged.emit()
        if hasattr(view, "crop_mask"):
            for name in ("crop", "bed"):
                mask = record.get(name)
                if mask is not None and (view.volume is None or mask.shape != view.volume.modality_pixels.shape):
                    raise ValueError(_msg('text.0020'))
            view._cancel_edit()
            view._clear_crop_selection()
            view.crop_mask, view._bed_mask = record.get("crop"), record.get("bed")
            view._bed_enabled = bool(record.get("bedEnabled", False))
            view._update_mask()
    voi = getattr(tab, "_voi_controller", None)
    if voi is not None:
        voi.cancel()
        voi.records = [dict(record) for record in state.get("voi", [])]
        voi._selected = ""
        voi.evaluations.clear()
        voi.itemsChanged.emit()
        voi._schedule()
    if "registration" in state and hasattr(tab, "matrix"):
        record = state["registration"]
        matrix, pivot = record["matrix"], record["pivot"]
        if matrix.shape != (4, 4) or pivot.shape != (3,) or not np.isfinite(matrix).all():
            raise ValueError(_msg('text.0021'))
        changed = not np.array_equal(tab.matrix, matrix) or not np.array_equal(tab.pivot, pivot)
        tab.matrix, tab.pivot = matrix.copy(), pivot.copy()
        tab._registration_changed = not np.allclose(matrix, np.eye(4))
        if changed:
            tab.settingsChanged.emit()
            tab.request_render()


def tab_snapshot(tab):
    config = tab.tab_config
    record = {"type": config.tab_type.value, "label": config.tab_label,
              "series": [m.series_uid for m in config.series_metas]}
    if config.tab_type in (TabType.SETTINGS, TabType.PACS, TabType.MANUAL, TabType.TAG):
        return record
    record.update(edits=editable_state(tab), views={}, activeView=view_key(tab.activeViewport),
                  focusedView=view_key(tab.viewports_by_id[tab.focusedViewportId]) if tab.focusedViewportId else "",
                  mpr=tab._target_mpr_state, projection=tab.toolController.mpr_projection_settings,
                  linkedWindow=tab._linked_mpr_window, phase=tab._current_phase_index,
                  fps=tab._fps, tool=str(tab.toolController.activeTool))
    if tab.mprLayout is not None:
        record["mprLayout"] = tab.mprLayout.snapshot()
    for view in tab.viewports_by_id.values():
        state = {}
        if hasattr(view, "_state"):
            state["image"] = view._state
        if hasattr(view, "state"):
            state.update(volume=view.state, display=view.display_state)
        if getattr(view, "scene", None) is not None:
            scene = view.scene
            request = scene.request
            record["fusionSource"] = dict(mpr=scene.state, ctWindow=scene.ct_window,
                petMeta=scene.pet_volume.pixel_value_meta, petUpper=scene.pet_window.width,
                matrix=np.asarray(request.transform).reshape(4, 4),
                plane=request.plane, ctInverted=request.ct_inverted,
                opacity=request.opacity, petColor=request.pet_color_map, fusionColor=request.fusion_color_map)
        for key in ("_column_count", "_details_expanded", "_unit", "_upper",
                    "_threshold_fraction", "_opacity", "_palette", "_mode",
                    "_ct_opacity", "_pet_opacity", "_ct_preset"):
            if hasattr(view, key):
                state[key] = getattr(view, key)
        display = getattr(view, "_pet_display", None)
        if display is not None:
            state["petDisplay"] = display.target
        record["views"][view_key(view)] = state
    if config.tab_type == TabType.COMPARE_2D:
        record["compareSync"] = tab.syncOperations
    if hasattr(tab, "pet_display"):
        record["pet"] = {key: getattr(tab, key) for key in (
            "_plane", "_ct_window", "_ct_inverted", "_opacity", "_pet_color", "_fusion_color",
            "_compact_crosshair", "_compact_overlay")}
        record["pet"]["display"] = tab.pet_display.target
    return record


def apply_tab_snapshot(tab, record):
    """Apply after initial loading, then render through the existing scheduler."""
    if "views" not in record:
        return
    from qt_dicom_viewer.ui.controller.viewport.image_2d.montage_viewport_controller import MontageViewportController
    tab.pausePlayback()
    tab._current_phase_index = max(0, min(record.get("phase", 0), max(0, tab.phaseCount - 1)))
    tab._fps = max(1, min(15, record.get("fps", 2)))
    tab.phaseChanged.emit()
    tab.fpsChanged.emit()
    tab._target_mpr_state = record.get("mpr")
    tab._mpr_3d_reset_state = tab._target_mpr_state
    tab.toolController._mpr_projection_settings = record["projection"]
    tab.toolController.mprProjectionChanged.emit()
    if "pet" in record:
        pet = record["pet"]
        for key in ("_plane", "_ct_window", "_ct_inverted", "_opacity", "_pet_color", "_fusion_color",
                    "_compact_crosshair", "_compact_overlay"):
            setattr(tab, key, pet[key])
        tab.pet_display.target = pet["display"]
        tab.settingsChanged.emit()
    # Choose the grid before restoring a maximized viewport. The user-facing
    # layout command exits maximization, so calling it last would erase focus.
    if tab.mprLayout is not None:
        tab.mprLayout.restore(record.get("mprLayout", {}))
    for view in tab.viewports_by_id.values():
        state = record["views"].get(view_key(view))
        if state is None:
            continue
        if "image" in state:
            saved = state["image"]
            view._state = replace(saved, width=view._state.width, height=view._state.height,
                                  slice_count=view._state.slice_count)
            view.transformChanged.emit()
            if hasattr(view, "windowLevelChanged"):
                view.windowLevelChanged.emit()
        if "volume" in state:
            view._set_state(state["volume"])
            view._set_display_state(state["display"])
        for key in ("_column_count", "_details_expanded", "_unit", "_upper",
                    "_threshold_fraction", "_opacity", "_palette", "_mode",
                    "_ct_opacity", "_pet_opacity", "_ct_preset"):
            if key in state and hasattr(view, key):
                setattr(view, key, state[key])
        if "petDisplay" in state:
            view._pet_display.target = state["petDisplay"]
        if hasattr(view, "restore_pet_display"):
            view.restore_pet_display(state)
        if isinstance(view, MontageViewportController):
            view.columnCountChanged.emit()
            view.detailsExpandedChanged.emit()
        if view_key(view) == record.get("activeView"):
            tab.activateViewport(view.viewportId)
        if view_key(view) == record.get("focusedView"):
            tab.focusSingleViewport(view.viewportId)
    # Restore geometry before submitting new renders; frame-bound metrics will
    # refresh only after their matching plane has been accepted.
    apply_edits(tab, record["edits"])
    if record.get("linkedWindow") is not None:
        tab._set_mpr_window(record["linkedWindow"], render=False)
    if hasattr(tab, "pet_display"):
        tab.request_render()
    elif tab._target_mpr_state is not None:
        tab._dirty_mpr_viewport_ids.update(tab._mpr_viewport_ids())
        tab._try_start_next_mpr_render()
    else:
        for view in tab.viewports_by_id.values():
            if not hasattr(view, "volume"):
                view.request_render()
    if tab.tab_config.tab_type == TabType.COMPARE_2D:
        tab.restore_sync(record.get("compareSync", {}))
    if record.get("tool"):
        tab.toolController.activateTool(record["tool"])
    if tab.mprLayout is not None:
        tab.mprLayout.sync_state()


def apply_fusion_source(tab, state):
    """Rebuild a detached 3D scene through the normal PET worker, without pixels in the file."""
    tab._target_mpr_state, tab._plane = state["mpr"], state["plane"]
    tab._ct_window, tab._ct_inverted = state["ctWindow"], state["ctInverted"]
    tab._opacity, tab._pet_color, tab._fusion_color = state["opacity"], state["petColor"], state["fusionColor"]
    tab.matrix = state["matrix"].copy()
    tab.pet_display.target = replace(tab.pet_display.target, meta=state["petMeta"],
        upper=state["petUpper"], control=max(tab.pet_display.target.control, state["petUpper"]))
    tab.request_render()
