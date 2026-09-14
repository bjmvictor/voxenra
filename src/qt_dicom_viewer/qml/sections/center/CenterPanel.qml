pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import 'viewportArea' as ViewportSection
import "../../theme"
import "../settings" as Settings
import "../pacs" as Pacs
import "../manual" as Manual
import "../../components" as Components

Rectangle {
    id: centerPanel

    required property var workspaceController
    required property var panelController
    property var pacsController: null
    property var settingsController: null
    required property var viewportController
    required property var currentTabAllViewports
    readonly property var windowManager: workspaceController.windowManager ?? null

    readonly property var opening: workspaceController.activeLoadState
    readonly property bool imageWorkspace: ["2d", "compare2d", "comparempr", "mpr", "4d", "petctfusion"].includes(workspaceController.activeTabType)

    readonly property Item exportItem: workspaceLoader.item
        ? (workspaceLoader.item.activeExportItem !== undefined ? workspaceLoader.item.activeExportItem() : workspaceLoader.item) : null

    readonly property bool hasTabs:
        workspaceController.tabs.length > 0

    color: Theme.workspaceBackground
    radius: 8
    clip: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: centerPanel.hasTabs || (centerPanel.windowManager?.dragging ?? false)

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            Layout.minimumHeight: 36
            Layout.maximumHeight: 36
            // 标签栏与诊断视口属于不同层级，保留明确的背景间隔，
            // 避免两个 active 状态在交界处拼成同一条边框。
            Layout.bottomMargin: 10
            TabBarSection {
                Layout.fillWidth: true
                Layout.fillHeight: true
                workspaceController: centerPanel.workspaceController
            }
            Components.AppButton {
                objectName: "showMainWindow"
                visible: centerPanel.workspaceController.detached === true
                Layout.preferredWidth: 36
                Layout.preferredHeight: 32
                compact: true
                iconName: "workspace"
                Accessible.name: qsTrId("tabs.showMain")
                onClicked: centerPanel.windowManager.showMainWindow()
                Components.AppToolTip { visible: parent.hovered; text: qsTrId("tabs.showMain") }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Loader {
                id: workspaceLoader
                objectName: "workspaceLoader"
                anchors.fill: parent
                asynchronous: true
                active: false
                property var loadedTab: null
                visible: status === Loader.Ready
                onStatusChanged: {
                    const nativePresentation = centerPanel.workspaceController.activeTabType === "3d"
                        && centerPanel.viewportController?.loadState === "ready"
                    if (loadedTab && (status === Loader.Error || (status === Loader.Ready && !nativePresentation)))
                        centerPanel.windowManager?.pageReady(centerPanel.workspaceController.windowId,
                            centerPanel.workspaceController.activeTabId, status === Loader.Ready)
                }
                function openCurrentTab() {
                    // Cancel the previous incubation before selecting another component.
                    // Binding sourceComponent directly to activeTabType can briefly start
                    // loading the next page during the same active-tab signal delivery.
                    active = false
                    sourceComponent = null
                    loadedTab = null
                    Qt.callLater(loadCurrentTab)
                }
                function loadCurrentTab() {
                    if (!centerPanel.hasTabs)
                        return
                    loadedTab = centerPanel.workspaceController.activeTab
                    const type = centerPanel.workspaceController.activeTabType
                    // TagPanel's inline control contexts are sensitive to cancellation
                    // during incubation. Build that lightweight shell atomically;
                    // metadata reading and delegate population remain deferred.
                    asynchronous = type !== "tag"
                    sourceComponent = type === "manual" ? manualComponent
                        : type === "settings" ? settingsComponent
                        : type === "pacs" ? pacsComponent
                        : type === "tag" ? tagComponent
                        : type === "3d" ? volumeComponent
                        : type === "comparempr" ? compareMprComponent
                        : type === "montage" ? montageComponent : type === "2d" ? twoDComponent : imageComponent
                    active = true
                }
                Component.onCompleted: openCurrentTab()
                Connections {
                    target: centerPanel.workspaceController
                    function onActiveTabChanged() { workspaceLoader.openCurrentTab() }
                }
            }
            WorkspaceLoadingState {
                anchors.fill: parent
                visible: centerPanel.hasTabs && (workspaceLoader.status !== Loader.Ready
                    || centerPanel.opening?.status === "loading" || centerPanel.opening?.status === "error")
                loading: workspaceLoader.status !== Loader.Error && centerPanel.opening?.status !== "error"
                message: workspaceLoader.status === Loader.Error ? qsTrId("text.0898")
                    : centerPanel.opening?.status === "error" ? centerPanel.opening.errorMessage
                    : workspaceLoader.status !== Loader.Ready ? qsTrId("text.0895")
                    : (centerPanel.opening?.message ?? qsTrId("text.0439"))
                onRetryRequested: {
                    if (workspaceLoader.status === Loader.Error) workspaceLoader.openCurrentTab()
                    centerPanel.workspaceController.retryActiveTab()
                }
                onCloseRequested: centerPanel.workspaceController.closeTab(centerPanel.workspaceController.activeTabId)
            }
        }

    }

    Component {
        id: manualComponent
        Manual.OperationManual {
            controller: centerPanel.workspaceController.manualController
            active: centerPanel.workspaceController.activeTabType === "manual"
                && workspaceLoader.status === Loader.Ready
        }
    }

    Component {
        id: settingsComponent
        Settings.SettingsPage { pacsController: centerPanel.pacsController; settingsController: centerPanel.settingsController }
    }

    Component {
        id: pacsComponent
        Pacs.PacsBrowser { pacsController: centerPanel.pacsController; workspaceController: centerPanel.workspaceController }
    }

    Component {
        id: tagComponent
        TagPanel {
            active: workspaceLoader.status === Loader.Ready
            tagController: workspaceLoader.loadedTab
                ? workspaceLoader.loadedTab.tagController
                : null
        }
    }

    Component {
        id: compareMprComponent
        ViewportSection.CompareMprViewportLayout { tabController: workspaceLoader.loadedTab }
    }
    Component {
        id: twoDComponent
        ViewportSection.TwoDViewportLayout {
            tabController: workspaceLoader.loadedTab
        }
    }
    Component {
        id: imageComponent
        ViewportSection.ViewportLayout {
            // Loader and workspace signals can update in different orders.
            // Never hand a volume controller to a still-live image component.
            viewportController: centerPanel.imageWorkspace
                && centerPanel.viewportController?.workspaceTab === workspaceLoader.loadedTab
                ? centerPanel.viewportController : null
            hasTabs: centerPanel.hasTabs
            tabType: centerPanel.workspaceController.activeTabType
            currentTabAllViewports: centerPanel.imageWorkspace
                ? centerPanel.currentTabAllViewports.filter(view => view?.setViewportSize !== undefined) : []
            onViewportActivated: viewportId => {
                const activeTab = centerPanel.workspaceController.activeTab
                if (activeTab) {
                    activeTab.activateViewport(viewportId)
                }
            }
        }
    }

    Component {
        id: volumeComponent
        ViewportSection.VolumeViewport {
            viewportController: centerPanel.viewportController
            onPresentationReady: success => {
                const manager = centerPanel.windowManager
                const windowId = centerPanel.workspaceController.windowId
                const tabId = centerPanel.workspaceController.activeTabId
                Qt.callLater(() => manager?.pageReady(windowId, tabId, success))
            }
        }
    }

    Component {
        id: montageComponent
        ViewportSection.MontageViewport {
            viewportController: centerPanel.workspaceController.activeTab?.activeViewport ?? null
        }
    }

    WorkspaceEmptyState {
        anchors.fill: parent
        anchors.topMargin: centerPanel.windowManager?.dragging ? 46 : 0
        visible: !centerPanel.hasTabs
        panelController: centerPanel.panelController
        pacsController: centerPanel.pacsController
        workspaceController: centerPanel.workspaceController
    }
}
