pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../components" as Components
import "../../../theme"

ColumnLayout {
    id: root
    objectName: "exportPanel"
    property var exportController: null
    property Item exportItem: null
    readonly property var report: exportController?.measurementReport ?? null
    signal manualRequested()
    spacing: 10
    Text {
        text: "导出"
        color: Theme.textPrimary
        font.pixelSize: 13
        font.weight: Font.DemiBold
    }
    Components.AppCheckBox {
        id: anonymous
        objectName: "viewportExportAnonymous"
        text: "匿名导出"
        checked: true
        enabled: !!root.exportController && !root.exportController.busy
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Components.AppButton {
            objectName: "exportPng"
            Layout.fillWidth: true
            text: "导出 PNG"
            normalColor: Theme.primaryButtonBackground
            hoverColor: Theme.primaryButtonHover
            pressedColor: Theme.primaryButtonPressed
            disabledColor: Theme.primaryButtonDisabled
            textColor: Theme.textOnPrimary
            compact: true
            enabled: !!root.exportController && !root.exportController.busy
            onClicked: root.exportController.exportPng(root.exportItem, Screen.devicePixelRatio, anonymous.checked)
        }
        Components.AppButton {
            objectName: "exportDicom"
            Layout.fillWidth: true
            text: "导出 DICOM"
            normalColor: "transparent"
            baseBorderWidth: 1
            baseBorderColor: Theme.primaryButtonBorder
            textColor: Theme.iconActive
            compact: true
            enabled: !!root.exportController && !root.exportController.busy
            onClicked: root.exportController.exportDicom(anonymous.checked)
        }
    }
    Basic.ProgressBar {
        Layout.fillWidth: true
        visible: !!root.exportController && root.exportController.busy
        value: root.exportController ? root.exportController.progress : 0
        indeterminate: value === 0
    }
    Text {
        objectName: "exportMessage"
        Layout.fillWidth: true
        text: root.exportController ? root.exportController.message : ""
        textFormat: Text.PlainText
        visible: text !== ""
        wrapMode: Text.WrapAnywhere
        font.pixelSize: 12
        color: root.exportController && root.exportController.isError ? Theme.dangerColor : Theme.textSecondary
    }
    Components.AppLinkButton {
        objectName: "exportResultPath"
        Layout.fillWidth: true
        text: root.exportController?.resultPath ?? ""
        visible: text !== ""
        tooltip: (Qt.platform.os === "osx" ? "在 Finder 中显示" : "在文件资源管理器中显示") + "\n" + text
        onClicked: root.exportController.openResultLocation()
    }
    Components.AppButton {
        text: "取消导出"
        visible: !!root.exportController && root.exportController.busy
        onClicked: root.exportController.cancel()
    }
    Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Theme.borderDefault }
    Text { text: "测量结果"; color: Theme.textPrimary; font.pixelSize: 13; font.weight: Font.DemiBold }
    Components.AppCheckBox {
        id: allTabs
        objectName: "reportAllTabs"
        text: "包含所有页签"
        enabled: !root.report?.busy
    }
    Components.AppCheckBox {
        id: reportImages
        objectName: "reportIncludeImages"
        text: "PDF 附当前切片参考图"
        checked: true
        enabled: !root.report?.busy
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Components.AppButton {
            objectName: "exportMeasurementCsv"
            text: "测量 CSV"
            actionRole: "primary"
            compact: true
            Layout.fillWidth: true
            enabled: !!root.report && !root.report.busy
            onClicked: root.report.exportReport("csv", allTabs.checked, anonymous.checked, false)
        }
        Components.AppButton {
            objectName: "exportMeasurementPdf"
            text: "测量 PDF"
            compact: true
            Layout.fillWidth: true
            baseBorderWidth: 1
            baseBorderColor: Theme.primaryButtonBorder
            enabled: !!root.report && !root.report.busy
            onClicked: root.report.exportReport("pdf", allTabs.checked, anonymous.checked, reportImages.checked)
        }
    }
    Basic.ProgressBar { Layout.fillWidth: true; visible: root.report?.busy ?? false; indeterminate: true }
    Text {
        objectName: "measurementReportMessage"
        Layout.fillWidth: true
        text: root.report?.message ?? ""
        textFormat: Text.PlainText
        visible: text !== ""
        wrapMode: Text.WrapAnywhere
        font.pixelSize: 12
        color: root.report?.isError ? Theme.dangerColor : Theme.textSecondary
    }
    Components.AppLinkButton {
        objectName: "measurementReportResultPath"
        Layout.fillWidth: true
        text: root.report?.resultPath ?? ""
        visible: text !== ""
        tooltip: (Qt.platform.os === "osx" ? "在 Finder 中显示" : "在文件资源管理器中显示") + "\n" + text
        onClicked: root.report.openResultLocation()
    }
    Components.AppLinkButton {
        objectName: "exportManualLink"
        Layout.fillWidth: true
        text: "查看导出说明"
        tooltip: "操作手册 · PNG、DICOM 与测量结果导出"
        onClicked: root.manualRequested()
    }
}
