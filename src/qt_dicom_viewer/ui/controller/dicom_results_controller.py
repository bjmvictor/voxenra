"""Snapshot current-tab measurements and masks, then export off the GUI thread."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Event
import numpy as np

from PySide6.QtCore import QObject, Property, Signal, Slot
from qt_dicom_viewer.core.dicom_results import (
    PlanarResult,
    SegmentResult,
    write_results,
)
from qt_dicom_viewer.i18n import message as _msg
from qt_dicom_viewer.i18n.messages import error_message
from qt_dicom_viewer.i18n.qt import translated_property as _TextProperty
from qt_dicom_viewer.i18n.widgets import QFileDialog
from qt_dicom_viewer.ui.file_location import reveal_path


def _instances(catalog, uid, phase=None, sop=None):
    series = catalog.get_series(uid)
    if series is None:
        raise ValueError(_msg("results.invalidSource"))
    if phase is not None:
        selected = series.phase_by_identifier(phase)
        if selected is None:
            raise ValueError(_msg("results.changedSource"))
        return tuple(selected.instances)
    if sop:
        phases = [
            p
            for p in series.phases
            if any(i.sop_instance_uid == sop for i in p.instances)
        ]
        if len(phases) == 1:
            return tuple(phases[0].instances)
    return tuple(series.instances)


def capture_dicom_results(workspace, catalog, *, report=True):
    tab = workspace.activeTab
    if tab is None:
        raise ValueError(_msg("results.noResults"))
    planar, segments = [], []
    if report:
        for view in tab.viewports_by_id.values():
            measure = getattr(view, "_measure_controller", None)
            if measure is None:
                continue
            if measure.has_active_transaction:
                raise ValueError(_msg("text.0383"))
            measurements = [
                item
                for item in measure.committed_measurements
                if str(getattr(item, "kind", "")) != "arrow"
            ]
            owner = getattr(view, "owner", None)
            if (
                measurements
                and getattr(owner, "isFusion", False)
                and getattr(view, "viewportRole", "") in ("pet", "fusion")
                and not np.allclose(owner.matrix, np.eye(4))
            ):
                raise ValueError(_msg("results.geometryMismatch"))
            settings = getattr(
                getattr(view, "_tool_controller", None), "mpr_projection_settings", None
            )
            if measurements and (
                (settings is not None and settings.enabled)
                or getattr(view, "viewportRole", "") == "mip"
            ):
                raise ValueError(_msg("results.projectedMeasurement"))
            for item in measurements:
                planar.append(
                    PlanarResult(
                        item,
                        measure._measurement_frames.get(item.measurement_id),
                        _instances(catalog, item.series_uid, sop=item.sop_instance_uid),
                        is_mpr=getattr(view, "_plane_geometry", None) is not None,
                    )
                )
    voi = getattr(tab, "_voi_controller", None)
    if voi is not None:
        records = [
            r for r in voi.current_records if report or r["kind"] == "segmentation"
        ]
        if records and (voi.busy or voi._draft):
            raise ValueError(_msg("text.0390"))
        for record in records:
            evaluation = voi.evaluations.get(record["id"])
            if evaluation is None:
                raise ValueError(_msg("text.0391"))
            # Background export owns its mask snapshot, independent of edits,
            # phase changes, closure and deletion in the live workspace.
            frozen = replace(
                evaluation,
                mask=evaluation.mask.copy(),
                offset=evaluation.offset.copy(),
                metrics=dict(evaluation.metrics),
            )
            segments.append(
                SegmentResult(
                    dict(record),
                    frozen,
                    _instances(catalog, record["series"], record.get("phase")),
                )
            )
    if not planar and not segments:
        raise ValueError(_msg("results.noResults"))
    return tuple(planar), tuple(segments)


class DicomResultsController(QObject):
    changed = Signal()
    _i18n_message = Signal()
    completed = Signal(object, bool, str)

    def __init__(self, workspace, catalog, parent=None):
        super().__init__(parent)
        self.workspace, self.catalog = workspace, catalog
        self._busy = self._error = self._closed = False
        self._message = self._result_path = ""
        self._cancel = Event()
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="dicom-results"
        )
        self.completed.connect(self._finish)

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(bool, notify=changed)
    def isError(self):
        return self._error

    @_TextProperty(
        str, notify=_i18n_message, notify_name="_i18n_message", source_notify="changed"
    )
    def message(self):
        return self._message

    @Property(str, notify=changed)
    def resultPath(self):
        return self._result_path

    @Slot(result=bool)
    def openResultLocation(self):
        return reveal_path(self._result_path)

    @Slot()
    def cancel(self):
        self._cancel.set()

    @Slot(str)
    def exportResults(self, kind):
        if self._busy or self._closed:
            return
        # Validate before showing a destination chooser.
        try:
            capture_dicom_results(self.workspace, self.catalog, report=kind == "sr")
        except ValueError as error:
            self._finish(error_message(error), True, "")
            return
        path = QFileDialog.getExistingDirectory(None, _msg("results.chooseDirectory"))
        if path:
            self.export_to(path, kind=kind)

    def export_to(self, path, *, kind="sr"):
        if self._busy or self._closed:
            return False
        try:
            if kind not in ("seg", "sr"):
                raise ValueError(_msg("text.0397"))
            planar, segments = capture_dicom_results(
                self.workspace, self.catalog, report=kind == "sr"
            )
        except ValueError as error:
            self._finish(error_message(error), True, "")
            return False
        self._cancel.clear()
        self._busy, self._error, self._message, self._result_path = (
            True,
            False,
            _msg("results.writing"),
            "",
        )
        self.changed.emit()

        def write():
            return write_results(
                path,
                planar,
                segments,
                report=kind == "sr",
                cancelled=self._cancel.is_set,
            )

        def done(future):
            try:
                output, count = future.result()
                message, error, path = (
                    _msg("results.written", count=count),
                    False,
                    str(output.resolve()),
                )
            except InterruptedError:
                message, error, path = _msg("results.cancelled"), False, ""
            except Exception as exc:
                message, error, path = (
                    _msg("results.failed", reason=error_message(exc)),
                    True,
                    "",
                )
            if not self._closed:
                self.completed.emit(message, error, path)

        self._executor.submit(write).add_done_callback(done)
        return True

    @Slot(object, bool, str)
    def _finish(self, message, error, path):
        self._busy, self._message, self._error, self._result_path = (
            False,
            message,
            error,
            path,
        )
        self.changed.emit()

    def shutdown(self):
        self._closed = True
        self._cancel.set()
        self._executor.shutdown(wait=True, cancel_futures=True)
