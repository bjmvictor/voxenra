pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: panel
    objectName: "mprLayoutPanel"
    required property var controller
    readonly property var volume: controller?.volumeViewport ?? null
    spacing: 10

    Text { text: "MPR 布局"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
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
    Rectangle { Layout.fillWidth: true; height: 1; color: Theme.dividerColor }
    ColumnLayout {
        Layout.fillWidth: true
        visible: panel.controller?.layout === "quad"
        spacing: 8
        Text { text: "3D 空间参考"; color: Theme.textPrimary; font.pixelSize: 14; font.bold: true }
        Components.AppComboBox {
            objectName: "mprReferenceMode"
            Layout.fillWidth: true
            model: [{label: "切面边框与交点", value: "planes"},
                    {label: "仅显示交点", value: "point"}, {label: "隐藏空间参考", value: "hidden"}]
            textRole: "label"
            currentIndex: model.findIndex(o => o.value === panel.controller?.referenceMode)
            onActivated: panel.controller.setReferenceMode(model[currentIndex].value)
        }
        Components.AppCheckBox {
            objectName: "mprLinkRotation"
            Layout.fillWidth: true
            text: "联动 3D 与 MPR 旋转"
            checked: panel.controller?.linkRotation ?? false
            onToggled: panel.controller.setLinkRotation(checked)
        }
        Text {
            Layout.fillWidth: true
            text: "拖动 3D 中心标记可移动 MPR 交点。开启旋转联动后，旋转 3D 会同时改变 MPR 切面。"
            color: Theme.textMuted
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
        Text { text: "3D 显示"; color: Theme.textSecondary; font.pixelSize: 12 }
        Components.AppComboBox {
            objectName: "mpr3dPreset"
            Layout.fillWidth: true
            visible: panel.volume?.isStandalonePetVolume !== true
            enabled: panel.volume?.loadState === "ready"
            model: (panel.volume?.volumePresets ?? []).filter(o => o.available)
            textRole: "label"
            currentIndex: model.findIndex(o => o.presetId === panel.volume?.currentPresetId)
            onActivated: panel.volume.applyVolumePreset(model[currentIndex].presetId)
        }
        Components.AppComboBox {
            objectName: "mpr3dPetColor"
            Layout.fillWidth: true
            visible: panel.volume?.isStandalonePetVolume === true
            enabled: panel.volume?.loadState === "ready"
            model: panel.volume?.colorMapOptions ?? []
            textRole: "label"
            currentIndex: model.findIndex(o => o.colorMap === panel.volume?.petPalette)
            onActivated: panel.volume.setPetPalette(model[currentIndex].colorMap)
        }
        VolumeDirectionPanel { Layout.fillWidth: true; viewportController: panel.volume }
    }
}
