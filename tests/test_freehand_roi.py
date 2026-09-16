from dataclasses import replace
import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from qt_dicom_viewer.core.freehand_roi import simple_polygon
from qt_dicom_viewer.core.measurement_geometry import roi_metrics
from qt_dicom_viewer.core.measurement_hit_test import (
    hit_test_interior,
    hit_test_outline,
)
from qt_dicom_viewer.core.workspace_state import dumps, loads, encode, decode
from qt_dicom_viewer.model import ImagePoint, MeasurementKind
from qt_dicom_viewer.model.measure import RoiMeasurement
from qt_dicom_viewer.ui.controller.viewport.controller.measure.measure_controller import (
    MeasurementController,
)
from test_measurement_controller import _context, _position, _drag
from test_measurement_qml import (
    qt_app as qt_app,
    viewport as viewport,
    _scene,
    _visual_children,
)


def points(values):
    return tuple(ImagePoint(*p) for p in values)


def test_concave_polygon_area_perimeter_and_pixel_centers():
    p = points([(0, 0), (4, 0), (4, 4), (2, 2), (0, 4)])
    pixels = np.arange(25, dtype=float).reshape(5, 5)
    m = roi_metrics(
        p, MeasurementKind.FREEHAND, pixels, row_spacing=3, column_spacing=2, unit="HU"
    )
    assert m.area_mm2 == 72
    assert m.perimeter_mm == pytest.approx(8 + 24 + 2 * np.hypot(4, 6))
    expected = pixels[
        np.array(
            [
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 0, 1, 1],
                [1, 0, 0, 0, 1],
            ],
            dtype=bool,
        )
    ]
    assert m.pixel_count == 21
    assert m.mean == pytest.approx(expected.mean()) and m.std == pytest.approx(
        expected.std()
    )
    assert simple_polygon(p)
    roi = RoiMeasurement("id", "s", "i", 0, MeasurementKind.FREEHAND, p, m)
    assert hit_test_interior(roi, ImagePoint(2, 3)) is None
    assert hit_test_interior(roi, ImagePoint(1, 1)) is not None
    assert hit_test_outline(roi, ImagePoint(0, 2), 0.1) is not None
    assert loads(dumps(roi)) == roi


def test_crossings_invalid_spacing_and_padding():
    assert not simple_polygon(points([(0, 0), (4, 4), (0, 4), (4, 0)]))
    p = points([(-2, -2), (3, -2), (3, 3), (-2, 3)])
    pixels = np.full((3, 3), 7.0)
    pixels[0, 0] = np.nan
    m = roi_metrics(
        p, MeasurementKind.FREEHAND, pixels, row_spacing=2, column_spacing=1
    )
    assert m.area_mm2 == 50 and m.pixel_count == 8 and m.mean == 7
    assert (
        roi_metrics(
            p, MeasurementKind.FREEHAND, pixels, row_spacing=0, column_spacing=1
        ).area_mm2
        is None
    )
    old = encode(m)
    del old["fields"]["perimeter_mm"]
    assert decode(old).perimeter_mm is None


def test_freehand_creation_translation_vertex_edit_cancel_and_copy():
    c = MeasurementController()
    context = replace(
        _context(),
        measurement_kind=MeasurementKind.FREEHAND,
        modality_pixels=np.ones((100, 100)),
        endpoint_tolerance=1,
        line_tolerance=0.5,
    )
    start = _position(10, 10)
    c.begin(start, context)
    for x, y in [(30, 10), (30, 30), (20, 20), (10, 30), (10, 10)]:
        c.update(_drag(start, _position(x, y)))
    c.end(start)
    original = c.committed_measurements[0]
    assert len(original.points) == 5 and original.metrics.area_mm2 == 300
    assert c.selected_copy()["kind"] == "freehand"
    c.begin(_position(15, 15), context)
    c.update(_drag(_position(15, 15), _position(20, 15)))
    c.end(_position(20, 15))
    moved = c.committed_measurements[0]
    assert moved.points[0] == ImagePoint(15, 10) and moved.metrics.area_mm2 == 300
    c.begin(_position(15, 10), context)
    c.update(_drag(_position(15, 10), _position(12, 8)))
    c.cancel_transaction()
    assert c.committed_measurements[0] == moved
    copy = c.paste_points(list(original.points), context)
    assert copy and copy != original.measurement_id
    assert len(c.committed_measurements) == 2


