pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "right" as Right
import "../theme"
import "../components" as Components

Rectangle {
    id: rightPanel
    objectName: "rightPanel"

    required property var toolController
    required property bool toolVisible
    required property var viewportController
    property bool collapsed: false
    signal collapseRequested()
    property var tabController: null
    property var exportController: null
    property Item exportItem: null
    signal manualRequested(string chapter)
    readonly property var volumeController: viewportController && viewportController.viewportType === "volume"
        ? viewportController : null

    color: Theme.panelBackground
    border.color: Theme.borderDefault
    border.width: 1
    radius: 8
    clip: true

    onCollapsedChanged: syncCompactTool()
    onToolControllerChanged: syncCompactTool()
    function syncCompactTool() {
        if (collapsed && toolController) {
            const direct = ["window", "ct-window", "pet-window", "scroll", "pan", "zoom", "volume-rotate", "mpr-rotate-3d"]
            if (!["measure", "rotate", "pseudocolor", "annotate"].includes(toolController.activeTool))
                toolController.activateDirectTool(direct.includes(toolController.activeTool) ? toolController.activeTool : "pan")
        }
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 1
        spacing: 0
        visible: rightPanel.toolVisible

        Right.CompactToolRail {
            visible: rightPanel.collapsed
            Layout.fillWidth: true
            Layout.fillHeight: true
            toolController: rightPanel.toolController
            viewportController: rightPanel.viewportController
        }
        Right.PrimaryToolBar {
            visible: !rightPanel.collapsed
            Layout.fillWidth: true
            Layout.preferredHeight: implicitHeight
            toolController: rightPanel.toolController
            viewportController: rightPanel.viewportController
            playbackActive: rightPanel.tabController?.playing ?? false

            onToolTriggered: toolDefinition => {
                rightPanel.toolController?.activateTool(
                    toolDefinition.toolType
                )
            }
        }

        Text {
            objectName: "volumeEditStatus"
            Layout.fillWidth: true
            Layout.margins: visible ? 10 : 0
            visible: !rightPanel.collapsed && !!rightPanel.volumeController && (rightPanel.volumeController.bedRemovalEnabled
                || rightPanel.volumeController.editMessage !== "")
            text: rightPanel.volumeController
                ? [rightPanel.volumeController.bedRemovalEnabled ? qsTrId("text.0676") : "",
                    rightPanel.volumeController.editMessage].filter(s => s !== "").join("\n") : ""
            color: Theme.textSecondary
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }

        Flickable {
            id: detailFlickable
            visible: !rightPanel.collapsed
            objectName: "toolDetailFlickable"

            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: Math.max(
                height,
                toolDetailPanel.implicitHeight
            )
            boundsBehavior: Flickable.StopAtBounds

            Right.ToolDetailPanel {
                id: toolDetailPanel

                // Reserve the gutter even before overflow. Otherwise wrapped
                // text changes the height, which changes this width again and
                // can trap narrow measurement panels in a Qt layout loop.
                width: Math.max(0, detailFlickable.width - 10)
                height: detailFlickable.contentHeight
                toolController: rightPanel.toolController
                activePanel: rightPanel.toolController
                    ? rightPanel.toolController.activePanel
                    : ""
                viewportController: rightPanel.viewportController
                tabController: rightPanel.tabController
                exportController: rightPanel.exportController
                exportItem: rightPanel.exportItem
                onManualRequested: chapter => rightPanel.manualRequested(chapter)
            }

            Basic.ScrollBar.vertical: Components.AppScrollBar {
                policy: detailFlickable.contentHeight
                    > detailFlickable.height
                    ? Basic.ScrollBar.AsNeeded
                    : Basic.ScrollBar.AlwaysOff
            }
        }

        Right.ToolResetBar {
            Layout.fillWidth: true
            collapsed: rightPanel.collapsed
            playbackActive: rightPanel.tabController?.playing ?? false
            onCollapseRequested: rightPanel.collapseRequested()
            toolController: rightPanel.toolController
            voiController: rightPanel.tabController?.voiController ?? rightPanel.viewportController?.voiController ?? null
        }
    }

}
