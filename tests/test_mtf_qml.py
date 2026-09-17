"""真实工具栏、视口鼠标事件和 Canvas 结果的端到端测试。"""

from pathlib import Path
from dataclasses import replace

import numpy as np
import pytest
from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest
from shiboken6 import delete

from qt_dicom_viewer.model import TabType, ToolType
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from test_measurement_qml import qt_app, _mouse_drag, _scene, _visual_children
from test_mtf_controller import bead_render, wait_result
from test_service_panel_qml import _click, _find
from test_viewport_transform import _controller


@pytest.fixture
def workspace(qt_app, request):
    # Exercise the actual 2D toolbar; the unscoped catalog also includes tools
    # belonging only to PET fusion and 3D workspaces.
    controller = _controller(tab_type=TabType.TWO_D)
    frame = bead_render(controller)
    controller.handleRenderResult(frame)
    controller._tool_controller.resetRequested.connect(lambda tool: controller.reset_tool_state(ToolType(tool)))
    view = QQuickView()
    from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider
    view.engine().addImageProvider("navigation", SvgIconProvider())
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    size = getattr(request, "param", (1200, 820))
    view.resize(*size)
    provider = DicomImageProvider()
    provider.set_array(controller.viewport_config.viewport_id, frame.image)
    view.engine().addImageProvider("dicom", provider)
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.setInitialProperties({"viewportController": controller, "toolController": controller._tool_controller})
    view.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / "qml/MtfWorkspace.qml")))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(80)
    pixels = view.rootObject().findChild(QQuickItem, "dicomPixelLayer")
    try:
        yield view, controller, pixels, warnings
    finally:
        controller.shutdown()
        view.hide()
        delete(view)


