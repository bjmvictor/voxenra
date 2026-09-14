pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../components" as Components
import "../../../theme"

Rectangle {
    id: root
    objectName: "mprReferenceViewport"
    required property var controller
    readonly property var volume: controller?.volumeViewport ?? null
    color: Theme.canvasBackground

    RowLayout {
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 4
        height: 30
        spacing: 3
        Text {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: "3D"
            color: Theme.textSecondary
            font.pixelSize: 12
            elide: Text.ElideRight
        }
        Repeater {
            model: root.controller ? [{tool:"volume-rotate", icon:"rotate-3d", label:"旋转 3D"},
                    {tool:"pan", icon:"pan", label:"平移 3D"},
                    {tool:"zoom", icon:"zoom", label:"缩放 3D"},
                    {tool:"reset", icon:"reset", label:"重置 3D"}] : []
            delegate: Components.AppButton {
                id: referenceTool
                required property var modelData
                objectName: "mpr3dTool-" + modelData.tool
                Layout.preferredWidth: 30
                Layout.preferredHeight: 28
                minimumButtonWidth: 28
                compact: true
                iconName: modelData.icon
                iconSize: 16
                Accessible.name: modelData.label
                enabled: root.volume?.loadState === "ready"
                checked: root.controller?.volumeTools.activeTool === modelData.tool
                onClicked: root.controller.volumeTools.activateTool(modelData.tool)
                Components.AppToolTip {
                    visible: referenceTool?.hovered ?? false
                    text: referenceTool?.modelData.label ?? ""
                }
            }
        }
    }
    Loader {
        anchors.top: header.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        active: root.visible && root.volume?.loadState === "ready"
        sourceComponent: VolumeViewport { viewportController: root.volume }
    }
    Column {
        anchors.centerIn: parent
        width: Math.max(0, parent.width - 32)
        spacing: 10
        visible: root.volume?.loadState !== "ready"
        Basic.BusyIndicator {
            anchors.horizontalCenter: parent.horizontalCenter
            running: root.visible && root.volume?.loadState !== "error"
            visible: running
        }
        Text {
            width: parent.width
            text: root.volume?.loadState === "error" ? root.volume.errorMessage : "正在准备 3D 参考视图…"
            color: Theme.textSecondary
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            font.pixelSize: 12
        }
        Components.AppButton {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: root.volume?.loadState === "error"
            text: "重试"
            onClicked: root.volume.retry()
        }
    }
}
