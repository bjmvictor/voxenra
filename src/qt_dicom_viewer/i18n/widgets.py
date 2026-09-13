"""App-owned widget text bindings; native file pickers translate on their next opening."""
from PySide6 import QtWidgets
from PySide6.QtCore import QEvent
from .messages import Message, JoinedMessage, localize, message


class TextBindings:
    def _bind(self, name, value):
        if not hasattr(self, '_texts'): self._texts = {}
        if isinstance(value, (Message, JoinedMessage)): self._texts[name] = value
        else: self._texts.pop(name, None)
        getattr(super(), name)(localize(value))

    def setText(self, value): self._bind('setText', value)
    def setWindowTitle(self, value): self._bind('setWindowTitle', value)
    def setToolTip(self, value): self._bind('setToolTip', value)
    def setPlaceholderText(self, value): self._bind('setPlaceholderText', value)
    def setInformativeText(self, value): self._bind('setInformativeText', value)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.LanguageChange:
            self.retranslate()

    def retranslate(self):
        for setter, source in getattr(self, '_texts', {}).items():
            getattr(super(), setter)(localize(source))
        if isinstance(self, QtWidgets.QMessageBox): self._translate_buttons()


def _text_widget(base):
    class BoundWidget(TextBindings, base):
        def __init__(self, *args, **kwargs):
            super().__init__(*(localize(arg) for arg in args), **kwargs)
            if args and isinstance(args[0], (Message, JoinedMessage)):
                self._texts = {'setText': args[0]}
    BoundWidget.__name__ = base.__name__
    return BoundWidget


QLabel = _text_widget(QtWidgets.QLabel)
QPushButton = _text_widget(QtWidgets.QPushButton)
QCheckBox = _text_widget(QtWidgets.QCheckBox)
QLineEdit = _text_widget(QtWidgets.QLineEdit)


class QDialog(TextBindings, QtWidgets.QDialog):
    pass


class QMessageBox(TextBindings, QtWidgets.QMessageBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*(localize(arg) for arg in args), **kwargs)
        self._texts = {}
        if len(args) >= 3:
            self._texts = {'setWindowTitle': args[1], 'setText': args[2]}
        self._translate_buttons()

    def _translate_buttons(self):
        for key, id_ in {QtWidgets.QMessageBox.StandardButton.Save: 'text.1092', QtWidgets.QMessageBox.StandardButton.Discard: 'common.dontSave',
                         QtWidgets.QMessageBox.StandardButton.Cancel: 'text.0539', QtWidgets.QMessageBox.StandardButton.Close: 'text.0621',
                         QtWidgets.QMessageBox.StandardButton.Ok: 'common.ok', QtWidgets.QMessageBox.StandardButton.Yes: 'common.yes', QtWidgets.QMessageBox.StandardButton.No: 'common.no',
                         QtWidgets.QMessageBox.StandardButton.Retry: 'common.retry'}.items():
            button = self.button(key)
            if button is not None: button.setText(localize(message(id_)))

    def setStandardButtons(self, buttons):
        super().setStandardButtons(buttons)
        self._translate_buttons()

    @staticmethod
    def question(parent, title, text, buttons=QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                 defaultButton=QtWidgets.QMessageBox.StandardButton.NoButton):
        # Qt's static helper would construct an unbound base QMessageBox.
        dialog = QMessageBox(QtWidgets.QMessageBox.Icon.Question, title, text, buttons, parent)
        if defaultButton != QtWidgets.QMessageBox.StandardButton.NoButton:
            dialog.setDefaultButton(defaultButton)
        try:
            return QtWidgets.QMessageBox.StandardButton(dialog.exec())
        finally:
            dialog.deleteLater()


class QFileDialog(QtWidgets.QFileDialog):
    @staticmethod
    def getSaveFileName(*args, **kwargs):
        return QtWidgets.QFileDialog.getSaveFileName(*(localize(v) for v in args), **kwargs)
    @staticmethod
    def getOpenFileName(*args, **kwargs):
        return QtWidgets.QFileDialog.getOpenFileName(*(localize(v) for v in args), **kwargs)
    @staticmethod
    def getOpenFileNames(*args, **kwargs):
        return QtWidgets.QFileDialog.getOpenFileNames(*(localize(v) for v in args), **kwargs)
    @staticmethod
    def getExistingDirectory(*args, **kwargs):
        return QtWidgets.QFileDialog.getExistingDirectory(*(localize(v) for v in args), **kwargs)
