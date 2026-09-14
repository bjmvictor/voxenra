pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../components" as Components
import "../theme"

Basic.Dialog {
    id: dialog
    objectName: "workspaceDocumentDialog"
    property var controller: null
    readonly property bool working: controller?.busy ?? false
    readonly property bool restoring: controller?.restoring ?? false
    readonly property bool missing: controller?.hasMissingSources ?? false
    readonly property bool recovery: controller?.recoveryAvailable ?? false
    // Keep a native window above VTK hosts, with the OS caption as the only close control.
    popupType: Basic.Popup.Window
    title: "工作区"
    implicitWidth: 500
    implicitHeight: 440
    width: Math.min(implicitWidth, parent ? parent.width - 24 : implicitWidth)
    height: Math.min(implicitHeight, parent ? parent.height - 24 : implicitHeight)
    padding: 16
    spacing: 0
    modal: true
    focus: true
    closePolicy: working ? Basic.Popup.NoAutoClose : Basic.Popup.CloseOnEscape
    background: Rectangle { color: Theme.panelBackgroundStrong }
    Connections {
        target: dialog.contentItem.Window.window
        function onClosing(event) {
            if (dialog.visible && dialog.working) event.accepted = false
        }
    }
    header: Item {
        implicitHeight: 72
        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12
            Components.AppIcon {
                iconName: "workspace"
                iconSize: 28
                iconColor: Theme.primaryColor
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                spacing: 4
                Text {
                    text: "保存与恢复"
                    color: Theme.textPrimary
                    font.pixelSize: 17
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    text: "保留影像引用与操作进度，稍后继续"
                    color: Theme.textMuted
                    font.pixelSize: 12
                    elide: Text.ElideRight
                }
            }
        }
    }
    contentItem: ColumnLayout {
        implicitWidth: 0
        implicitHeight: 0
        spacing: 12
        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumHeight: 44
            Layout.preferredHeight: 44
            Layout.maximumHeight: 44
            spacing: 6
            RowLayout {
                Layout.fillWidth: true
                Layout.minimumHeight: 18
                Layout.maximumHeight: 18
                Text {
                    objectName: "workspaceName"
                    Layout.fillWidth: true
                    text: dialog.controller?.workspaceName ?? "临时工作区"
                    color: Theme.textPrimary
                    font.pixelSize: 13
                    elide: Text.ElideRight
                }
                Text {
                    objectName: "workspaceSaveState"
                    text: dialog.controller?.dirty ? "有未保存更改" : "已保存"
                    opacity: dialog.controller?.path ? 1 : 0
                    color: dialog.controller?.dirty ? Theme.iconActive : Theme.textMuted
                    font.pixelSize: 12
                }
            }
            Text {
                id: location
                objectName: "workspaceDocumentPath"
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.minimumHeight: 20
                Layout.maximumHeight: 20
                text: dialog.controller?.path || "保存为工作区文件后，可在下次打开继续。"
                textFormat: Text.PlainText
                elide: Text.ElideMiddle
                color: Theme.textSecondary
                font.pixelSize: 12
                HoverHandler { id: pathHover }
                Components.AppToolTip {
                    visible: pathHover.hovered && !!dialog.controller?.path
                    text: location.text
                }
            }
        }
        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Theme.dividerColor }
        Item {
            objectName: "workspaceRecoveryArea"
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                RowLayout {
                    Layout.fillWidth: true
                    Layout.minimumHeight: 24
                    Layout.maximumHeight: 24
                    spacing: 8
                    Text {
                        Layout.fillWidth: true
                        text: dialog.missing ? "重新连接影像" : "自动恢复"
                        color: Theme.textPrimary
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                    Components.WorkspaceSaveIndicator {
                        objectName: "workspaceRecoveryStatus"
                        Layout.preferredWidth: 20
                        Layout.preferredHeight: 20
                        controller: dialog.controller
                    }
                    Components.AppCheckBox {
                        objectName: "workspaceAutomaticRecovery"
                        text: "启用"
                        implicitHeight: 24
                        checked: dialog.controller?.automaticRecovery ?? false
                        enabled: !!dialog.controller && !dialog.working
                        Accessible.name: "启用自动恢复"
                        onClicked: {
                            if (!dialog.controller.setAutomaticRecovery(checked))
                                checked = Qt.binding(() => dialog.controller.automaticRecovery)
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: dialog.missing ? "部分来源缺失或不一致。定位原文件、文件夹或压缩包后继续。"
                        : dialog.recovery ? "发现上次意外退出的恢复副本，可恢复进度或丢弃副本。"
                        : !dialog.controller?.automaticRecovery ? "自动恢复已关闭，仍可手动保存与打开工作区。"
                        : "有更改时每 30 秒保存恢复副本，用于意外退出后继续工作。"
                    color: Theme.textMuted
                    font.pixelSize: 12
                    wrapMode: Text.Wrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    spacing: 8
                    Components.AppLinkButton {
                        objectName: "workspaceRecoveryLocation"
                        Layout.fillWidth: true
                        text: "打开恢复副本位置"
                        tooltip: dialog.controller?.recoveryPath ?? ""
                        visible: !dialog.missing && !dialog.recovery
                        enabled: dialog.controller?.recoveryDirectoryAvailable ?? false
                        onClicked: dialog.controller.openRecoveryDirectory()
                    }
                    Components.AppButton {
                        objectName: dialog.missing ? "locateWorkspaceSources" : "recoverWorkspace"
                        text: dialog.missing ? "重新定位…" : "恢复上次进度"
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        compact: true
                        actionRole: "primary"
                        visible: dialog.missing || dialog.recovery
                        enabled: !dialog.working
                        onClicked: dialog.missing ? dialog.controller.locateMissing() : dialog.controller.recover()
                    }
                    Components.AppButton {
                        objectName: dialog.missing ? "skipWorkspaceSources" : "discardWorkspaceRecovery"
                        text: dialog.missing ? "仅恢复可用序列" : "丢弃旧副本"
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        compact: true
                        actionRole: dialog.missing ? "neutral" : "danger"
                        visible: dialog.missing || dialog.recovery
                        enabled: !dialog.working
                        onClicked: dialog.missing ? dialog.controller.skipMissing() : dialog.controller.discardRecovery()
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 48
            spacing: 8
            Basic.BusyIndicator {
                objectName: "workspaceDocumentProgress"
                Layout.alignment: Qt.AlignTop
                Layout.preferredWidth: 20
                Layout.preferredHeight: 20
                running: dialog.working && dialog.visible && dialog.controller?.recoveryState !== "saving"
                opacity: running ? 1 : 0
            }
            Basic.ScrollView {
                id: messageArea
                objectName: "workspaceDocumentMessageArea"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 0
                clip: true
                contentWidth: availableWidth
                Basic.ScrollBar.horizontal.policy: Basic.ScrollBar.AlwaysOff
                Basic.ScrollBar.vertical: Components.AppScrollBar {}
                TextEdit {
                    objectName: "workspaceDocumentMessage"
                    width: messageArea.availableWidth
                    rightPadding: 12
                    readOnly: true
                    selectByMouse: true
                    text: dialog.controller?.message ?? ""
                    textFormat: TextEdit.PlainText
                    wrapMode: TextEdit.Wrap
                    color: dialog.controller?.isError ? Theme.dangerColor : Theme.textSecondary
                    font.pixelSize: 12
                }
            }
        }
        Text {
            Layout.fillWidth: true
            text: "不包含原始影像，请保留源文件、压缩包或 PACS 下载文件。"
            color: Theme.textMuted
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
    }
    footer: Components.AppDialogFooter {
        leading: Item {
            implicitWidth: 132
            implicitHeight: 32
            Components.AppButton {
                objectName: "openWorkspace"
                anchors.fill: parent
                text: "打开工作区…"
                visible: !dialog.restoring
                enabled: !!dialog.controller && !dialog.working
                normalColor: "transparent"
                baseBorderWidth: 1
                compact: true
                onClicked: dialog.controller.open()
            }
            Components.AppButton {
                objectName: "cancelWorkspaceRestore"
                anchors.fill: parent
                text: "取消恢复"
                visible: dialog.restoring
                compact: true
                onClicked: dialog.controller.cancel()
            }
        }
        Components.AppButton {
            objectName: "saveWorkspaceAs"
            text: "另存为…"
            Layout.preferredWidth: 100
            compact: true
            enabled: !!dialog.controller && !dialog.working
            onClicked: dialog.controller.saveAs()
        }
        Components.AppButton {
            objectName: "saveWorkspace"
            text: "保存工作区"
            actionRole: "primary"
            Layout.preferredWidth: 110
            compact: true
            enabled: !!dialog.controller && !dialog.working
            onClicked: dialog.controller.save()
        }
    }
}
