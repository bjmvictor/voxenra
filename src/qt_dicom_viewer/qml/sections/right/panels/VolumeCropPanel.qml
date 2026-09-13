pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../theme"
import "../../../components" as Components
import "../components" as Controls

Item {
    id: root
    objectName: "volumeCropPanel"
    required property var viewportController
    readonly property var controller: viewportController && viewportController.viewportType === "volume" ? viewportController : null
    implicitHeight: controls.implicitHeight

    ColumnLayout {
        id: controls
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 12

        Text {
            Layout.fillWidth: true
            text: qsTrId("text.1047")
            wrapMode: Text.Wrap
            color: Theme.textSecondary
            font.pixelSize: 13
        }

        Repeater {
            model: [
                { mode: "inside", label: qsTrId("text.1048"), hint: qsTrId("text.1049") },
                { mode: "outside", label: qsTrId("text.1050"), hint: qsTrId("text.1051") }
            ]
            delegate: Components.AppButton {
                id: action
                required property var modelData
                objectName: "volumeCrop-" + modelData.mode
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                enabled: !!root.controller && root.controller.loadState === "ready"
                    && !root.controller.editBusy
                checked: !!root.controller && root.controller.cropMode === modelData.mode
                Accessible.name: modelData.label
                onClicked: root.controller.setCropMode(modelData.mode)
                contentItem: Column {
                    spacing: 4
                    Text {
                        width: parent.width
                        text: action.modelData.label
                        color: action.enabled ? Theme.textPrimary : Theme.textDisabled
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Text {
                        width: parent.width
                        text: action.modelData.hint
                        color: action.enabled ? Theme.textSecondary : Theme.textDisabled
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                baseBorderWidth: 1
                baseBorderColor: Theme.controlBorder
            }
        }

        Text {
            Layout.fillWidth: true
            text: root.controller && root.controller.hasCrop
                ? qsTrId("text.1052")
                : qsTrId("text.1053")
            wrapMode: Text.Wrap
            color: Theme.textSecondary
            font.pixelSize: 12
        }
    }
}