@pytest.mark.parametrize("workspace", [(1200, 820), (760, 560)], indirect=True)
def test_real_service_roi_to_canvas_chart_and_metrics(workspace, tmp_path):
    view, controller, pixels, warnings = workspace
    _click(view, _find(view, "primaryTool-service"))
    _click(view, _find(view, "serviceEntry-mtf"))
    assert controller.activeInteraction == "service:mtf"
    _mouse_drag(view, _scene(pixels, 8, 8), _scene(pixels, 118, 118))
    wait_result(controller.mtfController)
    QTest.qWait(100)
    assert controller.mtfController.status == "ready"
    chart = _find(view, "mtfChart")
    assert chart.width() > 200
    legend = _find(view, "mtfThresholdLegend")
    legend_position = legend.mapToItem(chart, QPointF())
    assert legend_position.x() > 0
    assert 0 <= legend_position.y() < 40
    assert legend_position.x() + legend.width() <= chart.width()
    texts = [item.property("text") for item in _visual_children(_find(view, "mtfResults"))
             if item.isVisible() and item.property("text")]
    assert not any("未做微珠尺寸修正" in text for text in texts)
    for index in (1, 2, 4, 5):
        assert float(_find(view, "mtfMetric-" + str(index)).property("text")) > 0
    assert _find(view, "mtfRoiLabel").property("text") == controller.mtfController.roiMetricLabel
    assert controller.mtfController.roiMetricLabel.startswith("ROI  ")
    assert " mm · " in controller.mtfController.roiMetricLabel
    assert " px\n" in controller.mtfController.roiMetricLabel
    badge = _find(view, "mtfRoiMetricBadge")
    badge_top_left = badge.mapToScene(QPointF())
    badge_bottom_right = badge.mapToScene(QPointF(badge.width(), badge.height()))
    assert 0 <= badge_top_left.x() < badge_bottom_right.x() <= view.width()
    assert 0 <= badge_top_left.y() < badge_bottom_right.y() <= view.height()
    assert not [item for item in _visual_children(view.rootObject())
                if item.objectName() == "roiMetricCard" and item.isVisible()]
    status = next(item for item in _visual_children(_find(view, "mtfResults"))
                  if item.objectName() == "mtfStatus")
    assert status.property("text") == "" and not status.isVisible()
    assert not any("质量提示不代表" in text for text in texts)

    measurement_label = _find(view, "mtfMeasurementMethodLabel")
    analysis_label = _find(view, "mtfAnalysisMethodLabel")
    for label, option_names in [
        (measurement_label, ["mtfMeasurementMethod-bead", "mtfMeasurementMethod-wire"]),
        (analysis_label, ["mtfAnalysisMethod-direct_fft", "mtfAnalysisMethod-gaussian"]),
    ]:
        label_center = label.mapToScene(QPointF(0, label.height() / 2)).y()
        assert all(_find(view, name).mapToScene(
            QPointF(0, _find(view, name).height() / 2)).y() == pytest.approx(label_center)
            for name in option_names)

    saved_result = controller.mtfController.currentResult
    x_legend, y_legend = _find(view, "mtfLegend-x"), _find(view, "mtfLegend-y")
    assert chart.property("showX") and chart.property("showY")
    _click(view, x_legend)
    assert not chart.property("showX") and chart.property("showY")
    _click(view, y_legend)
    assert not chart.property("showX") and not chart.property("showY")
    _click(view, x_legend)
    _click(view, y_legend)
    assert chart.property("showX") and chart.property("showY")
    assert controller.mtfController.currentResult == saved_result
    panel = _find(view, "rightPanel")
    results = _find(view, "mtfResults")
    # 水平空间受操作栏约束；高度不足交给外层 Flickable，不挤压或截短指标。
    assert results.width() <= panel.width()
    for item in _visual_children(results):
        if item.isVisible() and item.width() > 0:
            position = item.mapToItem(results, QPointF())
            assert position.x() >= -1
            assert position.x() + item.width() <= results.width() + 1
    screenshot = view.grabWindow()
    assert not screenshot.isNull()
    path = tmp_path / f"mtf-{view.width()}x{view.height()}-dpr{view.devicePixelRatio():g}.png"
    assert screenshot.save(str(path))
    print(f"MTF QML preview: {path}")
    if view.width() < 900:
        flickable = _find(view, "toolDetailFlickable")
        assert flickable.isVisible() and flickable.height() > 0
        assert flickable.property("contentHeight") > flickable.height()
        flickable.setProperty("contentY", flickable.property("contentHeight") - flickable.height())
        QTest.qWait(50)
        metric = _find(view, "mtfMetric-5")
        metric_y = metric.mapToItem(flickable, QPointF()).y()
        assert 0 <= metric_y <= flickable.height() - metric.height()
        scroll_path = tmp_path / f"mtf-small-scrolled-dpr{view.devicePixelRatio():g}.png"
        assert view.grabWindow().save(str(scroll_path))
        print(f"MTF scrolled preview: {scroll_path}")
        flickable.setProperty("contentY", 0)
        QTest.qWait(20)
    saved = controller.mtfController.roiController.measurementItems
    _click(view, _find(view, "serviceEntry-qa"))
    assert controller.activeInteraction == "service:qa"
    assert controller._tool_controller.canResetActiveTool
    assert controller._tool_controller.resetLabel == "重置水模 QA"
    assert not [item for item in _visual_children(view.rootObject())
                if item.objectName() == "mtfResults" and item.isVisible()]
    _mouse_drag(view, _scene(pixels, 20, 20), _scene(pixels, 90, 90))
    assert controller.mtfController.roiController.measurementItems == saved
    _click(view, _find(view, "primaryTool-service"))
    _click(view, _find(view, "serviceEntry-mtf"))
    assert controller._tool_controller.resetLabel == "重置 MTF"
    controller._tool_controller.resetActiveTool()
    assert controller.mtfController.status == "empty"
    assert not warnings, warnings


