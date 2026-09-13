"""One mixed file/directory picker; Qt's native file modes cannot express both."""
from qt_dicom_viewer.i18n import message as _msg, localize

from pathlib import Path

from PySide6.QtCore import QEvent, QDir, QItemSelectionModel, QStandardPaths, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QAbstractItemView, QFileSystemModel, QHBoxLayout, QTreeView, QVBoxLayout
from qt_dicom_viewer.i18n.widgets import QDialog, QLabel, QLineEdit, QPushButton


class ImportFileModel(QFileSystemModel):
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and 0 <= section < 4:
            return localize((_msg('text.0528'), _msg('text.0529'), _msg('text.0165'), _msg('text.0530'))[section])
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.column() == 2 and self.isDir(index):
            return localize(_msg('text.0531'))
        return super().data(index, role)


class LocalImportDialog(QDialog):
    def __init__(self, directory="", parent=None):
        super().__init__(parent)
        self.setObjectName("localImportDialog")
        self.setWindowTitle(_msg('text.0532'))
        self.resize(880, 560)
        self.setMinimumSize(620, 400)
        self.paths = []
        self._directory = ""
        self._apply_theme()
        from qt_dicom_viewer.ui.controller import appearance_controller
        appearance = appearance_controller._current() if appearance_controller._current else None
        if appearance is not None: appearance.changed.connect(self._apply_theme)
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._apply_theme)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        # The native dialog caption owns the only close control on every platform.
        heading = QLabel(_msg('text.0533'))
        heading.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(heading)
        location = QHBoxLayout()
        for title, navigate in (
            (_msg('text.0534'), self.up),
            (_msg('text.0535'), lambda: self.navigate(str(Path.home()))),
            (_msg('text.0536'), lambda: self.navigate("")),
        ):
            button = QPushButton(title)
            button.setAutoDefault(False)
            button.clicked.connect(navigate)
            location.addWidget(button)
        self.path_edit = QLineEdit()
        self.path_edit.setObjectName("importPath")
        self.path_edit.setPlaceholderText(_msg('text.0537'))
        self.path_edit.installEventFilter(self)
        location.addWidget(self.path_edit, 1)
        layout.addLayout(location)
        hint = QLabel(
            _msg('text.0538')
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.model = ImportFileModel(self)
        self.model.setReadOnly(True)
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.view = QTreeView()
        self.view.setObjectName("importFileList")
        self.view.setModel(self.model)
        self.view.setRootIsDecorated(False)
        self.view.setItemsExpandable(False)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.setSortingEnabled(True)
        self.view.sortByColumn(0, Qt.AscendingOrder)
        self.view.setColumnWidth(0, 420)
        self.view.doubleClicked.connect(self.open_item)
        self.view.selectionModel().selectionChanged.connect(self.update_selection)
        layout.addWidget(self.view, 1)
        self.selection_label = QLabel()
        self.selection_label.setObjectName("importSelectionSummary")
        layout.addWidget(self.selection_label)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch(1)
        self.cancel_button = QPushButton(_msg('text.0539'))
        self.cancel_button.setObjectName("importCancel")
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        self.open_button = QPushButton()
        self.open_button.setObjectName("importOpen")
        self.open_button.setMinimumWidth(144)
        self.open_button.setDefault(True)
        self.open_button.clicked.connect(self.accept)
        buttons.addWidget(self.open_button)
        layout.addLayout(buttons)
        initial = (
            directory
            or QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            or str(Path.home())
        )
        self.navigate(initial if Path(initial).is_dir() else str(Path.home()))

    def _apply_theme(self, *_):
        from qt_dicom_viewer.ui.controller.appearance_controller import current_colors
        colors = current_colors()
        style = """
            QDialog { background: @panelBackground; color: @textPrimary; }
            QLabel { color: @textSecondary; }
            QLineEdit, QTreeView { background: @controlBackground; color: @textPrimary;
                border: 1px solid @inputBorder; border-radius: 4px; padding: 5px; }
            QLineEdit:focus, QTreeView:focus { border-color: @focusBorder; }
            QTreeView::item { height: 28px; }
            QTreeView::item:selected { background: @selectionBackground; color: @textPrimary; }
            QHeaderView::section { background: @panelBackgroundStrong; color: @textSecondary;
                padding: 6px; border: none; }
            QPushButton { background: @controlBackground; color: @textPrimary; padding: 7px 12px;
                border: 1px solid @controlBorder; border-radius: 4px; }
            QPushButton:hover { background: @controlHover; border-color: @controlHoverBorder; }
            QPushButton:pressed { background: @controlPressed; }
            QPushButton:focus { border-color: @focusBorder; }
            QPushButton:disabled { color: @textDisabled; }
            QPushButton#importOpen { background: @primaryButtonBackground; color: @textOnPrimary; border-color: @primaryButtonBorder; }
            QPushButton#importOpen:hover { background: @primaryButtonHover; }
            QPushButton#importOpen:pressed { background: @primaryButtonPressed; }
            QPushButton#importOpen:disabled { background: @primaryButtonDisabled; color: @textDisabled; }
        """
        for key in sorted(colors, key=len, reverse=True): style = style.replace('@' + key, colors[key])
        self.setStyleSheet(style)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.ApplicationPaletteChange:
            self._apply_theme()
        if event.type() == QEvent.LanguageChange and hasattr(self, 'model'):
            self.model.headerDataChanged.emit(Qt.Horizontal, 0, 3)
            self.view.viewport().update()

    def eventFilter(self, watched, event):
        if (
            watched is self.path_edit
            and event.type() == QEvent.KeyPress
            and event.key() in (Qt.Key_Return, Qt.Key_Enter)
        ):
            self.open_typed_path()
            return True
        return super().eventFilter(watched, event)

    def selected_paths(self):
        return [
            self.model.filePath(index)
            for index in self.view.selectionModel().selectedRows(0)
        ]

    def navigate(self, directory):
        if directory and not Path(directory).is_dir():
            return
        self._directory = str(Path(directory).resolve()) if directory else ""
        self.model.setRootPath(self._directory)
        self.view.setRootIndex(self.model.index(self._directory))
        self.view.clearSelection()
        self.path_edit.setText(self._directory)
        self.update_selection()

    def up(self):
        if self._directory:
            parent = str(Path(self._directory).parent)
            self.navigate("" if parent == self._directory else parent)

    def open_typed_path(self):
        path = Path(self.path_edit.text()).expanduser()
        if path.is_dir():
            self.navigate(str(path))
        elif path.is_file():
            self.navigate(str(path.parent))
            index = self.model.index(str(path.resolve()))
            self.view.selectionModel().select(
                index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
            )
            self.view.scrollTo(index)
        else:
            self.selection_label.setText(_msg('text.0540'))

    def open_item(self, index):
        if self.model.isDir(index):
            self.navigate(self.model.filePath(index))
        else:
            self.accept()

    def update_selection(self, *_):
        paths = self.selected_paths()
        directories = sum(Path(path).is_dir() for path in paths)
        self.selection_label.setText(
            _msg('text.0541', value1=directories, value2=len(paths) - directories)
            if paths
            else _msg('text.0542')
        )
        self.open_button.setText(_msg('text.0543') if paths else _msg('text.0544'))
        self.open_button.setEnabled(bool(paths or self._directory))

    def accept(self):
        paths = self.selected_paths() or ([self._directory] if self._directory else [])
        if not paths or not all(Path(path).exists() for path in paths):
            self.selection_label.setText(_msg('text.0545'))
            return
        self.paths = paths
        super().accept()


def select_import_paths(directory=""):
    owner = QGuiApplication.focusWindow()
    dialog = LocalImportDialog(directory)
    if owner is not None:
        dialog.winId()
        dialog.windowHandle().setTransientParent(owner)
    try:
        return dialog.paths if dialog.exec() == QDialog.Accepted else []
    finally:
        dialog.deleteLater()
