"""Curve geometry and click-based paths share the displayed/exported physical arc."""
from dataclasses import replace
import math
import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from qt_dicom_viewer.core.curve_geometry import sample_curve, curve_length_mm
from qt_dicom_viewer.core.measurement_hit_test import hit_test_outline, hit_test_control_points
from qt_dicom_viewer.core.workspace_state import dumps, loads
from qt_dicom_viewer.model import ImagePoint, MeasurementKind
from qt_dicom_viewer.ui.controller.viewport.controller.measure.measure_controller import MeasurementController
from test_measurement_controller import _context, _position, _drag
from test_measurement_qml import qt_app, viewport, _scene, _visual_children


def click(c, p, context):
    c.tap_at(p, slice_index=0, endpoint_tolerance=1, line_tolerance=.5, context=context)


def test_curve_geometry_physical_spacing_endpoints_and_convergence():
    straight = [ImagePoint(0,0), ImagePoint(10,0), ImagePoint(20,0)]
    assert curve_length_mm(straight, 3, 2) == pytest.approx(40)
    assert curve_length_mm(straight, 0, 2) == 0
    controls = [ImagePoint(0,0), ImagePoint(10,20), ImagePoint(30,-5), ImagePoint(50,10)]
    path = sample_curve(controls)
    assert path[0] == controls[0] and path[-1] == controls[-1]
    assert [path[i*128] for i in range(len(controls))] == controls
    fine = sample_curve(controls, 2048)
    expected = sum(math.hypot((b.column-a.column)*.4, (b.row-a.row)*.9) for a,b in zip(fine,fine[1:]))
    assert curve_length_mm(controls,.9,.4) == pytest.approx(expected,abs=.002)
    assert curve_length_mm(controls,.9,.4) > sum(math.hypot((b.column-a.column)*.4,(b.row-a.row)*.9) for a,b in zip(controls,controls[1:]))


def test_curve_click_preview_edit_copy_and_workspace():
    c=MeasurementController()
    context=replace(_context(),measurement_kind=MeasurementKind.CURVE,endpoint_tolerance=1,line_tolerance=.5)
    controls=[ImagePoint(10,10),ImagePoint(30,40),ImagePoint(60,20)]
    for p in controls:
        click(c,p,context)
        c.preview_at(ImagePoint(p.column+5,p.row+6))
    assert c._active_transaction.draft.points==controls
    assert c.finish_path()
    original=c.committed_measurements[0]
    assert original.kind==MeasurementKind.CURVE and original.length_mm>0
    assert loads(dumps(original))==original
    sampled=sample_curve(original.points)
    assert hit_test_outline(original,sampled[30],.01)
    assert hit_test_control_points(original,sampled[30],.01) is None
    c.begin(_position(30,40),context)
    c.update(_drag(_position(30,40),_position(30,50)))
    c.end(_position(30,50))
    edited=c.committed_measurements[0]
    assert edited.points[1]==ImagePoint(30,50) and edited.length_mm>original.length_mm
    assert c.paste_points(list(edited.points),context)
    assert c.committed_measurements[1].length_mm==edited.length_mm


@pytest.mark.parametrize('kind',['curve','freehand'])
@pytest.mark.parametrize('finish',['enter','double'])
def test_real_click_paths_have_only_clicked_handles(viewport,kind,finish,tmp_path):
    view,controller,layer,warnings=viewport
    controller._tool_controller.selectInteraction('measure:'+kind)
    c=controller._measure_controller
    path=[(25,30),(100,35),(110,95),(35,85)]
    for p in path:
        QTest.mouseClick(view,Qt.LeftButton,Qt.NoModifier,_scene(layer,*p))
        QTest.qWait(30)
        QTest.mouseMove(view,_scene(layer,p[0]+5,p[1]+5),20)
    assert len(c._active_transaction.draft.points)==4
    if finish=='enter':
        QTest.keyClick(view,Qt.Key_Return)
    else:
        QTest.mouseDClick(view,Qt.LeftButton,Qt.NoModifier,_scene(layer,*path[-1]))
    QTest.qWait(50)
    assert len(c.committed_measurements)==1
    item=c.committed_measurements[0]
    assert len(item.points)==4
    if kind=='curve':
        assert item.length_mm>0
        handles=[x for x in _visual_children(view.rootObject()) if x.objectName()=='measurementControlPoint' and x.isVisible()]
        assert len(handles)==4
    assert view.grabWindow().save(str(tmp_path/f'{kind}-{finish}.png'))
    assert not warnings,warnings


def test_drag_does_not_sample_path_and_escape_discards_it(viewport):
    view,controller,layer,warnings=viewport
    controller._tool_controller.selectInteraction('measure:freehand')
    c=controller._measure_controller
    QTest.mousePress(view,Qt.LeftButton,Qt.NoModifier,_scene(layer,20,20))
    for p in [(30,25),(40,35),(50,40)]:
        QTest.mouseMove(view,_scene(layer,*p),20)
    QTest.mouseRelease(view,Qt.LeftButton,Qt.NoModifier,_scene(layer,50,40))
    assert len(c._active_transaction.draft.points)==1
    assert not c.committed_measurements
    QTest.keyClick(view,Qt.Key_Escape)
    assert not c.has_active_transaction and not c.committed_measurements
    assert not warnings,warnings