def test_canvas_handles_response_above_one_and_missing_crossings(workspace, tmp_path):
    view, controller, pixels, warnings = workspace
    frame = bead_render(controller)
    data = np.zeros((128, 128))
    data[64, 64] = 10
    data[64, 63] = data[64, 65] = -2
    controller.mtfController.setAnalysisMethod("direct_fft")
    controller.handleRenderResult(replace(frame, modality_pixel=data))
    controller._tool_controller.selectService("service:mtf")
    _mouse_drag(view, _scene(pixels, 20, 20), _scene(pixels, 110, 110))
    wait_result(controller.mtfController)
    QTest.qWait(60)
    assert max(controller.mtfController.currentResult["x"]["mtf"]) > 2
    assert _find(view, "mtfMetric-1").property("text") == "未达到"
    assert _find(view, "mtfMetric-2").property("text") == "未达到"
    assert "MTF50  X 未达到" in _find(view, "mtfRoiLabel").property("text")
    assert view.grabWindow().save(str(tmp_path / "mtf-response-above-one.png"))
    assert not warnings, warnings


def test_method_and_analysis_selectors_apply_simple_roi_rules(workspace):
    view, controller, pixels, warnings = workspace
    _click(view, _find(view, "primaryTool-service"))
    _click(view, _find(view, "serviceEntry-mtf"))
    bead = _find(view, "mtfMeasurementMethod-bead")
    wire = _find(view, "mtfMeasurementMethod-wire")
    direct = _find(view, "mtfAnalysisMethod-direct_fft")
    gaussian = _find(view, "mtfAnalysisMethod-gaussian")
    assert bead.property("selected") and gaussian.property("selected")
    for label_name, options in [
        ("mtfMeasurementMethodLabel", [bead, wire]),
        ("mtfAnalysisMethodLabel", [direct, gaussian]),
    ]:
        label = _find(view, label_name)
        label_center = label.mapToScene(QPointF(0, label.height() / 2)).y()
        assert all(option.mapToScene(QPointF(0, option.height() / 2)).y()
                   == pytest.approx(label_center) for option in options)

    _mouse_drag(view, _scene(pixels, 8, 8), _scene(pixels, 118, 118))
    wait_result(controller.mtfController)
    roi = controller.mtfController.roiController.measurementItems
    _click(view, direct)
    wait_result(controller.mtfController)
    assert controller.mtfController.roiController.measurementItems == roi
    assert controller.mtfController.analysisMethod == 'direct_fft'
    assert direct.property('selected') and not gaussian.property('selected')
    _click(view, gaussian)
    wait_result(controller.mtfController)
    assert controller.mtfController.roiController.measurementItems == roi
    assert controller.mtfController.analysisMethod == "gaussian"
    assert gaussian.property("selected") and not direct.property("selected")

    _click(view, wire)
    assert controller.mtfController.measurementMethod == "wire"
    assert controller.mtfController.status == "empty"
    assert not controller.mtfController.roiController.measurementItems
    assert wire.property("selected") and not bead.property("selected")
    assert "细丝截面" in _find(view, "mtfStatus").property("text")
    assert not warnings, warnings


@pytest.mark.parametrize("service", ["mtf", "fwhm"])
def test_analysis_badge_moves_without_geometry_or_recalculation(workspace, service):
    view, controller, pixels, warnings = workspace
    controller._tool_controller.selectService("service:"+service)
    _mouse_drag(view, _scene(pixels, 15, 15), _scene(pixels, 105, 105))
    analysis = controller.mtfController if service == "mtf" else controller.fwhmController
    wait_result(analysis)
    before = analysis.roiController.measurementItems[0]["points"]
    result = analysis.currentResult
    revision = analysis._revision
    badge = _find(view, "mtfRoiMetricBadge")
    position = badge.mapToScene(QPointF())
    start = badge.mapToScene(QPointF(badge.width() / 2, badge.height() / 2)).toPoint()
    _mouse_drag(view, start, start + QPointF(-12, -8).toPoint())
    assert analysis.status == "ready"
    assert analysis.currentResult == result
    assert analysis._revision == revision
    assert analysis.roiController.measurementItems[0]["points"] == before
    moved = _find(view, "mtfRoiMetricBadge").mapToScene(QPointF())
    assert moved.x() == pytest.approx(position.x()-12, abs=1)
    assert moved.y() == pytest.approx(position.y()-8, abs=1)
    assert not warnings, warnings


