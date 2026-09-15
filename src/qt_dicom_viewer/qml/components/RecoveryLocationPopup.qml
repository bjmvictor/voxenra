pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../theme"
Basic.Popup {
    id: card
    objectName: "workspaceRecoveryLocationPopup"
    property var controller: null
    property bool copied: false
    readonly property bool hovered: hover.hovered
    // Keep the link and card in one hover surface; native popups grab the mouse.
    popupType: Basic.Popup.Item
    modal: false
    focus: false
    closePolicy: Basic.Popup.CloseOnEscape | Basic.Popup.CloseOnPressOutside
    width: 340
    height: content.implicitHeight + padding * 2
    padding: 12
    margins: 8
    x: (parent?.width ?? 0) - width
    y: -height - 6
    onAboutToShow: copied = false
    background: Rectangle { radius: 6; color: Theme.elevatedBackground; border.color: Theme.borderStrong }
    contentItem: ColumnLayout {
        id: content
        spacing: 10
        HoverHandler { id: hover }
        SelectableText {
            objectName: "workspaceRecoveryFullPath"
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: card.controller?.recoveryPath ?? ""
            font.pixelSize: 12
            color: Theme.textPrimary
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            AppButton {
                objectName: "workspaceRecoveryOpen"
                Layout.fillWidth: true
                compact: true
                iconName: "nav-load-file"
                text: qsTrId("workspace.openLocation")
                enabled: card.controller?.recoveryDirectoryAvailable ?? false
                onClicked: { card.close(); card.controller.openRecoveryDirectory() }
            }
            AppButton {
                objectName: "workspaceRecoveryCopy"
                Layout.fillWidth: true
                compact: true
                text: card.copied ? qsTrId("workspace.pathCopied") : qsTrId("workspace.copyPath")
                onClicked: { card.controller.copyRecoveryPath(); card.copied = true }
            }
        }
    }
}
