"""Pointer movement for hover checks on both native and offscreen Qt windows."""
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtTest import QTest


def move_pointer(window, position):
    # Cocoa resynchronizes hover with the physical cursor when popup windows
    # appear. Keep it aligned with Qt's synthetic events during native tests.
    if QGuiApplication.platformName() == 'cocoa':
        QCursor.setPos(window.mapToGlobal(position))
    QTest.mouseMove(window, position)