def test_real_mtf_move_resize_escape_delete_and_transform(workspace):
    view, controller, pixels, warnings = workspace
    controller._tool_controller.selectService("service:mtf")
    _mouse_drag(view, _scene(pixels, 15, 15), _scene(pixels, 105, 105))
    wait_result(controller.mtfController)
    original = controller.mtfController.roiController.measurementItems[0]
    _mouse_drag(view, _scene(pixels, 60, 60), _scene(pixels, 65, 64))
    wait_result(controller.mtfController)
    moved = controller.mtfController.roiController.measurementItems[0]
    assert moved["measurementId"] == original["measurementId"]
    assert moved["points"][0]["column"] == pytest.approx(20, abs=.5)
    controller.applyTransformAction("rotate:cw90")
    controller.applyTransformAction("rotate:mirror-h")
    QTest.qWait(40)
    corner = moved["points"][1]
    _mouse_drag(
        view,
        _scene(pixels, corner["column"], corner["row"]),
        _scene(pixels, corner["column"] + 8, corner["row"] + 8),
    )
    wait_result(controller.mtfController)
    result = controller.mtfController.currentResult
    start = _scene(pixels, 60, 60)
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, start)
    QTest.mouseMove(view, start + QPointF(30, 30).toPoint(), 30)
    QTest.qWait(30)
    assert controller.mtfController.status == "editing"
    assert controller.mtfController.currentResult == {}
    assert not any(item.objectName() == "mtfRoiMetricBadge" and item.isVisible()
                   for item in _visual_children(view.rootObject()))
    QTest.keyClick(view, Qt.Key_Escape)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, start)
    assert controller.mtfController.currentResult == result
    assert _find(view, "mtfRoiMetricBadge").isVisible()
    QTest.keyClick(view, Qt.Key_Backspace)
    assert controller.mtfController.status == "empty"
    assert not controller.mtfController.roiController.measurementItems
    assert not warnings, warnings


def test_automatic_weighting_and_live_unit_labels(workspace, tmp_path):
    view, controller, pixels, warnings = workspace
    frame = bead_render(controller)
    t = np.arange(128) - 63.5
    lsf = np.exp(-.5 * (t / 2)**2) - .18 * np.exp(-.5 * ((t - 7) / 2)**2)
    controller.handleRenderResult(replace(frame, modality_pixel=80 + 1000 * np.outer(lsf, lsf)))
    controller._tool_controller.selectService("service:mtf")
    _mouse_drag(view, _scene(pixels, 20, 34), _scene(pixels, 108, 93))
    wait_result(controller.mtfController)
    QTest.qWait(60)
    c = controller.mtfController
    assert c.status == 'ready' and c.actualAnalysisMethod == 'tukey_fft'
    assert _find(view, 'mtfAnalysisMethod-gaussian').property('selected')
    assert '自动' in _find(view, 'mtfActualMethod').property('text')
    assert not any(item.objectName() == 'mtfAnalysisMethod-tukey_fft'
                   for item in _visual_children(view.rootObject()))
    original = c.currentResult
    controller.settingsController.setValue('measurement', 'mtfFrequencyUnit', 'lp/cm')
    QTest.qWait(60)
    chart = _find(view, 'mtfChart')
    assert chart.property('frequencyUnit') == 'lp/cm'
    assert chart.property('axisTitle').endswith('(lp/cm)')
    assert float(_find(view, 'mtfMetric-2').property('text')) == pytest.approx(original['x']['mtf10'] * 10, abs=.005)
    assert 'lp/cm' in _find(view, 'mtfRoiLabel').property('text')
    texts = [item.property('text') for item in _visual_children(_find(view, 'mtfResults'))
             if item.isVisible() and item.property('text')]
    assert 'MTF10\nlp/cm' in texts and not any('FWHM' in text for text in texts)
    assert view.grabWindow().save(str(tmp_path / 'mtf-automatic-weighting-lp-cm.png'))
    print(f'MTF auto / units preview: {tmp_path / "mtf-automatic-weighting-lp-cm.png"}')
    assert not warnings, warnings


