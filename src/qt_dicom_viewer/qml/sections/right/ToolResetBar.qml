pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "components" as Controls
import "../../theme"
Rectangle {
    id: root
    required property var toolController
    property var voiController: null
    property bool collapsed: false
    signal collapseRequested()
    readonly property string panel: toolController?.activePanel ?? ""
    readonly property bool voiActions: !!voiController && ["segmentation", "voi"].includes(panel)
    implicitHeight: collapsed ? 88 : 52
    color: Theme.panelBackgroundStrong
    Controls.ToolActionButton {
        objectName: "activeToolReset"
        visible: !root.collapsed && !root.voiActions
        anchors.fill: parent; anchors.margins: 6; anchors.rightMargin: 46
        iconName: "reset"
        label: root.toolController ? root.toolController.resetLabel : qsTrId("text.0576")
        enabled: root.toolController ? root.toolController.canResetActiveTool : false
        hoverColor: Theme.resetActionHover
        pressedColor: Theme.resetActionPressed
        onClicked: root.toolController.resetActiveTool()
    }
    RowLayout {
        objectName: "voiBottomActions"
        anchors.fill: parent
        anchors.margins: 6
        anchors.rightMargin: 46
        spacing: 8
        visible: !root.collapsed && root.voiActions
        Components.AppButton {
            objectName: "voiClearKind"
            Layout.fillWidth: true
            compact: true
            text: root.panel === "segmentation" ? qsTrId("text.0739") : qsTrId("text.0740")
            enabled: (root.voiController?.items ?? []).some(item => item.kind === root.panel)
            onClicked: root.voiController.clear(root.panel)
        }
        Components.AppButton {
            objectName: "voiClearAll"
            Layout.fillWidth: true
            compact: true
            text: qsTrId("text.0741")
            textColor: Theme.warningColor
            enabled: (root.voiController?.items?.length ?? 0) > 0
            onClicked: root.voiController.clear("")
        }
    }
    Components.ToolbarAction {
        visible: root.collapsed
        anchors.top: parent.top; anchors.topMargin: 4
        anchors.horizontalCenter: parent.horizontalCenter
        width: 36; height: 36
        buttonObjectName: "compactToolReset"
        iconName: "reset"
        label: root.toolController?.resetLabel ?? qsTrId("text.0576")
        resetAction: true
        actionEnabled: root.toolController?.canResetActiveTool ?? false
        onTriggered: root.toolController.resetActiveTool()
    }
    Components.ToolbarAction {
        anchors.right: parent.right; anchors.rightMargin: root.collapsed ? 3 : 6
        anchors.bottom: parent.bottom; anchors.bottomMargin: 8
        width: 36; height: 36
        buttonObjectName: "toggleRightPanel"
        iconName: root.collapsed ? "chevron-left" : "chevron-right"
        label: root.collapsed ? qsTrId("tools.expand") : qsTrId("tools.collapse")
        onTriggered: root.collapseRequested()
    }
}
