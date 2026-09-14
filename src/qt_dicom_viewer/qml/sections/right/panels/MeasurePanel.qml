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
        label: "测量操作手册"
        onClicked: measurePanel.manualRequested()
    }

    signal actionTriggered(string action)

    ColumnLayout {
        objectName: "measurementInstructions"
        Layout.fillWidth: true
        spacing: 7
        Repeater {
            model: [
                { label: "完成", detail: "绘制结束后松开，保持选中。角度按三点绘制。" },
                { label: "编辑", detail: "点击已有测量，进入选中草稿状态。" },
                { label: "复制", detail: Qt.platform.os === "osx" ? "⌘C 复制，⌘V 粘贴所选。" : "Ctrl+C 复制，Ctrl+V 粘贴所选。" },
                { label: "历史", detail: Qt.platform.os === "osx" ? "⌘Z 撤销，⇧⌘Z 重做。" : "Ctrl+Z 撤销，Ctrl+Y 重做。" },
                { label: "取消", detail: "Esc 取消当前绘制或编辑。" },
                { label: "删除", detail: "Delete / Backspace 删除所选。" }
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
