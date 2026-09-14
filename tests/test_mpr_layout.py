"""Layout changes preserve image state; 3D references use actual patient geometry."""
from dataclasses import replace
from pathlib import Path
import os

import numpy as np
import pytest
from PySide6.QtCore import QObject, QUrl, QPoint, Qt
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest
from vtkmodules.vtkRenderingCore import vtkRenderer
from shiboken6 import delete

from qt_dicom_viewer.core.mpr_layout import MPR_LAYOUTS, plane_box_intersection
from qt_dicom_viewer.core.volume_view import view_basis, rotate_drag, camera_parameters
from qt_dicom_viewer.core.volume_manager import VolumeManager
from qt_dicom_viewer.model import MprPlane
from qt_dicom_viewer.ui.controller.workspace_controller import WorkspaceController
from qt_dicom_viewer.ui.controller.settings_controller import SettingsController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider
from qt_dicom_viewer.ui.workers.dicom_render_worker import DicomRenderWorker
from qt_dicom_viewer.ui.workspace_snapshot import tab_snapshot, apply_tab_snapshot
from qt_dicom_viewer.ui.mpr_reference_overlay import MprReferenceOverlay
from test_pet_fusion import paired_series
from test_measurement_qml import qt_app, _visual_children
from test_volume_view import volume


@pytest.fixture(params=["CT", "PT"])
def loaded(qt_app, paired_series, request):
    catalog, ct, pet = paired_series
    host = QObject()
    host._settings_controller = SettingsController(host, path=False)
    provider = DicomImageProvider()
    workspace = WorkspaceController(catalog, provider, host)
    worker = DicomRenderWorker(catalog, VolumeManager())
    failures, requests = [], []
    worker.render_finished.connect(workspace.handleRenderResult)
    worker.render_failed.connect(failures.append)
    workspace.renderRequested.connect(requests.append)
    workspace.renderRequested.connect(worker.handleRenderRequest)
    series = ct if request.param == "CT" else pet
    workspace.createTab(series.series_instance_uid, "MPR layout", "mpr")
    assert not failures
    tab = workspace.activeTab
    yield workspace, tab, provider, requests, failures
    workspace.shutdown()


def move(tab, center):
    tab.mprLayout.move_center(center)


def rotate(tab, angle=.23):
    if hasattr(tab, "_rotate_plane"):
        tab._rotate_plane(MprPlane.AXIAL, angle)
    else:
        tab._handle_crosshair_rotation_requested(MprPlane.AXIAL, angle)


def test_layout_reuses_volume_and_preserves_mpr_and_view_state(loaded):
    workspace, tab, provider, requests, failures = loaded
    layout = tab.mprLayout
    initial_views = tuple(tab.viewports_by_id.values())
    state, frames = tab._target_mpr_state, [v._frame_meta for v in initial_views]
    before = len(requests)
    assert layout.volumeViewport.volume is None
    for key in (*MPR_LAYOUTS, "not-a-layout", "right", "quad"):
        layout.setLayout(key)
        assert tuple(tab.viewports_by_id.values()) == initial_views
        assert tab._target_mpr_state == state
        assert [v._frame_meta for v in initial_views] == frames
    assert len(requests) == before  # no new decoding or reslicing on layout changes
    assert layout.volumeViewport.volume is layout._pending_volume
    assert layout.volumeViewport.loadState == "ready"
    assert layout.volumeViewport._host is None  # native GPU host remains lazy
    tab.focusSingleViewport(initial_views[0].viewportId)
    layout.setLayout(layout.layout)
    assert tab.focusedViewportId == ""
    assert not failures


