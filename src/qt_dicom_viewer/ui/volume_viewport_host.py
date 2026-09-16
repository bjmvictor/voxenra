"""Native QWidget content for the QML WindowContainer; never a second app window."""
from qt_dicom_viewer.i18n.messages import error_message
from qt_dicom_viewer.i18n import message as _msg
import logging

from PySide6.QtCore import QEvent, QTimer, Qt, Slot, QThreadPool
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qt_dicom_viewer.ui.volume_render_backend import VolumeRenderBackend
from qt_dicom_viewer.ui.cursors import tool_cursor
from qt_dicom_viewer.ui.workers.volume_edit_task import VolumeEditTask
from qt_dicom_viewer.i18n.widgets import QLabel, QPushButton

logger = logging.getLogger(__name__)


class VolumeInteractor(QVTKRenderWindowInteractor):
    def __init__(self, host):
        self.host = host
        self._drag_button = Qt.NoButton
        super().__init__(host)
        self.setAcceptDrops(True)

    def _getPixelRatio(self):
        # VTK's default follows the cursor's screen, which can differ from the
        # embedded window's screen on mixed-DPI desktops.
        return self.devicePixelRatioF()

    def event(self, event):
        handled = super().event(event)
        if event.type() == QEvent.DevicePixelRatioChange and "_RenderWindow" in self.__dict__:
            self.resizeEvent(None)
            if getattr(self.host, "vtk_widget", None) is self:
                self.host._update_cursor()
        return handled

    def paintEvent(self, event):
        # Rendering from the native paint callback can deadlock Cocoa when its
        # parent is a QQuickWindow. Render only from the host's coalescing timer.
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.host.controller.viewport_resized()
        self.host.request_render()

    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton) and self._drag_button == Qt.NoButton:
            self._drag_button = event.button()
            self.setFocus(Qt.MouseFocusReason)
            p = event.position()
            self.host.controller.begin_drag((p.x(), p.y()), (self.width(), self.height()), event.button().value)
            self.host._update_cursor()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_button != Qt.NoButton and event.buttons() & self._drag_button:
            p = event.position()
            self.host.controller.update_drag((p.x(), p.y()))
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._drag_button != Qt.NoButton and event.button() == self._drag_button:
            self._drag_button = Qt.NoButton
            p = event.position()
            self.host.controller.update_drag((p.x(), p.y()))
            self.host.controller.end_drag()
            self.host._update_cursor()
            event.accept()

    def wheelEvent(self, event):
        self.host.controller.wheel_zoom(event.angleDelta().y(), event.pixelDelta().y())
        event.accept()

    def keyPressEvent(self, event):
        QWidget.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        QWidget.keyReleaseEvent(self, event)

    def focusOutEvent(self, event):
        # Focus loss must never commit an unfinished stroke. A crop already
        # dispatched on mouse release continues independently of keyboard focus.
        self._drag_button = Qt.NoButton
        self.host.controller.cancel_drag()
        self.host._update_cursor()
        super().focusOutEvent(event)


