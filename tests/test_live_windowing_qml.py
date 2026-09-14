"""Held mouse gestures must change the rendered comparison images in QML."""
import numpy as np
import pytest
from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

from test_dicom_tags import qt_app
from test_series_sidebar import sidebar_scene
from test_tag_qml import find
from test_compare_2d import open_pair as open_2d_pair
from test_compare_mpr import open_pair as open_mpr_pair
from test_live_windowing import pause_worker, assert_live_labels


def center_pixels(window, canvas):
    # Exclude changing WW/WL text, border, and the held cursor. The central
    # image must repaint, so updating labels/source strings alone cannot pass.
    image = window.grabWindow()
    scale = image.devicePixelRatio()
    start = canvas.mapToScene(QPointF(canvas.width()*.32, canvas.height()*.32))
    image = image.copy(QRect(round(start.x()*scale), round(start.y()*scale),
                            round(canvas.width()*.36*scale), round(canvas.height()*.36*scale)))
    image = image.convertToFormat(QImage.Format_RGBA8888)
    return np.frombuffer(image.constBits(), np.uint8).copy()


@pytest.mark.parametrize('mpr', [False, True])
def test_qml_comparison_repaints_all_images_while_mouse_remains_pressed(sidebar_scene, tmp_path, mpr):
    window, app, records, warnings = sidebar_scene
    window.resize(1440, 900)
    tab = open_mpr_pair(app, records) if mpr else open_2d_pair(app, records)[0]
    if mpr:
        tab.setLink('window', True)
    views = list(tab.viewports_by_id.values())
    source = views[0]
    tab.activateViewport(source.viewportId)
    source._tool_controller.activateTool('window')
    pause_worker(app)
    QTest.qWait(80)
    canvases = [find(window, 'imageViewport-' + v.viewportId) for v in views]
    canvas = canvases[0]
    start = canvas.mapToScene(QPointF(canvas.width()*.12, canvas.height()*.18)).toPoint()
    original = [center_pixels(window, c) for c in canvases]
    assert window.grabWindow().save(str(tmp_path/'before-window-drag.png'))
    QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
    try:
        # Cross Qt's drag threshold, then require repeated image changes.
        QTest.mouseMove(window, start + QPoint(12, 8), 20)
        QTest.qWait(30)
        previous = [center_pixels(window, c) for c in canvases]
        for step in range(2, 6):
            QTest.mouseMove(window, start + QPoint(12*step, 8*step), 20)
            QTest.qWait(30)
            current = [center_pixels(window, c) for c in canvases]
            for view in views:
                assert_live_labels(view)
            for before, after in zip(previous, current):
                assert before.shape == after.shape
                assert np.any(before != after), 'Peer image froze during the held drag'
            previous = current
        assert all(np.any(before != after) for before, after in zip(original, previous))
        assert source._active_drag_operation is not None
        assert window.grabWindow().save(str(tmp_path/'held-window-drag.png'))
    finally:
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, start + QPoint(60, 40))
    assert not warnings, warnings
