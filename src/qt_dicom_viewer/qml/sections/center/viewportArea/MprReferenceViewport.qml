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
            color: Theme.overlayText
            font.pixelSize: 12
            elide: Text.ElideRight
        }
        TapHandler { onTapped: root.controller?.activate() }
    }
    Loader {
        anchors.top: header.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        active: root.visible && root.volume?.loadState === "ready"
        sourceComponent: VolumeViewport {
            viewportController: root.volume
            activeViewport: root.controller?.active ?? false
        }
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
            text: root.volume?.loadState === "error" ? root.volume.errorMessage : qsTrId("mpr.reference.loading")
            color: Theme.textSecondary
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            font.pixelSize: 12
        }
        Components.AppButton {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: root.volume?.loadState === "error"
            text: qsTrId("text.0009")
            onClicked: root.volume.retry()
        }
    }
}
