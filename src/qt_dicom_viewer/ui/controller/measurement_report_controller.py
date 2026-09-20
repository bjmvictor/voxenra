"""Capture immutable result rows on the UI thread, write reports in a worker."""
from qt_dicom_viewer.i18n.messages import error_message
from qt_dicom_viewer.i18n import message as _msg
from qt_dicom_viewer.i18n.messages import snapshot
from qt_dicom_viewer.i18n.qt import translated_property as _TextProperty
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot, QPointF, QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QPolygonF

from qt_dicom_viewer.core.measurement_report import csv_bytes, pdf_bytes
from qt_dicom_viewer.ui.controller.settings_controller import resolve_settings
from qt_dicom_viewer.core.workspace_state import atomic_write
from qt_dicom_viewer.model.measure import LengthMeasurement, AngleMeasurement, RoiMeasurement
from qt_dicom_viewer.ui.file_location import reveal_path
from qt_dicom_viewer.i18n.widgets import QFileDialog

KINDS = {"curve": _msg("measurement.curve"), "freehand": _msg("measurement.freehand"), "length": _msg('text.0321'), "angle": _msg('text.0322'), "rect": _msg('text.0375'), "ellipse": _msg('text.0376'),
         "arrow": _msg('text.0377'), "text": _msg('text.0378'), "voi": "VOI", "segmentation": _msg('text.0379')}


def capture_results(workspace, catalog, *, all_tabs=False, anonymous=True, include_images=False):
    tabs = ((workspace.all_tabs() if hasattr(workspace, "all_tabs") else list(workspace._tab_dict.values()))
            if all_tabs else [workspace.activeTab])
    rows, pictures, sources = [], [], set()
    patients, series_names = {}, {}

    def base(uid, view, kind, slice_index=None, frame=None, sop=None):
        series = catalog.get_series(uid)
        if series is None:
            raise ValueError(_msg('text.0380'))
        patient_key = (series.patient_id_issuer, series.patient_id, series.patient_name)
        patient = patients.setdefault(patient_key, _msg('text.0381', value1=len(patients) + 1))
        label = series_names.setdefault(uid, _msg('text.0382', value1=len(series_names) + 1))
        phase = next((i+1 for i, p in enumerate(series.phases)
                      if any(instance.sop_instance_uid == sop for instance in p.instances)), None)
        row = dict(patient=patient if anonymous else series.patient_name,
                   patient_id="" if anonymous else series.patient_id,
                   series=label if anonymous else series.series_description,
                   modality=series.modality, view=view, id=f"M{len(rows)+1:03}",
                   kind=KINDS.get(kind, kind), slice=slice_index+1 if slice_index is not None else None, phase=phase)
        if frame and len(frame) > 5 and len(frame[5]) >= 11:
            row["origin"] = " / ".join(f"{v:.7g}" for v in frame[5][2:5])
            row["orientation"] = " / ".join(f"{v:.7g}" for v in frame[5][5:11])
        return row

    for tab in tabs:
        if tab is None: continue
        for view in tab.viewports_by_id.values():
            measure = getattr(view, "_measure_controller", None)
            if measure is None: continue
            if measure.has_active_transaction or getattr(view._text_annotation_controller, "_draft_id", None):
                raise ValueError(_msg('text.0383'))
            role = {"left": _msg("compare.leftImage"), "right": _msg("compare.rightImage"), "image": "2D", "axial": _msg('text.0384'), "coronal": _msg('text.0385'), "sagittal": _msg('text.0386'),
                    "fusion": _msg('text.0387'), "ct": "CT", "pet": "PET", "mip": "MIP"}.get(view.viewportRole or view.viewport_config.viewport_type.value, view.viewportRole or view.viewport_config.viewport_type.value)
            for mid, item in measure._measurements.items():
                kind = "angle" if isinstance(item, AngleMeasurement) else str(item.kind)
                row = base(item.series_uid, role, kind, item.slice_index,
                           measure._measurement_frames.get(mid), item.sop_instance_uid)
                if isinstance(item, LengthMeasurement) and kind in ("length", "curve"):
                    row["length_mm"] = item.length_mm
                elif isinstance(item, AngleMeasurement): row["angle_deg"] = item.angle
                elif isinstance(item, RoiMeasurement):
                    for key in ("width_mm", "height_mm", "area_mm2", "perimeter_mm", "pixel_count", "mean", "std", "minimum", "maximum", "unit"):
                        row[key] = getattr(item.metrics, key)
                rows.append(row)
            for item in view._text_annotation_controller._annotations.values():
                row = base(view.viewport_config.series_uid, role, "text", item.slice_index, item.frame_key)
                row["text"] = "" if anonymous else item.text
                rows.append(row)
            if include_images and measure.visible_measurements:
                if view._load_state != "ready" or view._frame_meta.slice_index != view._state.slice_index:
                    raise ValueError(_msg('text.0388'))
                image = getattr(workspace, 'registry', workspace)._image_provider._images.get(view.viewportId)
                if image is None or image.isNull(): continue
                annotations = list(measure.visible_measurements)
                caption = base(view.viewport_config.series_uid, role, "", view._frame_meta.slice_index)
                pictures.append((_msg('text.0389', value1=caption['patient'], value2=caption['series'], value3=role, value4=caption['slice']), image.copy(), annotations))
                series = catalog.get_series(view.viewport_config.series_uid)
                sources.update(i.path for group in (series, *series.phases) for i in group.instances)
        voi = getattr(tab, "_voi_controller", None)
        if voi is not None:
            if voi.busy or voi._draft:
                raise ValueError(_msg('text.0390'))
            for item in voi.records:
                result = voi.evaluations.get(item["id"])
                if result is None: raise ValueError(_msg('text.0391'))
                row = base(item["series"], _msg('text.0392'), item["kind"])
                row.update(unit=item["unitLabel"], threshold=result.threshold,
                           volume_cm3=result.metrics["volume"], pixel_count=result.metrics["count"],
                           mean=result.metrics["mean"], std=result.metrics["sd"],
                           minimum=result.metrics["minimum"], maximum=result.metrics["maximum"])
                rows.append(row)
    if not rows: raise ValueError(_msg('text.0393'))
    return rows, pictures, sources