def test_marker_move_and_bidirectional_optional_rotation(loaded):
    _, tab, _, _, failures = loaded
    layout = tab.mprLayout
    layout.setLayout("quad")
    view = layout.volumeViewport
    initial_camera = view.state
    rotate(tab)
    assert view.state == initial_camera
    layout.setLinkRotation(True)
    frame = tab._target_mpr_state.frame
    camera = view_basis(view.state)
    rotate(tab)
    delta = tab._target_mpr_state.frame.mpr_to_patient[:3, :3] @ frame.mpr_to_patient[:3, :3].T
    np.testing.assert_allclose(view_basis(view.state), delta @ camera, atol=1e-10)
    frame = tab._target_mpr_state.frame
    before = view.state
    view._set_state(rotate_drag(before, (25, 20), (95, 72), (200, 180)))
    delta = view_basis(view.state) @ view_basis(before).T
    np.testing.assert_allclose(tab._target_mpr_state.frame.mpr_to_patient[:3, :3],
                               delta @ frame.mpr_to_patient[:3, :3], atol=1e-10)
    # Zoom and pan never rotate or displace MPR.
    frame = tab._target_mpr_state.frame
    view._set_state(replace(view.state, zoom=1.5, pan=(.1, .2)))
    assert tab._target_mpr_state.frame == frame
    layout.setLinkRotation(False)
    view._set_state(rotate_drag(view.state, (15, 40), (65, 75), (200, 180)))
    assert tab._target_mpr_state.frame == frame
    center = view.volume.geometry.center_patient
    move(tab, center)
    np.testing.assert_allclose(layout._last_frame.center_patient, center)
    # Hit and drag the actual projected point, even with oblique camera/pan/zoom.
    size = (500, 450)
    params = camera_parameters(view.volume.geometry, view.state, size)
    basis = view_basis(view.state)
    delta = np.asarray(center) - params["focal"]
    factor = size[1]/(2*params["scale"])
    screen = (size[0]/2+np.dot(delta, basis[:, 0])*factor,
              size[1]/2-np.dot(delta, basis[:, 1])*factor)
    view.begin_drag(screen, size)
    assert view._marker_drag is not None
    view.update_drag((screen[0]+2, screen[1]+1))
    view.end_drag()
    assert tab._target_mpr_state.frame.center_patient != center
    assert view._marker_drag is None
    assert not failures


def test_reference_planes_clip_to_oblique_anisotropic_volume(volume):
    g = volume.geometry
    center = np.asarray(g.center_patient)
    for normal in ((0., 0., 1.), (0., 1., 0.), (1., 0., 0.), tuple(np.ones(3)/np.sqrt(3))):
        polygon = plane_box_intersection(g, center, normal)
        assert 3 <= len(polygon) <= 6
        for p in polygon:
            assert np.dot(np.array(p)-center, normal) == pytest.approx(0, abs=1e-6)
            voxel = (g.patient_to_voxel @ [*p, 1])[:3]
            assert np.all(voxel >= -1e-6)
            assert np.all(voxel <= np.array((g.slice_count-1, g.rows-1, g.columns-1))+1e-6)
    assert plane_box_intersection(g, center + 1000, (0, 0, 1)) == ()


def test_four_d_reference_tracks_phase_and_ignores_closed_updates(qt_app, tmp_path):
    from test_four_d import _cross_series_four_d
    from qt_dicom_viewer.application.series_catalog import SeriesCatalog
    from qt_dicom_viewer.model import DicomFolderScanSnapshot
    series = _cross_series_four_d(tmp_path)
    catalog = SeriesCatalog()
    catalog.update(DicomFolderScanSnapshot(folder=tmp_path, series=series,
        total_file_count=6, dicom_file_count=6, skipped_file_count=0))
    provider = DicomImageProvider()
    workspace = WorkspaceController(catalog, provider)
    worker = DicomRenderWorker(catalog, VolumeManager())
    failures = []
    worker.render_finished.connect(workspace.handleRenderResult)
    worker.render_failed.connect(failures.append)
    workspace.renderRequested.connect(worker.handleRenderRequest)
    workspace.createTab(series[0].series_instance_uid, "4D layout", "4d")
    tab = workspace.activeTab
    layout = tab.mprLayout
    try:
        layout.setLayout("quad")
        volume = layout.volumeViewport.volume
        state = tab._target_mpr_state
        for index in (1, 2, 0):
            tab.setPhaseIndex(index)
            assert layout.volumeViewport.volume.modality_pixels.mean() == pytest.approx((index+1)*10)
            assert tab._target_mpr_state == state
        workspace.closeTab(tab.tab_config.tab_id)
        layout.accept_volume(volume)
        assert layout._disposed and layout._pending_volume is None
        assert not failures
    finally:
        workspace.shutdown()