def test_real_pointer_freehand_outline_and_metrics(viewport):
    view, controller, layer, warnings = viewport
    controller._tool_controller.selectInteraction("measure:freehand")
    layer_item = next(
        x
        for x in _visual_children(view.rootObject())
        if x.objectName() == "viewportInteractionLayer"
    )
    assert layer_item.property("hoverCursorKind") == "measure-freehand"
    assert layer_item.property("immediateRoiDrag")
    path = [(30, 35), (95, 35), (110, 65), (80, 80), (95, 110), (30, 95), (30, 35)]
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, _scene(layer, *path[0]))
    for p in path[1:]:
        QTest.mouseMove(view, _scene(layer, *p), 25)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, _scene(layer, *path[-1]))
    QTest.qWait(50)
    item = controller._measure_controller.committed_measurements[0]
    assert item.kind == MeasurementKind.FREEHAND and item.metrics.perimeter_mm > 0
    assert len(item.points) == len(path) - 1
    assert item.points[1].column == pytest.approx(path[1][0], abs=0.5)
    assert item.points[1].row == pytest.approx(path[1][1], abs=0.5)
    cards = [
        x
        for x in _visual_children(view.rootObject())
        if x.objectName() == "roiMetricCard" and x.isVisible()
    ]
    assert len(cards) == 1
    assert not warnings


def test_freehand_history_workspace_and_csv(qt_app, tmp_path):
    import csv
    from test_workspace_persistence import populated_app
    from test_dicom_tags import wait_until

    app, _ = populated_app(tmp_path)
    try:
        view = app.workspaceController.activeViewport
        controller = view._measure_controller
        history = app.workspaceController.activeTab.historyController
        context = view._measurement_context(3, 2, kind=MeasurementKind.FREEHAND)
        path = points([(30, 30), (60, 30), (60, 60), (45, 45), (30, 60)])
        identifier = controller.paste_points(list(path), context)
        history.capture()
        original = controller._measurements[identifier]
        assert original.metrics.area_mm2 == pytest.approx(675 * 0.7 * 0.8)
        assert original.metrics.pixel_count > 0 and original.metrics.perimeter_mm > 0
        history.undo()
        assert not controller.committed_measurements
        history.redo()
        assert controller._measurements[identifier] == original

        document = app.workspaceDocumentController
        filename = tmp_path / "freehand.voxworkspace"
        assert document.save_to(filename)
        wait_until(lambda: not document.busy)
        assert not document.isError, document.message
        assert document.restore_from(filename)
        wait_until(lambda: not document.busy)
        assert not document.isError, document.message
        restored = app.workspaceController.activeViewport._measure_controller
        assert restored._measurements[identifier] == original
        report = app.exportController.measurementReport
        csv_path = tmp_path / "freehand.csv"
        assert report.export_to(csv_path)
        wait_until(lambda: not report.busy)
        assert not report.isError, report.message
        with csv_path.open(encoding="utf-8-sig") as stream:
            rows = list(csv.reader(stream))
        assert float(rows[-1][-1]) == pytest.approx(
            original.metrics.perimeter_mm, abs=0.01
        )
    finally:
        app.shutdown()


def test_projected_measurement_retains_frame_origin_after_projection_disabled(viewport):
    window, view, layer, _ = viewport
    controller = view._measure_controller
    frame = view._frame_meta
    uid = view.viewport_config.series_uid
    controller.set_frame(uid, frame, source_context=("projection", "mip", 20))
    context = view._measurement_context(3, 2, kind=MeasurementKind.FREEHAND)
    identifier = controller.paste_points(
        list(points([(20, 20), (40, 20), (30, 40)])), context
    )
    assert controller._measurement_frames[identifier][6] == ("projection", "mip", 20)
    controller.set_frame(uid, frame)
    assert controller.visible_measurements == ()
    assert controller.committed_measurements[0].measurement_id == identifier
    assert (
        loads(dumps(controller._measurement_frames))[identifier][6][0] == "projection"
    )
