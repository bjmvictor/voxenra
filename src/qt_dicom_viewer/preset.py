from qt_dicom_viewer.i18n import message as _msg
from qt_dicom_viewer.model import WindowPreset

CT_WINDOW_PRESETS = (
    WindowPreset(
        preset_id="ct-brain",
        label=_msg('text.0000'),
        center=40,
        width=80,
    ),
    WindowPreset(
        preset_id="ct-lung",
        label=_msg('text.0001'),
        center=-600,
        width=1500,
    ),
    WindowPreset(
        preset_id="ct-bone",
        label=_msg('text.0002'),
        center=300,
        width=1500,
    ),
    WindowPreset(
        preset_id="ct-soft-tissue",
        label=_msg('text.0003'),
        center=40,
        width=400,
    ),
)
