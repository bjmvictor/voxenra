pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../components" as Components
import "../../theme"

ColumnLayout {
    id: shot
    required property string file
    property string caption: ""
    property real maximumPreviewHeight: 240
    readonly property url imageUrl: file ? "../../assets/help/" + file : ""
    spacing: 6
    visible: file !== ""
    Basic.Button {
        id: button
        objectName: "manualScreenshotButton"
        Layout.fillWidth: true
        Layout.preferredHeight: example.sourceSize.width > 0
            ? Math.min(shot.maximumPreviewHeight, width * example.sourceSize.height / example.sourceSize.width) : 0
        padding: 0
        hoverEnabled: true
        Accessible.name: I18n.format(qsTrId("manual.enlarge"), {caption: shot.caption})
        onClicked: preview.open()
        HoverHandler { cursorShape: Qt.PointingHandCursor }
        contentItem: Image {
            id: example
            objectName: "manualExample"
            source: shot.imageUrl
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
        }
        background: Rectangle {
            color: Theme.appBackground
            radius: 4
            border.width: button.hovered || button.visualFocus ? 1 : 0
            border.color: Theme.primaryColor
        }
        Components.AppToolTip { visible: button.hovered; text: qsTrId("text.0960") }
    }
    Components.SelectableText {
        Layout.fillWidth: true
        text: I18n.format(qsTrId("manual.caption"), {caption: shot.caption})
        textFormat: TextEdit.PlainText
        color: Theme.textMuted
        font.pixelSize: 11
        wrapMode: TextEdit.Wrap
    }
    Basic.Dialog {
        id: preview
        objectName: "manualScreenshotPreview"
        parent: Basic.Overlay.overlay
        anchors.centerIn: parent
        popupType: Basic.Popup.Window
        title: qsTrId("text.0962")
        implicitWidth: 1120
        implicitHeight: 800
        width: Math.min(implicitWidth, parent ? parent.width - 32 : implicitWidth)
        height: Math.min(implicitHeight, parent ? parent.height - 32 : implicitHeight)
        padding: 12
        modal: true
        focus: true
        closePolicy: Basic.Popup.CloseOnEscape
        onOpened: original.checked = false
        background: Rectangle { color: Theme.panelBackgroundStrong }
        // The native caption supplies the only close control.
        header: Item { implicitHeight: 0 }
        contentItem: Basic.ScrollView {
            id: scroll
            implicitWidth: 0
            implicitHeight: 0
            clip: true
            contentWidth: fullImage.width
            contentHeight: fullImage.height
            Basic.ScrollBar.horizontal: Basic.ScrollBar {
                height: 8
                padding: 1
                contentItem: Rectangle {
                    implicitWidth: 6; implicitHeight: 6
                    radius: 3
                    color: Theme.textSubtle
                }
            }
            Basic.ScrollBar.vertical: Components.AppScrollBar {}
            Image {
                id: fullImage
                objectName: "manualFullScreenshot"
                source: shot.imageUrl
                width: original.checked ? sourceSize.width : scroll.availableWidth
                height: original.checked ? sourceSize.height : scroll.availableHeight
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }
        }
        footer: RowLayout {
            implicitHeight: 44
            spacing: 12
            Components.SelectableText {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.leftMargin: 12
                text: shot.caption
                textFormat: TextEdit.PlainText
                color: Theme.textSecondary
                font.pixelSize: 12
                wrapMode: TextEdit.Wrap
            }
            Components.AppButton {
                id: original
                objectName: "manualScreenshotOriginalSize"
                Layout.rightMargin: 12
                compact: true
                checkable: true
                text: checked ? qsTrId("text.0963") : qsTrId("text.0964")
            }
        }
    }
}
