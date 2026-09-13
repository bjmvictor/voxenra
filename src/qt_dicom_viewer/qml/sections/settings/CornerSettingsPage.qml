pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../components" as Components
import "../../theme"

SettingsSplit {
    id: root
    required property var settingsController
    readonly property var values: settingsController.values.corners
    readonly property var fields: settingsController.cornerFields
    readonly property var corners: [{key: "topLeft", title: qsTrId("text.0789")}, {key: "topRight", title: qsTrId("text.0790")}, {key: "bottomLeft", title: qsTrId("text.0791")}, {key: "bottomRight", title: qsTrId("text.0792")}]
    property string activeCorner: "topLeft"
    property string fieldSearch: ""
    readonly property var availableFields: fields.filter(item => !values[activeCorner].includes(item.key) && (item.label + item.key).toLowerCase().includes(fieldSearch.toLowerCase()))
    function fieldLabel(key) { return fields.find(item => item.key === key)?.label ?? key }
    SettingsSection {
        Layout.fillWidth: true
        title: qsTrId("text.0793")
        Components.AppCheckBox { objectName: "setting-corners-enabled"; text: qsTrId("text.0794"); checked: root.values.enabled; onClicked: root.settingsController.setValue("corners", "enabled", checked) }
        SettingSlider { Layout.fillWidth: true; title: qsTrId("text.0795"); settingName: "corners-fontSize"; from: 10; to: 20; stepSize: 1; value: root.values.fontSize; onEdited: value => root.settingsController.setValue("corners", "fontSize", value) }
        SettingSlider { Layout.fillWidth: true; title: qsTrId("text.0796"); settingName: "corners-lineHeight"; from: 1; to: 1.8; stepSize: 0.1; suffix: qsTrId("text.0797"); value: root.values.lineHeight; onEdited: value => root.settingsController.setValue("corners", "lineHeight", value) }
        RowLayout {
            Layout.fillWidth: true
            Text { Layout.fillWidth: true; text: qsTrId("text.0798"); color: Theme.textSecondary; font.pixelSize: 12 }
            Components.AppComboBox {
                objectName: "setting-corners-colorMode"
                Layout.preferredWidth: 180
                model: [{label: qsTrId("text.0799"), value: "auto"}, {label: qsTrId("text.0800"), value: "custom"}]
                textRole: "label"; valueRole: "value"
                currentIndex: root.values.colorMode === "auto" ? 0 : 1
                onActivated: index => root.settingsController.setValue("corners", "colorMode", index === 0 ? "auto" : "custom")
            }
        }
        SettingColor { Layout.fillWidth: true; enabled: root.values.colorMode === "custom"; title: qsTrId("text.0800"); settingName: "corners-color"; value: root.values.color; onEdited: color => root.settingsController.setValue("corners", "color", color) }
    }
    SettingsSection {
        Layout.fillWidth: true
        title: qsTrId("text.0801")
        RowLayout {
            Layout.fillWidth: true; spacing: 4
            Repeater {
                model: root.corners
                delegate: Components.AppButton {
                    required property var modelData
                    objectName: "cornerSelect-" + modelData.key
                    Layout.fillWidth: true; compact: true
                    text: modelData.title; checked: root.activeCorner === modelData.key
                    onClicked: root.activeCorner = modelData.key
                }
            }
        }
        Repeater {
            model: root.values[root.activeCorner]
            delegate: RowLayout {
                id: entry
                required property string modelData
                required property int index
                Layout.fillWidth: true; spacing: 4
                Text { Layout.preferredWidth: 18; text: entry.index + 1; color: Theme.textSubtle; font.pixelSize: 11 }
                Text { Layout.fillWidth: true; Layout.minimumWidth: 0; text: root.fieldLabel(entry.modelData); color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.Wrap }
                Repeater {
                    model: [{action: "Up", text: "↑", label: qsTrId("text.0802"), enabled: entry.index > 0}, {action: "Down", text: "↓", label: qsTrId("text.0803"), enabled: entry.index < root.values[root.activeCorner].length - 1}, {action: "Remove", text: "×", label: qsTrId("text.0804"), enabled: true}]
                    delegate: Components.AppButton {
                        id: actionButton
                        required property var modelData
                        objectName: "corner" + modelData.action + "-" + root.activeCorner + "-" + entry.index
                        Layout.preferredWidth: 26; Layout.preferredHeight: 26; minimumButtonWidth: 26; compact: true
                        text: modelData.text; enabled: modelData.enabled
                        Accessible.name: modelData.label + root.fieldLabel(entry.modelData)
                        Components.AppToolTip {
                            visible: actionButton.hovered || actionButton.visualFocus
                            text: actionButton.modelData.label
                            delay: 450
                        }
                        onClicked: {
                            if (modelData.action === "Remove") root.settingsController.removeCornerField(root.activeCorner, entry.index)
                            else root.settingsController.moveCornerField(root.activeCorner, entry.index, modelData.action === "Up" ? -1 : 1)
                        }
                    }
                }
            }
        }
        Text { visible: root.values[root.activeCorner].length === 0; text: qsTrId("text.0805"); color: Theme.textMuted; font.pixelSize: 12 }
        RowLayout {
            Layout.fillWidth: true
            Components.AppTextField { objectName: "cornerFieldSearch"; Layout.fillWidth: true; placeholderText: qsTrId("text.0806"); onTextEdited: root.fieldSearch = text }
            Text { text: root.values[root.activeCorner].length + " / 8"; color: Theme.textSubtle; font.pixelSize: 11 }
        }
        RowLayout {
            Layout.fillWidth: true
            Components.AppComboBox { id: choice; objectName: "cornerChoice-" + root.activeCorner; Layout.fillWidth: true; Layout.minimumWidth: 0; model: root.availableFields; textRole: "label"; valueRole: "key" }
            Components.AppButton { objectName: "cornerAdd-" + root.activeCorner; text: qsTrId("text.0807"); enabled: choice.currentIndex >= 0 && root.values[root.activeCorner].length < 8; onClicked: root.settingsController.addCornerField(root.activeCorner, choice.currentValue) }
        }
    }
    preview: Component {
        ColumnLayout {
            spacing: 10
            Text { text: qsTrId("text.0808"); color: Theme.textMuted; font.pixelSize: 12 }
            GridLayout {
                Layout.fillWidth: true
                columns: 2; columnSpacing: 6; rowSpacing: 6; uniformCellWidths: true
                Repeater {
                    model: root.corners
                    delegate: Rectangle {
                        id: tile
                        required property var modelData
                        objectName: "cornerPreview-" + modelData.key
                        Layout.fillWidth: true; Layout.minimumWidth: 0; Layout.preferredHeight: 116
                        color: Theme.canvasBackground; radius: 4
                        border.color: root.activeCorner === modelData.key ? Theme.selectionBorder : Theme.borderSubtle
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 10; spacing: 6
                            Text { text: tile.modelData.title; color: root.activeCorner === tile.modelData.key ? Theme.primaryColor : Theme.textMuted; font.pixelSize: 11 }
                            Text {
                                Layout.fillWidth: true; Layout.fillHeight: true
                                text: root.values[tile.modelData.key].slice(0, 2).map(key => root.fieldLabel(key)).join("\n") || qsTrId("text.0809")
                                font.pixelSize: 11; color: Theme.textSecondary; wrapMode: Text.Wrap
                            }
                            Text { text: I18n.format(qsTrId("corners.count"), {count: root.values[tile.modelData.key].length}); color: Theme.textSubtle; font.pixelSize: 10 }
                        }
                        TapHandler { onTapped: root.activeCorner = tile.modelData.key }
                    }
                }
            }
            Text { Layout.fillWidth: true; text: qsTrId("text.0811"); color: Theme.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap }
        }
    }
}
