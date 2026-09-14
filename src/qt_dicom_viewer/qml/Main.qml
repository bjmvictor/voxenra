import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "sections" as Sections
import "sections/center" as CenterSections
import "theme"
import "components" as Components

ApplicationWindow {
    id: window
    property bool detached: false
    property var windowWorkspace: appController.windowManager?.mainWorkspace ?? appController.workspaceController
    readonly property var windowManager: appController.windowManager ?? null
    readonly property var panelController: appController.panelController
    readonly property var workspaceController: window.windowWorkspace
    readonly property var exportController: window.workspaceController.exportController ?? appController.exportController ?? null
    readonly property var pacsController: appController.pacsController ?? null
    readonly property var seriesExportController: appController.seriesExportController ?? null
    readonly property var documentController: appController.workspaceDocumentController ?? null
    readonly property var editHistory: workspaceController.activeTab?.historyController ?? null
    readonly property bool editingText: !!activeFocusItem && activeFocusItem.selectByMouse !== undefined
    readonly property bool hasTabs: workspaceController.tabs.length > 0
    readonly property var viewportController:
        workspaceController.activeViewport
    readonly property var currentTabAllViewports: workspaceController.currentTabAllViewports
    readonly property var toolController: workspaceController.activeTab ? (workspaceController.activeTab.activeToolController ?? workspaceController.activeTab.toolController) : null

    width: detached ? 1000 : 1400
    height: 760
    minimumWidth: detached ? 720 : 1000
    minimumHeight: 600
    readonly property bool nativeTitleBar: Qt.platform.os === "windows"
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint
        | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        | (nativeTitleBar ? 0
            : Qt.WindowFullscreenButtonHint | Qt.ExpandedClientAreaHint | Qt.NoTitleBarBackgroundHint)
    topPadding: header ? header.height : 32
    function toggleFullScreen() {
        if (visibility === Window.FullScreen) showNormal()
        else showFullScreen()
    }
    Shortcut {
        sequence: Qt.platform.os === "osx" ? "Ctrl+Meta+F" : "F11"
        onActivated: window.toggleFullScreen()
    }
    Component.onCompleted: {
        if (typeof appController.configureNativeWindow === "function")
            appController.configureNativeWindow(window)
        window.windowManager?.registerWindow(window.workspaceController.windowId, window)
        if (!window.detached && window.documentController?.automaticRecovery && window.documentController.recoveryAvailable)
            Qt.callLater(() => workspaceDocumentDialog.open())
    }
    visible: !detached
    title: "Voxenra"
    color: Theme.appBackground
    onClosing: close => {
        if (window.windowManager) close.accepted = window.windowManager.requestCloseWindow(window.workspaceController.windowId)
        else if (window.documentController) close.accepted = window.documentController.requestClose()
    }
    onActiveChanged: {
        if (active) window.windowManager?.focusWindow(window.workspaceController.windowId)
    }
    Shortcut {
        sequences: [StandardKey.Close]
        context: Qt.WindowShortcut
        enabled: window.hasTabs && !window.documentController?.busy
        onActivated: window.workspaceController.closeTab(window.workspaceController.activeTabId)
    }
    Shortcut {
        sequence: Qt.platform.os === "osx" ? "Meta+Tab" : "Ctrl+Tab"
        context: Qt.WindowShortcut
        enabled: window.hasTabs && !!window.windowManager
        onActivated: window.workspaceController.cycleTab(1)
    }
    Shortcut {
        sequence: Qt.platform.os === "osx" ? "Meta+Shift+Tab" : "Ctrl+Shift+Tab"
        context: Qt.WindowShortcut
        enabled: window.hasTabs && !!window.windowManager
        onActivated: window.workspaceController.cycleTab(-1)
    }
    Shortcut {
        sequence: "Escape"
        context: Qt.WindowShortcut
        enabled: window.windowManager?.dragging ?? false
        onActivated: window.windowManager.cancelDrag()
    }
    Shortcut {
        sequences: [StandardKey.Save]
        enabled: !!window.documentController && !window.documentController.busy
        onActivated: window.documentController.save()
    }
    Shortcut {
        sequences: [StandardKey.SaveAs]
        enabled: !!window.documentController && !window.documentController.busy
        onActivated: window.documentController.saveAs()
    }
    Shortcut {
        sequence: "Ctrl+Shift+O"
        enabled: !!window.documentController && !window.documentController.busy
        onActivated: window.documentController.open()
    }
    Shortcut {
        objectName: "compareShortcut"
        // Qt maps Ctrl to Command on macOS, and Control on Windows/Linux.
        sequence: "Ctrl+D"
        context: Qt.WindowShortcut
        enabled: !window.editingText && !workspaceDocumentDialog.visible
            && !window.documentController?.busy && !window.panelController.scanning
        onActivated: window.panelController.compareController.requestFromViewport(window.viewportController)
    }
    Shortcut {
        sequences: [StandardKey.Undo]
        context: Qt.WindowShortcut
        enabled: !workspaceDocumentDialog.visible && !window.editingText && !!window.editHistory && window.editHistory.canUndo && !window.documentController?.busy
        onActivated: window.editHistory.undo()
    }
    Shortcut {
        sequences: [StandardKey.Redo]
        context: Qt.WindowShortcut
        enabled: !workspaceDocumentDialog.visible && !window.editingText && !!window.editHistory && window.editHistory.canRedo && !window.documentController?.busy
        onActivated: window.editHistory.redo()
    }
    Sections.WorkspaceDialog {
        id: workspaceDocumentDialog
        controller: window.documentController
        parent: Overlay.overlay
        anchors.centerIn: parent
        onManualRequested: {
            workspaceDocumentDialog.close()
            window.workspaceController.openManual("workspace")
        }
    }
    Connections {
        target: window.documentController
        property bool needsAttention: false
        function onRestored() {
            if (!window.documentController.isError) workspaceDocumentDialog.close()
            if (window.detached) return
            const layout = window.documentController.sidebarLayout
            seriesSidebar.expandedWidth = layout.width
            seriesSidebar.collapsed = layout.collapsed
        }
        function onChanged() {
            const nextAttention = window.documentController.isError || window.documentController.hasMissingSources
            if (nextAttention && !needsAttention && !workspaceDocumentDialog.visible
                    && (!window.windowManager || window.windowManager.focusedWindowId === window.workspaceController.windowId))
                workspaceDocumentDialog.open()
            needsAttention = nextAttention
        }
    }
    Connections {
        target: window.workspaceController
        function onShowDocumentRequested() { workspaceDocumentDialog.open() }
    }

    header: Components.ApplicationTitleBar {
        targetWindow: window
        // Windows owns the only caption, including branding and hit testing.
        visible: !window.nativeTitleBar
        height: visible ? implicitHeight : 0
    }
    Shortcut {
        sequences: [StandardKey.Open]
        enabled: window.pacsController?.localEnabled !== false && !window.panelController.scanning && !window.documentController?.restoring
        onActivated: {
            window.windowManager?.showMainWindow()
            window.panelController.openImportDialog()
        }
    }
    RowLayout {
        id: workspaceRow
        enabled: !window.documentController?.restoring
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        Sections.SidebarContainer {
            id: seriesSidebar
            visible: !window.detached
            Layout.minimumWidth: implicitWidth
            Layout.preferredWidth: implicitWidth
            Layout.maximumWidth: implicitWidth
            Layout.fillHeight: true
            panelController: window.panelController
            pacsController: window.pacsController
            workspaceController: window.workspaceController
            exportController: window.seriesExportController
            documentController: window.documentController
            onExpandedWidthChanged: {
                if (!window.detached) window.documentController?.setSidebarLayout(expandedWidth, collapsed)
            }
            onCollapsedChanged: {
                if (!window.detached) window.documentController?.setSidebarLayout(expandedWidth, collapsed)
            }
        }

        CenterSections.CenterPanel {
            id: centerView
            Layout.minimumWidth: 360
            Layout.fillWidth: true
            Layout.fillHeight: true
            workspaceController: window.workspaceController
            panelController: window.panelController
            pacsController: window.pacsController
            settingsController: appController.settingsController ?? null
            currentTabAllViewports: window.currentTabAllViewports
            viewportController: window.viewportController
        }

        Components.WidthResizeHandle {
            objectName: "rightPanelResizeHandle"
            visible: rightPanel.visible && !rightPanel.collapsed
            Layout.preferredWidth: 8
            Layout.fillHeight: true
            currentWidth: rightPanel.width
            minimumWidth: 220
            maximumWidth: rightPanel.widthLimit
            direction: -1
            onWidthDragged: value => rightPanel.dragWidth = value
            onWidthCommitted: value => {
                appController.settingsController?.setValue("layout", "rightPanelWidth", Math.round(value))
                rightPanel.dragWidth = -1
            }
        }
        Sections.RightPanel {
            id: rightPanel
            property real dragWidth: -1
            readonly property real widthLimit: Math.max(220, Math.min(420,
                workspaceRow.width - (window.detached ? 0 : seriesSidebar.width) - 360 - 8 - workspaceRow.spacing * 3))
            readonly property real desiredWidth: dragWidth >= 0 ? dragWidth
                : (appController.settingsController?.values.layout.rightPanelWidth ?? 250)
            collapsed: appController.settingsController?.values.layout.rightPanelCollapsed ?? false
            onCollapseRequested: appController.settingsController?.setValue("layout", "rightPanelCollapsed", !collapsed)
            readonly property real actualWidth: collapsed ? 44 : Math.min(widthLimit, desiredWidth)
            enabled: !["loading", "error"].includes(window.workspaceController.activeLoadState?.status ?? "")
            onManualRequested: chapter => window.workspaceController.openManual(chapter)
            exportController: window.exportController
            exportItem: centerView.exportItem
            visible: window.hasTabs && ["tag", "settings", "pacs", "manual"].indexOf(window.workspaceController.activeTabType) < 0
            Layout.minimumWidth: visible ? actualWidth : 0
            Layout.preferredWidth: visible ? actualWidth : 0
            Layout.maximumWidth: visible ? actualWidth : 0
            Layout.fillHeight: true
            toolController: window.toolController
            viewportController: window.viewportController
            tabController: visible ? window.workspaceController.activeTab : null
            toolVisible: visible
            // onRotationActionTriggered: action => {
            //     if (window.viewportController) {
            //         window.viewportController.applyTransformAction(action)
            //     }
            // }

        }
    }
    DropArea {
        id: fileDrop
        objectName: "dicomFileDropArea"
        anchors.fill: parent
        enabled: window.pacsController?.localEnabled !== false && !window.documentController?.restoring
        onEntered: drag => {
            if (drag.hasUrls && window.panelController.canImportUrls(drag.urls)
                    && (drag.supportedActions & Qt.CopyAction)) drag.accept(Qt.CopyAction)
            else drag.accepted = false
        }
        onDropped: drop => {
            if (drop.hasUrls && (drop.supportedActions & Qt.CopyAction)
                    && window.panelController.importUrls(drop.urls)) {
                window.windowManager?.showMainWindow()
                drop.accept(Qt.CopyAction)
            }
            else drop.accepted = false
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: 10
            visible: fileDrop.containsDrag
            color: "#b3101d27"
            border.width: 2
            border.color: Theme.primaryColor
            radius: 8
            Column {
                anchors.centerIn: parent
                spacing: 8
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: qsTrId("text.0609"); color: Theme.textPrimary; font.pixelSize: 22 }
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: qsTrId("text.0610"); color: Theme.textMuted; font.pixelSize: 13 }
            }
        }
    }
    Loader {
        active: !window.detached
        sourceComponent: Item {
            Sections.ImportTaskDialog { controller: window.panelController }
            Sections.ExportDialog {
                controller: window.seriesExportController
                settingsController: appController.settingsController ?? null
                onManualRequested: window.workspaceController.openManual("export")
            }
        }
    }
    CenterSections.TabDragPreview {
        manager: window.windowManager
        sourceWindowId: window.workspaceController.windowId ?? "main"
    }
    Components.AppDialog {
        id: tabMoveError
        objectName: "tabMoveError"
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(440, window.width - 32)
        title: qsTrId("tabs.moveFailed")
        popupType: Popup.Window
    }
    Connections {
        target: window.windowManager
        function onOperationFailed(message) {
            if (window.windowManager.focusedWindowId === window.workspaceController.windowId)
                tabMoveError.open()
        }
    }
}
