pragma ComponentBehavior: Bound
import QtQuick
import "../theme"

Item {
    id: indicator
    property var controller: null
    property bool badge: false
    property bool tooltipEnabled: true
    readonly property string status: controller?.recoveryState ?? "disabled"
    readonly property string statusText: controller?.recoveryStatusText ?? "自动恢复不可用"
    readonly property color statusColor: status === "saved" ? Theme.successColor
        : status === "error" ? Theme.dangerColor
        : ["pending", "recoverable"].includes(status) ? Theme.warningColor
        : status === "saving" ? Theme.primaryColor : Theme.textMuted
    implicitWidth: badge ? 12 : 20
    implicitHeight: implicitWidth
    Accessible.role: Accessible.StaticText
    Accessible.name: statusText
    Accessible.ignored: badge
    Rectangle {
        anchors.fill: parent
        radius: width / 2
        visible: indicator.badge
        color: Theme.panelBackgroundStrong
    }
    AppIcon {
        id: glyph
        anchors.centerIn: parent
        width: indicator.width - (indicator.badge ? 2 : 0)
        height: width
        iconName: ({saved: "check", saving: "reset", pending: "status-pending", recoverable: "reset",
            error: "close", disabled: "cine-pause", idle: "status-pending"})[indicator.status]
        iconColor: indicator.statusColor
    }
    RotationAnimation {
        target: glyph
        property: "rotation"
        from: 0; to: 360
        duration: 1100
        loops: Animation.Infinite
        running: indicator.visible && indicator.status === "saving"
        onStopped: glyph.rotation = 0
    }
    HoverHandler { id: hover }
    AppToolTip {
        visible: indicator.tooltipEnabled && hover.hovered
        text: indicator.statusText + "\n恢复副本：" + (indicator.controller?.recoveryPath ?? "")
    }
}