def test_reference_mode_colors_and_snapshot_restore(loaded):
    _, tab, _, _, failures = loaded
    layout = tab.mprLayout
    layout.setLayout("quad")
    rotate(tab)
    layout.setReferenceMode("point")
    layout.setLinkRotation(True)
    view = layout.volumeViewport
    view._set_state(replace(view.state, zoom=2))
    record = tab_snapshot(tab)
    layout.setLayout("columns")
    layout.setLinkRotation(False)
    layout.setReferenceMode("hidden")
    view._set_state(replace(view.state, zoom=1))
    apply_tab_snapshot(tab, record)
    assert layout.layout == "quad" and layout.referenceMode == "point" and layout.linkRotation
    assert view.state.zoom == 2
    renderer = vtkRenderer()
    overlay = MprReferenceOverlay(renderer)
    colors = ("#ff0000", "#00ff00", "#0000ff")
    for mode in ("planes", "point", "hidden"):
        overlay.update(view.volume.geometry, tab._target_mpr_state, mode, colors)
        assert (overlay.center is None) == (mode == "hidden")
        assert all(bool(a.GetVisibility()) == (mode == "planes") for _, a in overlay.planes)
    assert not failures


def test_pet_reference_restore_before_first_volume_and_reset_uses_shared_unit(loaded):
    _, tab, _, requests, failures = loaded
    if not hasattr(tab, "pet_display"):
        return
    from qt_dicom_viewer.ui.controller.tab.mpr_layout_controller import MprLayoutController
    layout = tab.mprLayout
    layout.setLayout("quad")
    view = layout.volumeViewport
    view.setPetUpper(.25)
    view.setPetOpacity(.4)
    state = layout.snapshot()
    restored = MprLayoutController(tab)
    try:
        restored.restore(state)
        assert restored.volumeViewport.volume is None
        restored.accept_volume(view.volume)
        assert restored.volumeViewport.petUpper == pytest.approx(.25)
        assert restored.volumeViewport.petOpacity == pytest.approx(.4)
        before = len(requests)
        restored.volumeViewport.reset_all_view_state()
        assert restored.volumeViewport.loadState == "ready"
        assert restored.volumeViewport._request_id is None
        assert len(requests) == before
        assert not failures
    finally:
        restored.dispose()


