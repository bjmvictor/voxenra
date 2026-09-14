"""Patient-space slice outlines and an always-visible screen-space locator."""
import numpy as np
from PySide6.QtGui import QColor
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkCellArray
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkActor2D, vtkPolyDataMapper2D

from qt_dicom_viewer.core.mpr_layout import plane_box_intersection


class MprReferenceOverlay:
    def __init__(self, renderer):
        self.renderer = renderer
        self._key = None
        self.center = None
        self.planes = []
        for _ in range(3):
            data, mapper, actor = vtkPolyData(), vtkPolyDataMapper(), vtkActor()
            mapper.SetInputData(data)
            actor.SetMapper(mapper)
            actor.GetProperty().LightingOff()
            actor.GetProperty().SetLineWidth(2)
            actor.SetVisibility(False)
            renderer.AddActor(actor)
            self.planes.append((data, actor))
        self.marker_data, mapper, self.marker = vtkPolyData(), vtkPolyDataMapper2D(), vtkActor2D()
        mapper.SetInputData(self.marker_data)
        self.marker.SetMapper(mapper)
        self.marker.GetProperty().SetColor(0.15, 0.8, 1.0)
        self.marker.GetProperty().SetLineWidth(2)
        self.marker.SetVisibility(False)
        renderer.AddViewProp(self.marker)

    def update(self, geometry, state, mode, colors):
        frame = state.frame if state is not None else None
        key = (id(geometry), frame, mode, tuple(colors))
        if key == self._key:
            return
        self._key = key
        self.center = frame.center_patient if frame is not None and mode != "hidden" else None
        # Axial normal W, coronal normal V, sagittal normal U.
        normals = (frame.w_direction_patient, frame.v_direction_patient, frame.u_direction_patient) if frame else ()
        for index, (data, actor) in enumerate(self.planes):
            polygon = plane_box_intersection(geometry, frame.center_patient, normals[index]) \
                if frame is not None and geometry is not None and mode == "planes" else ()
            actor.SetVisibility(bool(polygon))
            if not polygon:
                continue
            vertices, lines = vtkPoints(), vtkCellArray()
            for point in polygon:
                vertices.InsertNextPoint(*point)
            lines.InsertNextCell(len(polygon) + 1)
            for i in range(len(polygon)):
                lines.InsertCellPoint(i)
            lines.InsertCellPoint(0)
            data.SetPoints(vertices)
            data.SetLines(lines)
            data.Modified()
            color = QColor(colors[index])
            actor.GetProperty().SetColor(color.redF(), color.greenF(), color.blueF())

    def project_marker(self, pixel_ratio=1.0):
        if self.center is None:
            self.marker.SetVisibility(False)
            return
        self.renderer.SetWorldPoint(*self.center, 1.0)
        self.renderer.WorldToDisplay()
        x, y, depth = self.renderer.GetDisplayPoint()
        width, height = self.renderer.GetRenderWindow().GetSize()
        self.marker.SetVisibility(0 <= x <= width and 0 <= y <= height and 0 <= depth <= 1)
        vertices, lines = vtkPoints(), vtkCellArray()
        radius = 7 * pixel_ratio
        for angle in np.linspace(0, 2*np.pi, 32, endpoint=False):
            vertices.InsertNextPoint(x+radius*np.cos(angle), y+radius*np.sin(angle), 0)
        lines.InsertNextCell(33)
        for index in range(32):
            lines.InsertCellPoint(index)
        lines.InsertCellPoint(0)
        self.marker_data.SetPoints(vertices)
        self.marker_data.SetLines(lines)
        self.marker_data.Modified()
