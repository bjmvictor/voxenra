"""Automatic recovery state reflects persisted data, settings, and in-flight edits."""
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QPointF
from PySide6.QtTest import QTest

from qt_dicom_viewer.ui.app_controller import AppController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from qt_dicom_viewer.ui.controller.settings_controller import SettingsController
from qt_dicom_viewer.core.workspace_document import read_document
from test_dicom_tags import qt_app, wait_until
from test_series_sidebar import sidebar_scene
from test_tag_qml import find, click
from test_workspace_persistence import populated_app


def test_recovery_snapshot_status_and_edits_during_save(qt_app, tmp_path, monkeypatch):
    import qt_dicom_viewer.ui.controller.workspace_document_controller as module
    app, _ = populated_app(tmp_path, settings_path=tmp_path / 'display.json')
    manager = app.workspaceDocumentController
    manager._autosave.stop()
    original_write = module.atomic_write
    entered, release = Event(), Event()
    def delayed(path, data):
        entered.set()
        assert release.wait(5)
        original_write(path, data)
    monkeypatch.setattr(module, 'atomic_write', delayed)
    try:
        assert manager.workspaceName == '临时工作区'
        assert manager.automaticRecovery and manager.recoveryState == 'pending'
        manager._save_recovery()
        assert entered.wait(2)
        assert manager.recoveryState == 'saving'
        assert not manager.setAutomaticRecovery(False)
        manager.mark_dirty()
        release.set()
        wait_until(lambda: not manager.busy)
        assert manager.recoveryState == 'pending'  # New edits were not in the first snapshot.
        assert manager.dirty and not manager.path
        manager._save_recovery()
        wait_until(lambda: not manager.busy)
        assert manager.recoveryState == 'saved'
        assert '副本已更新' in manager.recoveryStatusText
        assert '已自动保存' not in manager.message  # Routine feedback belongs to the icon.
        assert manager.recoveryPath == str(tmp_path / 'workspace-recovery.voxworkspace')
        assert read_document(manager.recoveryPath)['tabs']
        good = Path(manager.recoveryPath).read_bytes()
        def fail(*args): raise OSError('磁盘空间不足')
        monkeypatch.setattr(module, 'atomic_write', fail)
        manager.mark_dirty(); manager._save_recovery()
        wait_until(lambda: not manager.busy)
        assert manager.recoveryState == 'error'
        assert '磁盘空间不足' in manager.recoveryStatusText and manager.isError
        assert Path(manager.recoveryPath).read_bytes() == good
        monkeypatch.setattr(module, 'atomic_write', original_write)
        manager._save_recovery(); wait_until(lambda: not manager.busy)
        assert manager.recoveryState == 'saved' and not manager.isError
        assert '失败' not in manager.message
        # Named saves do not mark an older automatic copy as up to date.
        manager.mark_dirty()
        manager.save_to(tmp_path / '复查.voxworkspace')
        wait_until(lambda: not manager.busy)
        assert manager.workspaceName == '复查' and not manager.dirty
        assert manager.recoveryState == 'pending'
        monkeypatch.setattr(module, 'atomic_write', fail)
        manager._save_recovery(); wait_until(lambda: not manager.busy)
        assert manager.recoveryState == 'error'
        assert not manager.dirty  # A backup error does not invalidate the named file we just saved.
    finally:
        release.set()
        app.shutdown()


def test_auto_recovery_switch_persists_without_disabling_manual_workspaces(qt_app, tmp_path, monkeypatch):
    config = tmp_path / 'display.json'
    app, _ = populated_app(tmp_path, settings_path=config)
    manager = app.workspaceDocumentController
    target = tmp_path / 'manual.voxworkspace'
    try:
        manager._save_recovery(); wait_until(lambda: not manager.busy)
        assert Path(manager.recoveryPath).is_file()
        backup = Path(manager.recoveryPath).read_bytes()
        assert manager.setAutomaticRecovery(False)
        assert manager.recoveryState == 'disabled' and not manager._autosave.isActive()
        assert not SettingsController(path=config).section('workspace')['automaticRecovery']
        manager.mark_dirty(); manager._save_recovery()
        assert not manager.busy and Path(manager.recoveryPath).read_bytes() == backup
        assert manager.save_to(target)
        wait_until(lambda: not manager.busy)
        assert not manager.isError and target.is_file()
        assert not manager.dirty
        assert manager.setAutomaticRecovery(True)
        assert not manager.dirty  # The preference is not an edit to the named workspace.
        assert manager._autosave.isActive() and manager.recoveryState == 'pending'
        assert manager.setAutomaticRecovery(False)
        calls = []
        monkeypatch.setattr('qt_dicom_viewer.ui.controller.workspace_document_controller.reveal_path', lambda path: calls.append(path) or True)
        assert manager.openRecoveryDirectory() and calls == [str(tmp_path)]
    finally: app.shutdown()
    assert not (tmp_path / 'workspace-recovery.voxworkspace').exists()  # Normal exit cleans the owned copy.
    fresh = AppController(DicomImageProvider(), settings_path=config)
    try:
        assert not fresh.workspaceDocumentController.automaticRecovery
        assert not fresh.workspaceDocumentController._autosave.isActive()
    finally: fresh.shutdown()
    # Turning off future saves preserves an unhandled recovery file from a previous crash.
    recovery = tmp_path / 'workspace-recovery.voxworkspace'
    recovery.write_bytes(target.read_bytes())
    fresh = AppController(DicomImageProvider(), settings_path=config)
    try:
        controller = fresh.workspaceDocumentController
        assert controller.recoveryAvailable and not controller.automaticRecovery
        assert controller.recoveryState == 'recoverable'
    finally: fresh.shutdown()
    assert recovery.is_file()