@pytest.mark.parametrize('workspace', [(1200, 820), (760, 560)], indirect=True)
def test_quality_notes_only_appear_in_dismissible_info_popup(workspace, tmp_path):
    view, controller, pixels, warnings = workspace
    frame = bead_render(controller)
    data = np.zeros((128, 128)); data[64, 64] = 10; data[64, 63] = data[64, 65] = -2
    controller.handleRenderResult(replace(frame, modality_pixel=data))
    controller.mtfController.setAnalysisMethod('direct_fft')
    controller._tool_controller.selectService('service:mtf')
    _mouse_drag(view, _scene(pixels, 20, 34), _scene(pixels, 108, 93))
    wait_result(controller.mtfController)
    QTest.qWait(50)
    assert not any(item.objectName() == 'mtfAnalysisHint' and item.isVisible()
                   for item in _visual_children(view.rootObject()))
    notes = controller.mtfController.warnings
    # A compound target produces actual multiple-crossing quality notes.
    analysis = controller.mtfController._current_analysis()
    analysis.result = replace(analysis.result, warnings=tuple(notes) + ('X：MTF 多次穿越阈值，取首次下降交点。',))
    controller.mtfController.stateChanged.emit()
    QTest.qWait(40)
    if view.width() < 900:
        flick = _find(view, 'toolDetailFlickable')
        flick.setProperty('contentY', max(0, flick.property('contentHeight') - flick.height()))
        QTest.qWait(40)
    assert not any(item.objectName().startswith('mtfInfoWarning-') and item.isVisible()
                   for item in _visual_children(view.contentItem()))
    _click(view, _find(view, 'mtfInfoButton'))
    QTest.qWait(80)
    assert view.grabWindow().save(str(tmp_path / 'popup-open.png'))
    explanation = next(item for item in _visual_children(view.contentItem())
                       if item.objectName() == 'mtfInfoExplanation' and item.isVisible())
    assert '傅里叶变换' in explanation.property('text')
    note = next(item for item in _visual_children(view.contentItem())
                if item.objectName() == 'mtfInfoWarning-0' and item.isVisible())
    assert note.isVisible()
    assert 0 <= note.mapToScene(QPointF()).x()
    assert note.mapToScene(QPointF(note.width(), 0)).x() <= view.width()
    path = tmp_path / f'mtf-notes-{view.width()}.png'
    assert view.grabWindow().save(str(path))
    print(f'MTF popup preview: {path}')
    QTest.keyClick(view, Qt.Key_Escape)
    QTest.qWait(50)
    assert not note.isVisible()
    _click(view, _find(view, 'mtfInfoButton'))
    QTest.qWait(40)
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, QPointF(4, 4).toPoint())
    QTest.qWait(40)
    assert not note.isVisible()
    assert not warnings, warnings