@pytest.mark.parametrize("size", [(1100, 760), (780, 550)])
def test_real_qml_layout_choices_bounds_and_state(loaded, monkeypatch, size):
    workspace, tab, provider, _, failures = loaded
    # Native VTK embedding is tested separately on Cocoa; this test exercises real QML.
    monkeypatch.setattr(type(tab.mprLayout.volumeViewport), "ensureNativeView", lambda self: None)
    view = QQuickView()
    view.engine().addImageProvider("navigation", SvgIconProvider())
    view.engine().addImageProvider("dicom", provider)
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(*size)
    view.setInitialProperties(dict(workspace=workspace, tabController=tab, rightPanelWidth=220))
    view.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / "qml/MprVoiWorkspace.qml")))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(80)
    try:
        # Exercise the real toolbar entry rather than opening its panel directly.
        items = list(_visual_children(view.rootObject()))
        entry = next(i for i in items if i.objectName() == "primaryTool-mpr-layout")
        assert entry.isVisible() and entry.isEnabled()
        assert entry.width() > 0 and entry.height() > 0
        point = entry.mapToScene(entry.boundingRect().center()).toPoint()
        QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, point)
        QTest.qWait(35)
        assert tab.toolController.activePanel == "mpr-layout"
        assert any(i.objectName() == "mprLayoutPanel" and i.isVisible()
                   for i in _visual_children(view.rootObject()))
        for key in MPR_LAYOUTS:
            items = list(_visual_children(view.rootObject()))
            button = next(i for i in items if i.objectName() == "mprLayout-"+key)
            p = button.mapToScene(button.boundingRect().center()).toPoint()
            QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, p)
            QTest.qWait(35)
            assert tab.mprLayout.layout == key
            items = list(_visual_children(view.rootObject()))
            cells = [i for i in items if i.objectName().startswith("mprLayoutCell-") and i.isVisible()]
            reference = next(i for i in items if i.objectName() == "mprReferenceViewport")
            assert reference.isVisible() == (key == "quad")
            if reference.isVisible(): cells.append(reference)
            for i, a in enumerate(cells):
                assert a.width() > 0 and a.height() > 0
                assert a.x() >= 0 and a.y() >= 0
                assert a.x()+a.width() <= a.parentItem().width()+1
                assert a.y()+a.height() <= a.parentItem().height()+1
                for b in cells[i+1:]:
                    assert min(a.x()+a.width(), b.x()+b.width()) <= max(a.x(), b.x())+1 \
                        or min(a.y()+a.height(), b.y()+b.height()) <= max(a.y(), b.y())+1
        assert not warnings
        assert not failures
    finally:
        view.close()
        delete(view)
        QTest.qWait(20)


@pytest.mark.skipif(os.environ.get("VOXENRA_NATIVE_QA") != "1", reason="requires native desktop window")
def test_native_four_up_reference_view(loaded, tmp_path):
    workspace, tab, provider, _, failures = loaded
    layout = tab.mprLayout
    layout.setLayout("quad")
    view = QQuickView()
    view.engine().addImageProvider("navigation", SvgIconProvider())
    view.engine().addImageProvider("dicom", provider)
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(1200, 820)
    view.setInitialProperties(dict(workspace=workspace, tabController=tab, rightPanelWidth=250))
    view.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / "qml/MprVoiWorkspace.qml")))
    view.show()
    tab.toolController.activateTool("mpr-layout")
    try:
        QTest.qWait(600)
        v = layout.volumeViewport
        host = v._host
        assert host and host._active and host.backend._initialized
        assert v.loadState == "ready", v.errorMessage
        assert host.backend.mpr_reference.center == tab._target_mpr_state.frame.center_patient
        widget = host.vtk_widget
        layout.setLinkRotation(True)
        frame = tab._target_mpr_state.frame
        QTest.mousePress(widget, Qt.LeftButton, Qt.NoModifier, QPoint(30, 30))
        QTest.mouseMove(widget, QPoint(95, 75), 25)
        QTest.mouseRelease(widget, Qt.LeftButton, Qt.NoModifier, QPoint(95, 75))
        QTest.qWait(250)
        assert tab._target_mpr_state.frame != frame
        image = v.snapshot_image()
        assert not image.isNull()
        assert image.save(str(tmp_path / "mpr-reference.png"))
        layout.setLayout("rows")
        QTest.qWait(100)
        assert not host._active
        layout.setLayout("quad")
        view.resize(960, 680)
        QTest.qWait(250)
        assert host._active and v.loadState == "ready"
        # Close while the native child is attached, as in the real tab strip.
        workspace.closeTab(tab.tab_config.tab_id)
        QTest.qWait(50)
        assert host._disposed and not host._active
        assert not warnings
        assert not failures
    finally:
        view.close()
        delete(view)
        QTest.qWait(30)
