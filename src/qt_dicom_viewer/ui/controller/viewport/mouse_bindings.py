"""Fallback gestures shared by slice, montage and native volume views."""
from PySide6.QtCore import Qt

from qt_dicom_viewer.model import InteractionType


def drag_interaction(active: InteractionType, buttons: int) -> InteractionType:
    """Call after any view-specific binding (e.g. registration) claims a drag.

    The selected tool owns the left button. Right zoom is temporary and never
    changes the selected tool. Preserve the existing middle-button binding.
    """
    if buttons & Qt.MouseButton.LeftButton.value:
        return active or InteractionType.WINDOW
    if buttons & Qt.MouseButton.RightButton.value:
        return InteractionType.ZOOM
    if buttons & Qt.MouseButton.MiddleButton.value:
        return active
    return InteractionType.NONE