class VolumeViewportHost(QWidget):
    def __init__(self, controller, backend_factory=VolumeRenderBackend):
        super().__init__(None, Qt.FramelessWindowHint)
        self.controller = controller
        self._active = False
        self._disposed = False
        self._dirty = False
        self._interactive = False
        self._prepared_key = None
        self._presented_key = None
        self._preparing_key = None
        self._prepare_token = 0
        self._prepare_task = None
        self._exposed_windows = set()
        self.setAttribute(Qt.WA_NativeWindow)
        # Mark an explicit initial size so QWidget.show() cannot replace the
        # container's geometry with a sizeHint when first attached.
        self.resize(640, 480)
        self.setStyleSheet("QWidget { background: #02070e; color: #eaf3fb; }"
                           "QPushButton { padding: 8px 20px; background: #17354a; border-radius: 4px; }")
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._render)
        self._settle = QTimer(self)
        self._settle.setSingleShot(True)
        self._settle.setInterval(160)
        self._settle.timeout.connect(lambda: self.request_render(False))
        self.stack = QStackedLayout(self)
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.status_page = QWidget(self)
        status_layout = QVBoxLayout(self.status_page)
        status_layout.addStretch()
        self.message = QLabel(_msg('text.0008'), self.status_page)
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.message)
        self.retry_button = QPushButton(_msg('text.0009'), self.status_page)
        self.retry_button.clicked.connect(controller.retry)
        status_layout.addWidget(self.retry_button, alignment=Qt.AlignCenter)
        status_layout.addStretch()
        self.stack.addWidget(self.status_page)
        self.vtk_widget = VolumeInteractor(self)
        self.stack.addWidget(self.vtk_widget)
        self.backend = backend_factory(self.vtk_widget)
        self.winId()
        self.windowHandle().installEventFilter(self)
        self.vtk_widget.windowHandle().installEventFilter(self)
        controller.stateChanged.connect(self._state_changed)
        controller.displayStateChanged.connect(self._state_changed)
        controller.maskChanged.connect(self._state_changed)
        controller.selectionChanged.connect(self._selection_changed)
        controller.loadStateChanged.connect(self.sync_status)
        controller.activeInteractionChanged.connect(self._update_cursor)
        if hasattr(controller, "referenceChanged"):
            controller.referenceChanged.connect(self._reference_changed)
        self._update_cursor()

    def _reference_changed(self):
        if not self._disposed:
            self.request_render(True)

    def _update_cursor(self):
        interaction = (self.controller._drag[-1] if self.controller._drag is not None
                       else self.controller.activeInteraction)
        kind = {"pan": "pan", "zoom": "zoom", "window": "window",
                "volume:crop": "volume-crop", "volume:rotate": "rotate-3d"}.get(
                    interaction or "window")
        self.vtk_widget.setCursor(tool_cursor(kind, self.vtk_widget.devicePixelRatioF())
                                  if kind else Qt.ArrowCursor)

    def _selection_changed(self):
        if self._disposed:
            return
        self.backend.set_selection(self.controller.selection_points, self.controller._selection_size)
        self.request_render()

    def _state_changed(self):
        self.request_render(True)
        self._settle.start()

    def set_active(self, active):
        if self._disposed:
            return
        self._active = active
        if active:
            # WindowContainer must attach the native window before QWidget.show().
            # Do not fetch parent() into Python: PySide can parent the returned
            # QQuickWindow wrapper to this child and invalidate it on disposal.
            if not self.windowHandle().isTopLevel():
                self.show()
                self.sync_status()
                self.request_render()
        else:
            self._timer.stop()
            self._settle.stop()
            self.hide()

    def sync_status(self):
        if self._disposed:
            return
        if self.controller.loadState == "ready":
            key = self.backend.preparation_key(self.controller.volume)
            if key == self._prepared_key:
                self.stack.setCurrentWidget(self.vtk_widget)
                self.request_render()
                return
            # During temporal playback retain the last completed 3D frame
            # while preparing the next phase. Showing the loading page for
            # every phase makes the native surface flash throughout playback.
            owner = getattr(self.controller, "_layout_owner", None)
            keep_frame = (owner is not None and owner.tab.temporalPlayback
                          and self._presented_key is not None)
            if not keep_frame:
                self.stack.setCurrentWidget(self.status_page)
            self.message.setText(_msg('text.0011'))
            self.retry_button.setVisible(False)
            if not self._active or key == self._preparing_key:
                return
            self._prepare_token += 1
            self._preparing_key = key
            function, args = self.backend.preparation_request(self.controller.volume)
            task = VolumeEditTask(self._prepare_token, "prepare", function, *args)
            task.signals.finished.connect(self._preparation_finished, Qt.QueuedConnection)
            self._prepare_task = task
            QThreadPool.globalInstance().start(task)
        else:
            self._prepare_token += 1
            self._preparing_key = None
            self._prepare_task = None
            self.stack.setCurrentWidget(self.status_page)
            failed = self.controller.loadState == "error"
            self.message.setText(_msg('text.0010')+self.controller.errorMessage
                                 if failed else _msg('text.0011'))
            self.retry_button.setVisible(failed)

    @Slot(int, str, object, object)
    def _preparation_finished(self, token, kind, prepared, error):
        if self._disposed or token != self._prepare_token:
            return
        key, self._preparing_key = self._preparing_key, None
        self._prepare_task = None
        if (self.controller.loadState != "ready"
                or key != self.backend.preparation_key(self.controller.volume)):
            self.sync_status()
            return
        if error:
            self.controller.render_failed(error)
            return
        try:
            self.backend.set_volume(self.controller.volume, prepared)
            self._prepared_key = key
            self.stack.setCurrentWidget(self.vtk_widget)
            self.request_render()
        except Exception as error:
            logger.exception("Could not prepare VTK volume")
            self.controller.render_failed(error_message(error))

    @property
    def data_ready(self):
        return (not self._disposed and self.controller.loadState == "ready"
                and self._prepared_key == self.backend.preparation_key(self.controller.volume))

    @property
    def frame_ready(self):
        """The current volume has reached the native render window, not just VTK."""
        return self.data_ready and self._presented_key == self._prepared_key

    def request_render(self, interactive=False):
        if self._disposed:
            return
        self._dirty = True
        self._interactive = interactive
        if self._active and not self._timer.isActive():
            self._timer.start()

    def _render(self):
        if (self._disposed or not self._active or not self._dirty
                or self.controller.loadState != "ready"
                or not self.windowHandle().isExposed()):
            return
        if self._prepared_key != self.backend.preparation_key(self.controller.volume):
            self.sync_status()
            return
        self._dirty = False
        try:
            owner = getattr(self.controller, "_layout_owner", None)
            if owner is not None:
                from qt_dicom_viewer.ui.mpr_reference_overlay import MprReferenceOverlay
                if not hasattr(self.backend, "mpr_reference"):
                    self.backend.mpr_reference = MprReferenceOverlay(self.backend.renderer)
                settings = owner._tools.settingsController.values["crosshair"]
                self.backend.mpr_reference.configure_title(owner._tools.settingsController.values["corners"])
                self.backend.mpr_reference.update(self.controller.volume.geometry,
                    owner.tab._target_mpr_state, owner.referenceMode,
                    [settings[key + "Color"] for key in ("axial", "coronal", "sagittal")])
            self.backend.render(self.controller.state, self._interactive, self.controller.display_state,
                                self.controller.visible_mask)
            self._presented_key = self._prepared_key
        except Exception as error:
            logger.exception("VTK rendering failed")
            self.controller.render_failed(error_message(error))

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Expose:
            # Cocoa can emit Expose after every buffer swap. Scheduling a
            # render for every such event creates an endless redraw loop.
            # State/resize changes already request their own renders.
            if watched.isExposed():
                if watched not in self._exposed_windows:
                    self._exposed_windows.add(watched)
                    self.request_render()
            else:
                self._exposed_windows.discard(watched)
        return super().eventFilter(watched, event)

    def dispose(self):
        if self._disposed:
            return
        self._disposed = True
        self._prepare_token += 1
        self._prepare_task = None
        self._exposed_windows.clear()
        self._timer.stop()
        self._settle.stop()
        self.controller.stateChanged.disconnect(self._state_changed)
        self.controller.displayStateChanged.disconnect(self._state_changed)
        self.controller.maskChanged.disconnect(self._state_changed)
        self.controller.selectionChanged.disconnect(self._selection_changed)
        self.controller.loadStateChanged.disconnect(self.sync_status)
        self.controller.activeInteractionChanged.disconnect(self._update_cursor)
        if hasattr(self.controller, "referenceChanged"):
            self.controller.referenceChanged.disconnect(self._reference_changed)
        self.vtk_widget.DestroyTimer(None, None)
        self.backend.dispose()
        self.hide()
        self.deleteLater()