def test_ramp_metrics_profile_and_live_angle_conversion(workspace, tmp_path):
    view, controller, pixels, warnings = workspace
    controller._tool_controller.selectService('service:mtf')
    _click(view, _find(view, 'serviceEntry-fwhm'))
    _mouse_drag(view, _scene(pixels, 25, 60), _scene(pixels, 102, 67))
    wait_result(controller.fwhmController)
    QTest.qWait(60)
    c = controller.fwhmController
    assert c.status == 'ready' and c.rampDirection == 'x'
    assert not any(item.objectName() in ('rampProfileChart', 'mtfAnalysisMethod-gaussian') and item.isVisible()
                   for item in _visual_children(view.rootObject()))
    assert _find(view, 'rampDirection-x').isVisible()
    assert 'Slice Thickness' in c.roiMetricLabel
    saved_result = c.currentResult
    _click(view, _find(view, 'rampDetailsToggle'))
    assert _find(view, 'rampProfileChart').isVisible()
    assert c.currentResult == saved_result
    assert not any(item.objectName() in ('mtfMetrics', 'mtfChart') and item.isVisible()
                   for item in _visual_children(view.rootObject()))
    fwhm = c.currentResult['ramp']['fwhm']
    assert float(_find(view, 'rampFwhmMetric').property('text')) == pytest.approx(fwhm, abs=.005)
    assert float(_find(view, 'rampThicknessMetric').property('text')) == pytest.approx(fwhm * np.tan(np.deg2rad(23)), abs=.005)
    controller.settingsController.setValue('measurement', 'rampThicknessAngle', 45)
    QTest.qWait(30)
    assert _find(view, 'rampThicknessMetric').property('text') == _find(view, 'rampFwhmMetric').property('text')
    assert '45°' in _find(view, 'mtfRoiLabel').property('text')
    assert view.grabWindow().save(str(tmp_path / 'ramp-thickness.png'))
    print(f'Ramp profile preview: {tmp_path / "ramp-thickness.png"}')
    _click(view, _find(view, 'mtfAnalysisMethod-direct_fft'))
    wait_result(c)
    assert c.actualAnalysisMethod == 'half_height'
    _click(view, _find(view, 'rampDetailsToggle'))
    assert c.actualAnalysisMethod == 'half_height'
    info = _find(view, 'mtfInfoButton')
    assert info.width() == info.height() == 26
    assert info.property('leftPadding') == info.property('rightPadding') == 0
    assert info.property('baseBorderWidth') == 1
    _click(view, _find(view, 'serviceEntry-mtf'))
    assert controller.mtfController.currentResult == {}
    assert c.currentResult['ramp']
    assert not warnings, warnings


def test_mtf_and_fwhm_entries_preserve_independent_ui_state(workspace, tmp_path):
    view, controller, pixels, warnings = workspace
    controller._tool_controller.selectService('service:mtf')
    _mouse_drag(view, _scene(pixels, 20, 20), _scene(pixels, 105, 105))
    wait_result(controller.mtfController)
    QTest.qWait(40)
    mtf_value = controller.mtfController.currentResult
    assert not any(item.property('text') and 'FWHM' in str(item.property('text'))
                   for item in _visual_children(_find(view, 'mtfResults')) if item.isVisible())
    assert not any(item.objectName() == 'mtfMeasurementMethod-ramp' and item.isVisible()
                   for item in _visual_children(_find(view, 'mtfResults')))
    assert view.grabWindow().save(str(tmp_path / 'independent-mtf.png'))
    _click(view, _find(view, 'serviceEntry-fwhm'))
    assert controller.activeInteraction == 'service:fwhm'
    assert _find(view, 'fwhmResults').isVisible()
    _mouse_drag(view, _scene(pixels, 25, 61), _scene(pixels, 102, 66))
    wait_result(controller.fwhmController)
    QTest.qWait(40)
    fwhm_value = controller.fwhmController.currentResult
    assert fwhm_value.get('ramp') and controller.mtfController.currentResult == mtf_value
    assert not any(item.objectName() == 'mtfMeasurementMethod-bead' and item.isVisible()
                   for item in _visual_children(_find(view, 'fwhmResults')))
    assert view.grabWindow().save(str(tmp_path / 'independent-fwhm.png'))
    _click(view, _find(view, 'serviceEntry-mtf'))
    assert controller.mtfController.currentResult == mtf_value
    assert _find(view, 'mtfRoiLabel').property('text') == controller.mtfController.roiMetricLabel
    _click(view, _find(view, 'serviceEntry-fwhm'))
    assert controller.fwhmController.currentResult == fwhm_value
    assert _find(view, 'mtfRoiLabel').property('text') == controller.fwhmController.roiMetricLabel
    controller._tool_controller.resetActiveTool()
    assert controller.fwhmController.currentResult == {} and controller.mtfController.currentResult == mtf_value
    assert not warnings, warnings
