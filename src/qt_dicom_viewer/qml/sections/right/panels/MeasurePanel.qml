pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../components" as Components
import "../../../theme"

ColumnLayout {
    id: measurePanel
    spacing: 8
    required property var toolController

    signal manualRequested()

    Components.ToolActionButton {
        objectName: "measurementManualButton"
        Layout.alignment: Qt.AlignRight
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        iconName: "manual"
        iconSize: 18
        label: qsTrId("text.1031")
        onClicked: measurePanel.manualRequested()
    }

    signal actionTriggered(string action)

    ColumnLayout {
        objectName: "measurementInstructions"
        Layout.fillWidth: true
        spacing: 7
        Repeater {
            model: [
                { label: qsTrId("text.0864"), detail: qsTrId("text.1032") },
                { label: qsTrId("text.0782"), detail: qsTrId("text.1033") },
                { label: qsTrId("text.1034"), detail: Qt.platform.os === "osx" ? qsTrId("text.1035") : qsTrId("text.1036") },
                { label: qsTrId("text.1037"), detail: Qt.platform.os === "osx" ? qsTrId("text.1038") : qsTrId("text.1039") },
                { label: qsTrId("text.0539"), detail: qsTrId("text.1040") },
                { label: qsTrId("text.0761"), detail: qsTrId("text.1041") }
            ]
            delegate: RowLayout {
                id: instructionRow
                required property var modelData
                required property int index
                objectName: "measurementInstruction" + index
                Layout.fillWidth: true
                spacing: 8
                Text {
                    Layout.alignment: Qt.AlignTop
                    Layout.preferredWidth: 28
                    text: instructionRow.modelData.label
                    color: Theme.textSecondary
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    text: instructionRow.modelData.detail
                    color: Theme.textSubtle
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                }
            }
        }
    }

    GridLayout {
        Layout.fillWidth: true
        columns: 2
        columnSpacing: 6
        rowSpacing: 6
        uniformCellWidths: true
        Repeater {
            model: measurePanel.toolController ? measurePanel.toolController.measureActions : []
            delegate: Components.ToolActionButton {
                id: measureButton
                required property var modelData
                readonly property bool btnChecked: measureButton.modelData.action === (measurePanel.toolController?.activeInteraction ?? "")

                checked: measureButton.btnChecked
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                iconName: modelData.iconName
                label: modelData.label

                onClicked: {
                    measurePanel.actionTriggered(modelData.action);
                }
            }
        }
    }

    Item {
        Layout.fillHeight: true
    }
}
