"""Cross-platform setup for the real Qt rendering tests."""
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def offscreen_desktop():
    # Use a desktop-sized test surface without changing platform-based skip rules.
    # Explicit caller-supplied screen configurations remain available for QA.
    if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
        yield
        return
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([
        "pytest", "-platform", "offscreen:configfile=" + str(Path(__file__).with_name("qt-offscreen-desktop.json"))])
    yield app


# Windows' offscreen plugin uses FreeType rather than the native font database.
# Point it at installed fonts so PDF and QML tests actually render text.
if sys.platform == "win32" and os.environ.get("QT_QPA_PLATFORM", "").split(":")[0] == "offscreen":
    os.environ.setdefault("QT_QPA_FONTDIR", str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"))
