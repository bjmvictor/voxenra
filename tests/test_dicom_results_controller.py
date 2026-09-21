from pathlib import Path
from threading import Event
from types import SimpleNamespace
import pydicom
from PySide6.QtTest import QTest
from PySide6.QtCore import QPointF

from qt_dicom_viewer.ui.controller.dicom_results_controller import (
    DicomResultsController,
)
from qt_dicom_viewer.model import DicomFolderScanSnapshot
from test_dicom_results import source as source, segmentation, freehand
from test_dicom_tags import qt_app as qt_app, wait_until
from test_pacs_qml import scene as scene
from test_tag_qml import find, click


def workspace_for(series, volume):
    r = segmentation(series, volume)
    roi = freehand(series, volume)
    voi = SimpleNamespace(
        current_records=[r.record],
        evaluations={r.record["id"]: r.evaluation},
        busy=False,
        _draft=None,
    )
    measure = SimpleNamespace(
        committed_measurements=[roi.measurement],
        has_active_transaction=False,
        _measurement_frames={roi.measurement.measurement_id: roi.frame},
    )
    view = SimpleNamespace(_measure_controller=measure, viewportRole="image")
    workspace = SimpleNamespace(
        activeTab=SimpleNamespace(viewports_by_id={"a": view}, _voi_controller=voi)
    )
    catalog = SimpleNamespace(get_series=lambda uid: series)
    return workspace, catalog, r


def test_background_snapshot_survives_edit_tab_close_and_preserves_metrics(
    qt_app, source, tmp_path, monkeypatch
):
    series, volume = source
    workspace, catalog, r = workspace_for(series, volume)
    controller = DicomResultsController(workspace, catalog)
    import qt_dicom_viewer.core.dicom_results as module

    actual = module.write_results
    entered, release = Event(), Event()

    def blocked(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return actual(*args, **kwargs)

    monkeypatch.setattr(module, "write_results", blocked)
    try:
        assert controller.export_to(tmp_path) and entered.wait(3)
        assert not controller.export_to(tmp_path)
        r.evaluation.mask[:] = False
        r.record["name"] = "changed"
        workspace.activeTab = None
        release.set()
        wait_until(lambda: not controller.busy)
        assert not controller.isError, controller.message
        output = Path(controller.resultPath)
        assert len(list(output.glob("*.dcm"))) == 3
        assert (
            pydicom.dcmread(output / "SEG-001.dcm").SegmentSequence[0].SegmentLabel
            == "测试分割"
        )
    finally:
        release.set()
        controller.shutdown()


def test_draft_and_missing_evaluation_rejected_before_write(qt_app, source, tmp_path):
    series, volume = source
    workspace, catalog, _ = workspace_for(series, volume)
    controller = DicomResultsController(workspace, catalog)
    try:
        workspace.activeTab._voi_controller._draft = {"editing": True}
        assert not controller.export_to(tmp_path)
        assert controller.isError and not controller.busy
        workspace.activeTab._voi_controller._draft = None
        workspace.activeTab._voi_controller.evaluations.clear()
        assert not controller.export_to(tmp_path)
    finally:
        controller.shutdown()


def test_actual_export_panel_buttons_write_seg_and_linked_sr(
    scene, source, tmp_path, monkeypatch
):
    window, app, warnings = scene
    series, volume = source
    snapshot = DicomFolderScanSnapshot(
        tmp_path, len(series.instances), len(series.instances), 0, [series]
    )
    app.panelController.update_series_session(snapshot)
    app.panelController._update_series_record(snapshot)
    workspace = app.workspaceController
    workspace.createTab(series.series_instance_uid, "DICOM results", "mpr")
    tab = workspace.activeTab
    wait_until(lambda: bool(tab.voiController.sources))
    r = segmentation(series, volume)
    r.record.update(phase=None, visible=True)
    tab.voiController.records = [r.record]
    tab.voiController.evaluations = {r.record["id"]: r.evaluation}
    monkeypatch.setattr(
        "qt_dicom_viewer.ui.controller.dicom_results_controller.QFileDialog.getExistingDirectory",
        lambda *args: str(tmp_path),
    )
    window.resize(1280, 720)
    app.settingsController.setValue("layout", "rightPanelWidth", 220)
    QTest.qWait(80)
    tab.toolController.activateTool("export")
    QTest.qWait(80)
    flickable = find(window, "toolDetailFlickable")

    def reveal(name):
        button = find(window, name)
        point = button.mapToScene(QPointF(0, button.height()))
        bottom = flickable.mapToScene(QPointF(0, flickable.height())).y()
        if point.y() > bottom:
            flickable.setProperty(
                "contentY", flickable.property("contentY") + point.y() - bottom + 8
            )
        QTest.qWait(50)
        start = button.mapToScene(QPointF(0, 0))
        end = button.mapToScene(QPointF(button.width(), button.height()))
        assert 0 <= start.x() < end.x() <= window.width()
        assert 0 <= start.y() < end.y() <= window.height()
        return button

    controller = app.exportController.dicomResults
    click(window, reveal("exportSegmentation"))
    wait_until(lambda: not controller.busy)
    assert controller.resultPath and not controller.isError, controller.message
    assert len(list(Path(controller.resultPath).glob("SEG-*.dcm"))) == 1
    click(window, reveal("exportStructuredReport"))
    wait_until(lambda: not controller.busy)
    assert controller.resultPath and not controller.isError, controller.message
    assert len(list(Path(controller.resultPath).glob("*.dcm"))) == 2
    assert not warnings, warnings


def test_real_mpr_projection_export_rejected_even_after_disabling(
    qt_app, source, tmp_path
):
    from qt_dicom_viewer.ui.app_controller import AppController
    from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
    from qt_dicom_viewer.model import ImagePoint, MeasurementKind

    series, _ = source
    app = AppController(DicomImageProvider(), settings_path=False)
    try:
        snapshot = DicomFolderScanSnapshot(tmp_path, 4, 4, 0, [series])
        app.panelController.update_series_session(snapshot)
        app.panelController._update_series_record(snapshot)
        app.workspaceController.createTab(series.series_instance_uid, "MPR", "mpr")
        tab = app.workspaceController.activeTab
        wait_until(lambda: bool(tab.voiController.sources))
        view = tab.activeViewport
        tab.toolController.setMprThickness("axial", 6)
        tab.toolController.setMprProjectionEnabled(True)
        measure = view._measure_controller
        wait_until(
            lambda: measure.frame_key is not None and len(measure.frame_key) == 7
        )
        context = view._measurement_context(1, 0.1, kind=MeasurementKind.FREEHAND)
        identifier = measure.paste_points(
            [ImagePoint(1, 1), ImagePoint(4, 1), ImagePoint(3, 4)], context
        )
        assert identifier
        tab.toolController.setMprProjectionEnabled(False)
        wait_until(lambda: len(measure.frame_key) == 6)
        export = app.exportController.dicomResults
        assert export.export_to(tmp_path)
        wait_until(lambda: not export.busy)
        assert export.isError and not export.resultPath
        assert not list(tmp_path.glob("voxenra-results-*"))
    finally:
        app.shutdown()
