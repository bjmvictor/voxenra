"""Theme-aware exit confirmation for new and existing workspace documents."""
from PySide6.QtCore import QEvent, QTimer, Qt

from qt_dicom_viewer.i18n import localize, message as _msg
from qt_dicom_viewer.i18n.widgets import QCheckBox, QMessageBox


class WorkspaceExitDialog(QMessageBox):
    def __init__(self, appearance, *, workspace_name=""):
        self._workspace_name = workspace_name
        super().__init__(QMessageBox.NoIcon, _msg('workspace.exit.title'),
                         _msg('workspace.exit.updateQuestion', name=workspace_name)
                         if workspace_name else _msg('text.0433'),
                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        self.setObjectName("workspaceExitConfirmation")
        self._button_text_timer = QTimer(self)
        self._button_text_timer.setSingleShot(True)
        self._button_text_timer.timeout.connect(self._translate_buttons)
        # A platform-native alert can ignore the application's selected palette.
        self.setOption(QMessageBox.Option.DontUseNativeDialog, True)
        self.setTextFormat(Qt.PlainText)
        self.setInformativeText(_msg('workspace.exit.updateDetails') if workspace_name
                                else _msg('workspace.exit.saveDetails'))
        self.button(QMessageBox.Save).setObjectName("workspaceExitSave")
        self.setDefaultButton(QMessageBox.Save)
        self.setEscapeButton(QMessageBox.Cancel)
        remember = QCheckBox(_msg('text.0435'), self)
        remember.setObjectName("rememberWorkspaceExit")
        remember.setToolTip(_msg('text.0434'))
        self.setCheckBox(remember)
        self._appearance = appearance
        appearance.changed.connect(self._apply_theme)
        self._apply_theme()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.LanguageChange and hasattr(self, '_button_text_timer'):
            # QDialogButtonBox may reset its standard labels in a queued event.
            self._button_text_timer.start(0)

    def _translate_buttons(self):
        super()._translate_buttons()
        for role, key in (
            (QMessageBox.Save, 'workspace.exit.update' if self._workspace_name else 'workspace.exit.save'),
            (QMessageBox.Discard, 'workspace.exit.dontUpdate' if self._workspace_name else 'common.dontSave'),
            (QMessageBox.Cancel, 'workspace.exit.cancel'),
        ):
            button = self.button(role)
            if button is not None:
                button.setText(localize(_msg(key)))

    def _apply_theme(self):
        style = """
            QMessageBox { background: @panelBackground; color: @textPrimary; }
            QLabel, QCheckBox { color: @textPrimary; background: transparent; }
            QLabel#qt_msgbox_informativelabel { color: @textSecondary; }
            QCheckBox { spacing: 8px; }
            QPushButton { background: @controlBackground; color: @textPrimary;
                border: 1px solid @controlBorder; border-radius: 4px; padding: 7px 14px; }
            QPushButton:hover { background: @controlHover; border-color: @controlHoverBorder; }
            QPushButton:pressed { background: @controlPressed; }
            QPushButton:focus { border-color: @focusBorder; }
            QPushButton#workspaceExitSave { background: @primaryButtonBackground;
                color: @textOnPrimary; border-color: @primaryButtonBorder; }
            QPushButton#workspaceExitSave:hover { background: @primaryButtonHover; }
            QPushButton#workspaceExitSave:pressed { background: @primaryButtonPressed; }
        """
        colors = self._appearance.colors
        for key in sorted(colors, key=len, reverse=True):
            style = style.replace('@' + key, colors[key])
        self.setStyleSheet(style)
