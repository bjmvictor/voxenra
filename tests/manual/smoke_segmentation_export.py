"""Native Qt UI smoke test with a synthetic CT, never a patient's data.

QT_QPA_PLATFORM=cocoa QT_QUICK_BACKEND=software .venv/bin/python \
    tests/manual/smoke_segmentation_export.py
Screenshots and exported DICOM stay in ignored build/validation/seg-sr/ui.
"""

from pathlib import Path
import sys
from unittest.mock import patch

import pydicom
from PySide6.QtCore import QPointF, QUrl, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import delete

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from i18n_support import install_default_language
from test_series_sidebar import phantom_series
from test_dicom_tags import wait_until
from test_tag_qml import find, click
from qt_dicom_viewer.core.dicom_scanner import DicomFolderScanner
from qt_dicom_viewer.ui.app_controller import AppController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider

output = ROOT / "build/validation/seg-sr/ui"
source = output / "source"
source.mkdir(parents=True, exist_ok=True)
phantom_series(
    source, 1, "SYNTHETIC-DEMO", "1.2.826.0.1.3680043.10.999.500", "20260916"
)
for path in source.glob("*.dcm"):
    ds = pydicom.dcmread(path)
    ds.FrameOfReferenceUID = "1.2.826.0.1.3680043.10.999.501"
    ds.save_as(path, enforce_file_format=True)
snapshot = list(
    DicomFolderScanner().scan_files(list(source.glob("*.dcm")), folder=source)
)[-1]
record = snapshot.series[0]
qt = QApplication.instance() or QApplication([])
install_default_language(qt)
provider = DicomImageProvider()
app = AppController(
    provider,
    settings_path=False,
    pacs_config_path=output / "pacs.json",
    pacs_import_root=output / "imports",
)
engine = QQmlApplicationEngine()
engine.addImageProvider("navigation", SvgIconProvider())
engine.addImageProvider("dicom", provider)
engine.rootContext().setContextProperty("appController", app)
warnings = []
engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
engine.load(QUrl.fromLocalFile(str(ROOT / "src/qt_dicom_viewer/qml/Main.qml")))
window = engine.rootObjects()[0]


def screenshot(name):
    QTest.qWait(200)
    assert window.grabWindow().save(str(output / f"{name}.png"))


def reveal(name):
    item, flickable = find(window, name), find(window, "toolDetailFlickable")
    edge = item.mapToScene(QPointF(0, item.height())).y()
    bottom = flickable.mapToScene(QPointF(0, flickable.height())).y()
    if edge > bottom:
        flickable.setProperty(
            "contentY", flickable.property("contentY") + edge - bottom + 8
        )
    QTest.qWait(100)
    return item


try:
    app.panelController.update_series_session(snapshot)
    app.panelController._update_series_record(snapshot)
    workspace = app.workspaceController
    workspace.createTab(record.series_instance_uid, "Synthetic CT", "2d")
    view = workspace.activeViewport
    wait_until(lambda: view.loadState == "ready")
    window.resize(1400, 900)
    window.show()
    window.requestActivate()
    QTest.qWait(250)
    view._tool_controller.activateTool("measure")
    view._tool_controller.selectInteraction("measure:freehand")
    layer = find(window, "dicomPixelLayer")
    path = [(28, 28), (64, 28), (69, 48), (59, 65), (49, 55), (29, 66), (28, 28)]
    position = lambda p: layer.mapToScene(QPointF(p[0] + 0.5, p[1] + 0.5)).toPoint()
    QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, position(path[0]))
    for point in path[1:]:
        QTest.mouseMove(window, position(point), 30)
    QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, position(path[-1]))
    QTest.qWait(100)
    assert len(view._measure_controller.committed_measurements) == 1
    screenshot("freehand")
    # The 2D SR button exports the pointer-drawn contour.
    view._tool_controller.activateTool("export")
    with patch(
        "qt_dicom_viewer.ui.controller.dicom_results_controller.QFileDialog.getExistingDirectory",
        return_value=str(output),
    ):
        click(window, reveal("exportStructuredReport"))
    wait_until(lambda: not app.exportController.dicomResults.busy)
    assert not app.exportController.dicomResults.isError, (
        app.exportController.dicomResults.message
    )
    screenshot("freehand-report")

    workspace.createTab(record.series_instance_uid, "Synthetic CT MPR", "mpr")
    tab = workspace.activeTab
    wait_until(
        lambda: (
            bool(tab.voiController.sources)
            and tab.activeViewport._plane_geometry is not None
        )
    )
    tab.toolController.activateTool("segmentation")
    controller = tab.voiController
    controller.begin(tab.activeViewport, 20, 20, 0.1)
    controller.finish(tab.activeViewport, 75, 80)
    wait_until(lambda: bool(controller.evaluations) and not controller.busy)
    assert controller.evaluations[controller.selectedId].metrics["count"] > 0
    screenshot("segmentation")
    tab.toolController.activateTool("export")
    window.resize(1000, 600)
    app.settingsController.setValue("layout", "rightPanelWidth", 260)
    QTest.qWait(100)
    with patch(
        "qt_dicom_viewer.ui.controller.dicom_results_controller.QFileDialog.getExistingDirectory",
        return_value=str(output),
    ):
        click(window, reveal("exportStructuredReport"))
    wait_until(lambda: not app.exportController.dicomResults.busy)
    assert not app.exportController.dicomResults.isError, (
        app.exportController.dicomResults.message
    )
    reveal("dicomResultsPath")
    screenshot("segmentation-report-small")
    assert not warnings, warnings
    print("NATIVE_UI_OK", output, flush=True)
finally:
    window.hide()
    app.shutdown()
    delete(engine)
