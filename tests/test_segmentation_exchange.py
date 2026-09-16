from pathlib import Path
from threading import Event

import numpy as np
import pytest
from PySide6.QtTest import QTest

from qt_dicom_viewer.model import DicomFolderScanSnapshot, ImagePoint, MeasurementKind
from qt_dicom_viewer.ui.app_controller import AppController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from test_dicom_results import source as source
from test_dicom_tags import qt_app as qt_app, wait_until
from test_segmentation_import import external_seg as external_seg, full_mask
from test_pacs_qml import scene as scene
from test_tag_qml import find, click
from PySide6.QtCore import QPointF


def open_mpr(app, series, folder):
    snapshot = DicomFolderScanSnapshot(
        folder, len(series.instances), len(series.instances), 0, [series]
    )
    app.panelController.update_series_session(snapshot)
    app.panelController._update_series_record(snapshot)
    app.workspaceController.createTab(series.series_instance_uid, "Exchange", "mpr")
    tab = app.workspaceController.activeTab
    wait_until(
        lambda: (
            bool(tab.voiController.sources) and not tab.activeViewport.render_pending
        )
    )
    return tab


@pytest.fixture
def exchange(qt_app, source, tmp_path):
    app = AppController(DicomImageProvider(), settings_path=False)
    tab = open_mpr(app, source[0], tmp_path)
    yield app, tab, app.exportController.dicomResults
    app.shutdown()


def import_masks(controller, path):
    assert controller.import_from(path), controller.message
    wait_until(lambda: not controller.busy)
    assert not controller.isError, controller.message


def test_import_history_persistence_and_reexport(exchange, external_seg, tmp_path):
    app, tab, controller = exchange
    path, expected, _ = external_seg
    voi, history = tab.voiController, tab.historyController
    import_masks(controller, path)
    wait_until(lambda: not voi.busy)
    assert len(voi.items) == 2 and all(i["fixedMask"] for i in voi.items)
    assert all(voi.masks(view) for view in tab.viewports_by_id.values())
    assert not voi.overlays(tab.activeViewport)
    history.capture()
    history.undo()
    assert not voi.records
    history.redo()
    wait_until(lambda: len(voi.evaluations) == 2 and not voi.busy)
    first = voi.records[0]
    voi.select(first["id"])
    voi.setThreshold(999)
    voi.setDepth(999)
    assert first["threshold"] == 0
    np.testing.assert_array_equal(
        full_mask(first, expected.shape[:3]), expected[..., 0]
    )
    voi.renameItem(first["id"], "Renamed")
    voi.setColor(first["id"], "#ffbb55")
    voi.toggleVisible(first["id"])
    assert not first["visible"]
    # A duplicate file must not partially append its segments.
    assert controller.import_from(path)
    wait_until(lambda: not controller.busy)
    assert controller.isError and len(voi.records) == 2
    document = app.workspaceDocumentController
    workspace_file = tmp_path / "masks.voxworkspace"
    assert document.save_to(workspace_file)
    wait_until(lambda: not document.busy)
    assert not document.isError, document.message
    path.unlink()
    assert document.restore_from(workspace_file)
    wait_until(lambda: not document.busy, timeout=20000)
    assert not document.isError, document.message
    restored = app.workspaceController.activeTab.voiController
    wait_until(lambda: len(restored.evaluations) == 2 and not restored.busy)
    assert restored.records[0]["name"] == "Renamed"
    assert restored.records[0]["color"] == "#ffbb55"
    assert not restored.records[0]["visible"]
    for index, record in enumerate(restored.records):
        np.testing.assert_array_equal(
            full_mask(record, expected.shape[:3]), expected[..., index]
        )
    assert controller.export_to(tmp_path)
    wait_until(lambda: not controller.busy)
    assert not controller.isError, controller.message
    assert len(list(Path(controller.resultPath).glob("*.dcm"))) == 3


@pytest.mark.parametrize("change", ["cancel", "close", "phase"])
def test_import_does_not_publish_after_target_changes(
    exchange, external_seg, monkeypatch, change
):
    app, tab, controller = exchange
    import qt_dicom_viewer.core.segmentation_import as module

    actual = module.read_segmentation
    entered, release = Event(), Event()

    def blocked(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return actual(*args, **kwargs)

    monkeypatch.setattr(module, "read_segmentation", blocked)
    try:
        assert controller.import_from(external_seg[0])
        assert entered.wait(3)
        if change == "cancel":
            controller.cancel()
        elif change == "close":
            app.workspaceController.closeTab(tab.tab_config.tab_id)
        else:
            tab.voiController._phase = "another-phase"
        release.set()
        wait_until(lambda: not controller.busy)
        assert not tab.voiController.records
        assert controller.isError == (change != "cancel")
    finally:
        release.set()


def test_selected_freehand_conversion_keeps_measurement_and_can_undo(
    exchange, tmp_path
):
    from test_series_sidebar import phantom_series

    app, _, controller = exchange
    folder = tmp_path / "orthogonal"
    folder.mkdir()
    series = phantom_series(folder, 1, "TEST", "1.2.3.9", "20260916")
    tab = open_mpr(app, series, folder)
    view = tab.activeViewport
    tab.toolController.activateTool("measure")
    measure = view._measure_controller
    wait_until(lambda: measure.frame_key is not None)
    context = view._measurement_context(1, 0.1, kind=MeasurementKind.FREEHAND)
    identifier = measure.paste_points(
        [ImagePoint(1, 1), ImagePoint(4, 1), ImagePoint(3, 4)], context
    )
    assert identifier
    tab.historyController.capture()
    assert controller.convertSelectedRoi(), controller.message
    wait_until(lambda: not controller.busy)
    assert not controller.isError, controller.message
    assert len(tab.voiController.records) == 1
    assert identifier in measure._measurements
    tab.historyController.capture()
    tab.historyController.undo()
    assert not tab.voiController.records and identifier in measure._measurements
    QTest.qWait(50)


def test_import_button_and_mask_list_at_small_window(
    scene, source, external_seg, tmp_path, monkeypatch
):
    window, app, warnings = scene
    tab = open_mpr(app, source[0], tmp_path)
    controller = app.exportController.dicomResults
    window.resize(1000, 600)
    app.settingsController.setValue("layout", "rightPanelWidth", 240)
    monkeypatch.setattr(
        "qt_dicom_viewer.ui.controller.dicom_results_controller.QFileDialog.getOpenFileName",
        lambda *args: (str(external_seg[0]), ""),
    )
    QTest.qWait(100)
    flickable = find(window, "toolDetailFlickable")

    def reveal(name):
        item = find(window, name)
        edge = item.mapToScene(QPointF(0, item.height())).y()
        bottom = flickable.mapToScene(QPointF(0, flickable.height())).y()
        if edge > bottom:
            flickable.setProperty(
                "contentY", flickable.property("contentY") + edge - bottom + 8
            )
        QTest.qWait(70)
        return item

    click(window, find(window, "primaryTool-import"))
    QTest.qWait(80)
    click(window, reveal("importSegmentation"))
    wait_until(lambda: not controller.busy)
    assert not controller.isError, controller.message
    click(window, reveal("manageImportedSegments"))
    QTest.qWait(80)
    first = tab.voiController.records[0]
    click(window, reveal("voiVisibility-" + first["id"]))
    assert not first["visible"]
    original = first["color"]
    click(window, reveal("voiColor-" + first["id"]))
    assert first["color"] != original
    assert find(window, "voiRegionList").property("count") == 2
    click(window, reveal("voiDelete-" + first["id"]))
    assert len(tab.voiController.records) == 1
    assert not warnings, warnings
