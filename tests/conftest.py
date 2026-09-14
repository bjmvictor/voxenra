"""Cross-platform setup for the real Qt rendering tests."""
import os
from pathlib import Path
import sys


# Windows' offscreen plugin uses FreeType rather than the native font database.
# Point it at installed fonts so PDF and QML tests actually render text.
if sys.platform == "win32" and os.environ.get("QT_QPA_PLATFORM", "").split(":")[0] == "offscreen":
    os.environ.setdefault("QT_QPA_FONTDIR", str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"))
