pragma ComponentBehavior: Bound

import QtQuick
import "../../../components" as Components
import QtQuick.Controls.Basic as Basic
import "../../../theme"

Item {
    id: root

    required property var viewportController
    readonly property int sliceCount: viewportController?.sliceCount ?? 0

    function selectSlice(index) {
        if (!root.viewportController) return
        root.viewportController.workspaceTab?.activateViewport(root.viewportController.viewportId)
        root.viewportController.setSliceIndex(index)
    }

    implicitWidth: Math.max(32, maximumLabel.implicitWidth + 10)
    property bool allowOrthogonal: false
    visible: !!root.viewportController
        && (root.viewportController.viewportType === "stack" || root.allowOrthogonal)
        && root.sliceCount > 1

    Rectangle {
        anchors.fill: parent
        color: Theme.panelBackground
        radius: 4
    }

    Text {
        id: minimumLabel
        objectName: "sliceMinimum"
        anchors.top: parent.top
        anchors.topMargin: 3
        anchors.horizontalCenter: parent.horizontalCenter
        height: 20
        text: "1"
        color: Theme.textSecondary
        font.pixelSize: 11
        verticalAlignment: Text.AlignVCenter
        TapHandler { onTapped: root.selectSlice(0) }
    }
    Text {
        id: maximumLabel
        objectName: "sliceMaximum"
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 3
        anchors.horizontalCenter: parent.horizontalCenter
        height: 20
        text: String(root.sliceCount)
        color: Theme.textSecondary
        font.pixelSize: 11
        verticalAlignment: Text.AlignVCenter
        TapHandler { onTapped: root.selectSlice(Math.max(0, root.sliceCount - 1)) }
    }

    Basic.Slider {
        id: sliceControl
        objectName: "sliceControl"

        anchors.top: minimumLabel.bottom
        anchors.bottom: maximumLabel.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 4
        anchors.bottomMargin: 4
        leftPadding: 7
        rightPadding: 7

        orientation: Qt.Vertical
        // Qt 的垂直 Slider 默认把较大值放在上方。交换范围端点，
        // 让小索引位于顶部、大索引位于底部，同时 value 仍是实际索引。
        from: Math.max(0, root.sliceCount - 1)
        to: 0
        stepSize: 1
        snapMode: Basic.Slider.SnapAlways
        live: true
        // Range and index arrive in the same sliceChanged signal. Delay the
        // value update until the new range is installed, or Qt clamps an MPR
        // plane's initial middle slice against the previous zero-sized range.
        Binding {
            target: sliceControl
            property: "value"
            value: Math.max(0, Math.min(root.sliceCount - 1, root.viewportController?.sliceIndex ?? 0))
            delayed: true
        }

        onMoved: {
            if (!root.viewportController)
                return
            root.selectSlice(Math.round(sliceControl.value))
        }

        Components.AppToolTip {
            visible: sliceControl.hovered || sliceControl.pressed
            delay: 250
            text: Math.round(sliceControl.value) + 1
                + " / " + (root.viewportController
                    ? root.viewportController.sliceCount
                    : 0)
        }

        background: Rectangle {
            x: sliceControl.leftPadding
                + (sliceControl.availableWidth - width) / 2
            y: sliceControl.topPadding
            width: 4
            height: sliceControl.availableHeight
            radius: 2
            color: Theme.controlBackground
            border.width: 1
            border.color: Theme.controlBorder

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: sliceControl.visualPosition
                    * parent.height
                radius: parent.radius
                color: Theme.primaryStrong
            }
        }

        handle: Rectangle {
            x: sliceControl.leftPadding
                + (sliceControl.availableWidth - width) / 2
            y: sliceControl.topPadding
                + sliceControl.visualPosition
                    * (sliceControl.availableHeight - height)
            implicitWidth: 14
            implicitHeight: 14
            radius: width / 2
            color: sliceControl.pressed
                ? Theme.primaryPressed
                : sliceControl.hovered
                    ? Theme.primaryHover
                    : Theme.primaryColor
            border.width: 1
            border.color: Theme.textOnPrimary
        }
    }
}