def report_images(pictures):
    output = []
    for caption, source, measurements in pictures:
        image = source.convertToFormat(QImage.Format_RGB32)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#ffe161"), max(1.0, image.width()/450))
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        for item in measurements:
            geometry = item.points
            if getattr(item, "kind", None) == "curve":
                from qt_dicom_viewer.core.curve_geometry import sample_curve
                geometry = sample_curve(geometry)
            points = [QPointF(p.column, p.row) for p in geometry]
            if isinstance(item, RoiMeasurement):
                if str(item.kind) == "freehand":
                    painter.drawPolygon(QPolygonF(points))
                    continue
                rect = QRectF(points[0], points[1]).normalized()
                painter.drawEllipse(rect) if str(item.kind) == "ellipse" else painter.drawRect(rect)
            else:
                for a, b in zip(points, points[1:]): painter.drawLine(a, b)
        painter.end()
        output.append((caption, image))
    return output


class MeasurementReportController(QObject):
    _i18n_message = Signal()
    changed = Signal()
    completed = Signal(object, bool, str)

    def __init__(self, workspace, catalog, parent=None):
        super().__init__(parent)
        self.workspace, self.catalog = workspace, catalog
        self._settings_controller = resolve_settings(parent)
        self._busy = self._error = self._closed = False
        self._message = ""
        self._result_path = ""
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="measurement-report")
        self.completed.connect(self._finish)

    @Property(bool, notify=changed)
    def busy(self): return self._busy

    @Property(bool, notify=changed)
    def isError(self): return self._error

    @_TextProperty(str, notify=_i18n_message, notify_name='_i18n_message', source_notify='changed')
    def message(self): return self._message

    @Property(str, notify=changed)
    def resultPath(self): return self._result_path

    @Slot(result=bool)
    def openResultLocation(self):
        if reveal_path(self._result_path):
            return True
        self._message, self._error = _msg('text.0394'), True
        self.changed.emit()
        return False

    @Slot(str, bool, bool, bool)
    def exportReport(self, format, all_tabs=False, anonymous=True, include_images=False):
        if self._busy: return
        suffix = "pdf" if format == "pdf" else "csv"
        path, _ = QFileDialog.getSaveFileName(None, _msg('text.0395'), _msg('text.0396', value1=suffix), f"{suffix.upper()} (*.{suffix})")
        if path:
            if not path.lower().endswith("."+suffix): path += "."+suffix
            self.export_to(path, format=suffix, all_tabs=all_tabs, anonymous=anonymous, include_images=include_images)

    def export_to(self, path, *, format="csv", all_tabs=False, anonymous=True, include_images=False):
        if self._busy or self._closed: return False
        try:
            if format not in ("csv", "pdf"): raise ValueError(_msg('text.0397'))
            rows, pictures, sources = capture_results(self.workspace, self.catalog, all_tabs=all_tabs,
                anonymous=anonymous, include_images=include_images and format == "pdf")
        except ValueError as error:
            self._finish(error_message(error), True)
            return False
        translations = snapshot()
        decimal_places = self._settings_controller.section("measurement")["decimalPlaces"]
        self._busy, self._error, self._message = True, False, _msg('text.0398')
        self._result_path = ""
        self.changed.emit()
        def write():
            if anonymous and pictures:
                import pydicom
                from qt_dicom_viewer.core.dicom_anonymizer import check_pixel_identity
                for source in sources:
                    check_pixel_identity(pydicom.dcmread(source, stop_before_pixels=True))
            data = csv_bytes(rows, translations=translations, decimal_places=decimal_places) if format == "csv" else pdf_bytes(rows, anonymous=anonymous, images=report_images(pictures), translations=translations, decimal_places=decimal_places)
            atomic_write(path, data)
            return _msg('text.0399', value1=len(rows))
        def done(future):
            try: message, error = future.result(), False
            except Exception as exc: message, error = _msg('text.0400', value1=exc), True
            if not self._closed: self.completed.emit(message, error, str(Path(path).resolve()) if not error else "")
        self._executor.submit(write).add_done_callback(done)
        return True

    @Slot(object, bool, str)
    def _finish(self, message, error, path=""):
        self._busy, self._message, self._error = False, message, error
        self._result_path = path if not error else ""
        self.changed.emit()

    def shutdown(self):
        self._closed = True
        self._executor.shutdown(wait=True, cancel_futures=True)
