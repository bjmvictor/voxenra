pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../components" as Components
import "../theme"

Components.AppDialog {
    id: dialog
    objectName: "exportDialog"
    property var controller: null
    property var settingsController: null
    signal manualRequested()
    parent: Basic.Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(560, parent ? parent.width - 32 : 560)
    height: Math.min(560, parent ? parent.height - 32 : 560)
    closeEnabled: !!controller && !controller.busy
    closeButtonName: "exportDialogClose"
    modal: true
    title: controller && controller.anonymousLocked ? "脱敏导出整个序列" : "导出序列"
    padding: 16
    onClosed: { if (controller) controller.closeDialog() }

    Connections {
        target: dialog.controller
        function onDialogChanged() {
            if (dialog.controller.dialogOpen) {
                format.currentIndex = 0
                anonymous.checked = true
                dialog.open()
            } else {
                dialog.close()
            }
        }
    }

    contentItem: Basic.ScrollView {
        id: exportScroll
        clip: true
        contentWidth: availableWidth
        Basic.ScrollBar.horizontal.policy: Basic.ScrollBar.AlwaysOff
        Basic.ScrollBar.vertical: Components.AppScrollBar {}
        ColumnLayout {
            width: exportScroll.availableWidth
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: "整个序列 · " + (dialog.controller ? dialog.controller.instanceCount : 0) + " 个 DICOM 文件"
                color: Theme.textMuted
                font.pixelSize: 13
            }
            RowLayout {
                Layout.fillWidth: true
                Text { text: "导出格式"; color: Theme.textPrimary; font.pixelSize: 13 }
                Components.AppComboBox {
                    id: format
                    objectName: "exportFormat"
                    Layout.fillWidth: true
                    model: ["DICOM (.dcm)", "PNG (.png)"]
                    enabled: dialog.controller && !dialog.controller.busy
                }
            }
            Components.AppCheckBox {
                id: anonymous
                objectName: "exportAnonymous"
                text: "匿名导出"
                checked: true
                enabled: dialog.controller && !dialog.controller.busy && !dialog.controller.anonymousLocked
            }
            Components.AppLinkButton {
                objectName: "seriesExportManualLink"
                Layout.fillWidth: true
                text: "查看导出说明"
                enabled: !dialog.controller?.busy
                tooltip: "操作手册 · 导出格式与匿名范围"
                onClicked: {
                    dialog.close()
                    dialog.manualRequested()
                }
            }
            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.dividerColor }
            Text { text: "导出位置"; color: Theme.textPrimary; font.pixelSize: 13 }
            Text {
                objectName: "exportDestination"
                Layout.fillWidth: true
                text: dialog.settingsController ? dialog.settingsController.exportDirectory : ""
                textFormat: Text.PlainText
                color: Theme.textMuted
                font.pixelSize: 12
                wrapMode: Text.WrapAnywhere
            }
            Components.AppButton {
                text: "更改导出位置…"
                normalColor: "transparent"
                baseBorderWidth: 1
                baseBorderColor: Theme.controlBorder
                compact: true
                enabled: dialog.controller && !dialog.controller.busy
                onClicked: dialog.settingsController.chooseExportDirectory()
            }
            Basic.ProgressBar {
                objectName: "exportProgress"
                Layout.fillWidth: true
                visible: dialog.controller && dialog.controller.busy
                from: 0
                to: dialog.controller ? Math.max(1, dialog.controller.totalCount) : 1
                value: dialog.controller ? dialog.controller.completedCount : 0
                indeterminate: dialog.controller && dialog.controller.totalCount === 0
            }
            Text {
                objectName: "exportMessage"
                Layout.fillWidth: true
                visible: text !== ""
                text: dialog.controller ? dialog.controller.message : ""
                textFormat: Text.PlainText
                color: Theme.textPrimary
                font.pixelSize: 13
                wrapMode: Text.Wrap
            }
            Components.AppLinkButton {
                objectName: "exportOutputDirectory"
                Layout.fillWidth: true
                visible: text !== ""
                text: dialog.controller ? dialog.controller.outputDirectory : ""
                tooltip: "打开导出文件夹\n" + text
                onClicked: dialog.controller.openOutputDirectory()
            }

        }
    }
    footer: Components.AppDialogFooter {
        Components.AppButton {
            objectName: "cancelExport"
            text: dialog.controller && dialog.controller.busy ? "取消导出" : "取消"
            onClicked: {
                if (dialog.controller.busy) dialog.controller.cancelExport()
                else dialog.reject()
            }
        }
        Components.AppButton {
            objectName: "startExport"
            text: "开始导出"
            actionRole: "primary"
            enabled: dialog.controller && !dialog.controller.busy && dialog.controller.instanceCount > 0
            onClicked: dialog.controller.startExport(format.currentIndex === 0 ? "dicom" : "png", anonymous.checked)
        }
    }
}