def test_recovery_preference_write_failure_keeps_current_setting(qt_app, tmp_path):
    app = AppController(DicomImageProvider(), settings_path=tmp_path / 'display.json')
    try:
        app.settingsController._path = tmp_path  # A directory cannot be replaced by the JSON file.
        controller = app.workspaceDocumentController
        assert not controller.setAutomaticRecovery(False)
        assert controller.automaticRecovery and controller._autosave.isActive()
        assert controller.isError and '保存设置失败' in controller.message
    finally: app.shutdown()


def test_dialog_and_compact_sidebar_share_recovery_icons(sidebar_scene, tmp_path, monkeypatch):
    window, app, _, warnings = sidebar_scene
    manager = app.workspaceDocumentController
    manager._autosave.stop()
    window.resize(1000, 600)
    QTest.qWait(80)
    click(window, find(window, 'sidebarWorkspace'))
    dialog = window.findChild(QObject, 'workspaceDocumentDialog')
    wait_until(lambda: dialog.property('visible'))
    native = dialog.findChild(QObject, 'workspaceDocumentMessage').window()
    icon = dialog.findChild(QObject, 'workspaceRecoveryStatus')
    sidebar_icon = find(window, 'sidebarWorkspaceStatus')
    assert dialog.findChild(QObject, 'workspaceName').property('text') == '临时工作区'
    assert dialog.findChild(QObject, 'workspaceSaveState').property('opacity') == 0
    button = dialog.findChild(QObject, 'saveWorkspace')
    QTest.qWait(80)
    stable = (native.geometry(), button.mapToScene(QPointF()), button.size())
    try:
        for state in ['pending', 'saving', 'saved', 'error', 'disabled']:
            manager._busy = manager._saving_recovery = state == 'saving'
            manager._autosave_enabled = state != 'disabled'
            manager._recovery_dirty = state == 'pending'
            manager._recovery_error = '无法写入恢复副本' if state == 'error' else ''
            manager._last_recovery_at = '12:34:56'
            manager._owns_recovery = True
            manager.changed.emit()
            QTest.qWait(60)
            assert icon.property('status') == sidebar_icon.property('status') == state
            assert icon.property('statusColor') == sidebar_icon.property('statusColor')
            assert (native.geometry(), button.mapToScene(QPointF()), button.size()) == stable
        manager._busy = manager._saving_recovery = False
        manager._recovery_error = ''
        manager._autosave_enabled = True
        manager.changed.emit()
        calls = []
        monkeypatch.setattr('qt_dicom_viewer.ui.controller.workspace_document_controller.reveal_path', lambda path: calls.append(path) or True)
        link = dialog.findChild(QObject, 'workspaceRecoveryLocation')
        click(native, link)
        assert calls == [str(tmp_path)]
        toggle = dialog.findChild(QObject, 'workspaceAutomaticRecovery')
        click(native, toggle)
        assert not manager.automaticRecovery and icon.property('status') == 'disabled'
        click(native, toggle)
        assert manager.automaticRecovery
        assert native.grabWindow().save(str(tmp_path / 'workspace-recovery-status.png'))
        assert native.close()
        sidebar = find(window, 'sidebarContainer')
        for compact in [False, True]:
            sidebar.setProperty('collapsed', compact)
            QTest.qWait(80)
            entry = find(window, 'sidebarWorkspace')
            assert sidebar_icon.isVisible() and sidebar_icon.width() == 12
            assert sidebar_icon.mapToScene(QPointF()).x() >= entry.mapToScene(QPointF()).x()
            assert sidebar_icon.mapToScene(QPointF(12, 12)).x() <= entry.mapToScene(QPointF(entry.width(), entry.height())).x()
            assert window.grabWindow().save(str(tmp_path / f'sidebar-recovery-{compact}.png'))
            click(window, entry)
            wait_until(lambda: dialog.property('visible'))
            assert native.close()
    finally:
        manager._busy = manager._saving_recovery = False
        manager._owns_recovery = False
        manager.changed.emit()
        native.close()
    assert not warnings, warnings
