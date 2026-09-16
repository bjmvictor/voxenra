"""Opt-in UI checks for downloaded public samples; never downloads during tests."""
import os
from pathlib import Path

import pytest
from PySide6.QtTest import QTest

from qt_dicom_viewer.core.dicom_scanner import DicomFolderScanner
from test_pacs_qml import scene
from test_dicom_tags import qt_app, wait_until

ROOT = os.environ.get('VOXENRA_COMPRESSED_SAMPLE_DIR')
pytestmark = pytest.mark.skipif(not ROOT, reason='Set VOXENRA_COMPRESSED_SAMPLE_DIR to public sample folder')
CASES = [
 '01_RLE/MR_single', '02_JPEG_LS_lossless/MR_single',
 '03_JPEG2000_lossless/MR_single', '03_JPEG2000_lossless/MR_large',
 '03_JPEG2000_lossless/CT_693', '04_JPEG2000_lossy/MR_large',
 '05_JPEG_lossless/Grayscale',
]


@pytest.mark.parametrize('folder', CASES)
def test_public_compressed_2d_qml(scene, folder):
    window, app, warnings = scene
    snapshot = list(DicomFolderScanner().scan(Path(ROOT) / folder))[-1]
    assert len(snapshot.series) == 1
    app.panelController.acceptPacsImport(snapshot)
    workspace = app.workspaceController
    wait_until(lambda: workspace.activeViewport is not None and workspace.activeViewport.loadState in ('ready','error'),10000)
    view = workspace.activeViewport
    assert view.loadState == 'ready', view.errorMessage
    assert view.imageSource and view.sliceCount == 1
    initial = view.current_window
    view.applyWindowPreset(initial.center, max(initial.width * .8, .001))
    wait_until(lambda: not view.render_pending)
    QTest.qWait(60)
    assert not warnings, warnings
    output = Path(os.environ.get('VOXENRA_SAMPLE_QA_OUTPUT', 'build/public-compressed-qa'))
    output.mkdir(parents=True,exist_ok=True)
    assert window.grabWindow().save(str(output / (folder.replace('/','-') + '.png')))
