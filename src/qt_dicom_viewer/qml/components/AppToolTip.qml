pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic as Basic
import "../theme"

Basic.ToolTip {
    id: tip
    property string placement: "above"
    readonly property real gap: 8
    readonly property var anchorWindow: parent?.Window.window ?? null
    readonly property point anchorPosition: {
        // Depend on the available geometry before Popup.Window is exposed.
        const revision = (parent?.x ?? 0) + (parent?.y ?? 0)
            + (anchorWindow?.width ?? 0) + (anchorWindow?.height ?? 0)
        return parent ? parent.mapToItem(null, 0, 0) : Qt.point(0, 0)
    }
    x: placement === "right" ? (parent?.width ?? 0) + gap
        : placement === "left" ? -width - gap
        : Math.max(8 - anchorPosition.x, Math.min((parent?.width ?? 0) / 2 - width / 2,
            (anchorWindow?.width ?? 376) - anchorPosition.x - width - 8))
    y: {
        const preferred = placement === "above" ? -height - gap : ((parent?.height ?? 0) - height) / 2
        return Math.max(8 - anchorPosition.y, Math.min(preferred,
            (anchorWindow?.height ?? 600) - anchorPosition.y - height - 8))
    }
    // Explicit styling also applies to controls backed by the system light palette.
    popupType: Basic.Popup.Window
    delay: 500
    padding: 10
    margins: 8
    opacity: 1
    implicitWidth: Math.min(360, Math.max(80, (parent?.Window.window?.width ?? 376) - 16), label.implicitWidth + padding * 2)
    implicitHeight: label.implicitHeight + padding * 2
    Binding {
        // ToolTip's native window otherwise draws a square platform frame
        // around our rounded background (especially visible in light mode).
        target: label.Window.window
        property: "flags"
        when: !!target && !!tip.parent && target !== tip.parent.Window.window
        value: Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
        restoreMode: Binding.RestoreNone
    }
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
