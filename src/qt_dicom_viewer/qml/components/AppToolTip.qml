pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic as Basic
import "../theme"

Basic.ToolTip {
    id: tip
    // Explicit styling also applies to controls backed by the system light palette.
    popupType: Basic.Popup.Window
    delay: 500
    padding: 10
    margins: 8
    opacity: 1
    implicitWidth: Math.min(360, Math.max(80, (parent?.Window.window?.width ?? 376) - 16), label.implicitWidth + padding * 2)
    implicitHeight: label.implicitHeight + padding * 2
    contentItem: Text {
        id: label
        text: tip.text
        textFormat: Text.PlainText
        color: Theme.textPrimary
        font.pixelSize: 13
        wrapMode: Text.Wrap
        lineHeight: 1.2
    }
    background: Rectangle {
        color: Theme.elevatedBackground
        opacity: 1
        border.color: Theme.borderStrong
        radius: Theme.controlRadius
    }
}
