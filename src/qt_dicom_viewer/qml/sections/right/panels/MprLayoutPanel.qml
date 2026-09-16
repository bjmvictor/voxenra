pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "mprLayoutPanel"
    required property var controller
    spacing: 10

    Text { text: qsTrId("mpr.layout.title"); color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
    GridLayout {
        Layout.fillWidth: true
        columns: 2
        columnSpacing: 6; rowSpacing: 6
        Repeater {
            model: panel.controller?.options ?? []
            delegate: Components.AppButton {
                id: choice
                required property var modelData
                objectName: "mprLayout-" + modelData.value
                Layout.fillWidth: true
                Layout.preferredWidth: 90
                Layout.preferredHeight: 66
                checkable: true
                checked: panel.controller?.layout === modelData.value
                Accessible.name: modelData.label
                onClicked: panel.controller.setLayout(modelData.value)
                contentItem: Column {
                    spacing: 4
                    Components.AppIcon {
                        anchors.horizontalCenter: parent.horizontalCenter
                        iconName: choice.modelData.icon
                        iconSize: 28
                        iconColor: choice.checked ? Theme.primaryColor : Theme.textSecondary
                    }
                    Text {
                        width: parent.width
                        text: choice.modelData.label
                        color: Theme.textPrimary
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }
    Components.AppCheckBox {
        objectName: "mprRememberLayout"
        Layout.fillWidth: true
        text: qsTrId("mpr.layout.remember")
        checked: panel.controller?.rememberLayout ?? false
        onToggled: panel.controller?.setRememberLayout(checked)
    }
    Text {
        Layout.fillWidth: true
        text: qsTrId("mpr.layout.rememberHint")
        color: Theme.textMuted
        font.pixelSize: 11
        wrapMode: Text.Wrap
    }
    Text {
        Layout.fillWidth: true
        visible: text.length > 0
        text: panel.controller?.preferenceError ?? ""
        color: Theme.warningColor
        font.pixelSize: 11
        wrapMode: Text.Wrap
    }
    Rectangle { Layout.fillWidth: true; height: 1; color: Theme.dividerColor }
    ColumnLayout {
        Layout.fillWidth: true
        visible: panel.controller?.layout === "quad"
        spacing: 8
        Text { text: qsTrId("mpr.reference.title"); color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
        Components.AppComboBox {
            objectName: "mprReferenceMode"
            Layout.fillWidth: true
            model: [{label: qsTrId("mpr.reference.planes"), value: "planes"},
                    {label: qsTrId("mpr.reference.point"), value: "point"}, {label: qsTrId("mpr.reference.hidden"), value: "hidden"}]
            textRole: "label"
            currentIndex: model.findIndex(o => o.value === panel.controller?.referenceMode)
            onActivated: panel.controller.setReferenceMode(model[currentIndex].value)
        }
        Components.AppCheckBox {
            objectName: "mprLinkRotation"
            Layout.fillWidth: true
            text: qsTrId("mpr.reference.linkRotation")
            checked: panel.controller?.linkRotation ?? false
            onToggled: panel.controller.setLinkRotation(checked)
        }
        Text {
            Layout.fillWidth: true
            text: qsTrId("mpr.reference.hint")
            color: Theme.textMuted
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
    }
}
