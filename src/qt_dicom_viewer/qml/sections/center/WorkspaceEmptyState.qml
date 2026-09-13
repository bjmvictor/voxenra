pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

Item {
    id: emptyState
    objectName: "workspaceEmptyState"

    required property var panelController
    property var pacsController: null
    property var workspaceController: null

    readonly property bool scanning:
        emptyState.panelController?.scanning ?? false
    readonly property int seriesCount:
        emptyState.panelController?.seriesItems?.length ?? 0
    readonly property bool hasSeries: seriesCount > 0

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(440, Math.max(220, emptyState.width - 72))
        spacing: 12

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 64
            Layout.preferredHeight: 64

            radius: 18
            color: Theme.primarySoft
            border.color: Theme.selectionBorder
            border.width: 1

            Components.AppIcon {
                objectName: "homeFolderIcon"
                anchors.centerIn: parent
                visible: !emptyState.hasSeries
                iconName: "nav-load-file"
                iconSize: 30
                iconColor: Theme.primaryColor
                opacity: emptyState.scanning ? 0.55 : 1
            }

            Text {
                anchors.centerIn: parent
                visible: emptyState.hasSeries
                text: emptyState.seriesCount
                color: Theme.primaryHover
                font.pixelSize: 21
                font.weight: Font.DemiBold
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.topMargin: 4

            text: {
                if (emptyState.scanning && !emptyState.hasSeries)
                    return qsTrId("text.0917")
                if (emptyState.hasSeries)
                    return qsTrId("text.0918")
                return qsTrId("text.0919")
            }
            color: Theme.textPrimary
            font.pixelSize: 22
            font.weight: Font.DemiBold
            horizontalAlignment: Text.AlignHCenter
        }

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 92
            Layout.preferredHeight: 1
            color: Theme.selectionBorder
            opacity: 0.8
        }

        Text {
            Layout.fillWidth: true

            text: {
                if (emptyState.scanning && !emptyState.hasSeries)
                    return qsTrId("text.0920")
                if (emptyState.hasSeries)
                    return I18n.format(qsTrId("workspace.seriesFound"), {count: emptyState.seriesCount})
                return emptyState.pacsController && emptyState.pacsController.pacsEnabled
                    ? (emptyState.pacsController.localEnabled
                        ? qsTrId("text.0923")
                        : qsTrId("text.0924"))
                    : qsTrId("text.0925")
            }
            color: Theme.textMuted
            font.pixelSize: 13
            lineHeight: 1.45
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }

        Components.AppButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 8
            Layout.preferredWidth: 168

            visible: !emptyState.hasSeries && (!emptyState.pacsController || emptyState.pacsController.localEnabled)
            enabled: true
            text: emptyState.scanning ? qsTrId("text.0620") : qsTrId("text.0926")
            id: openImport
            objectName: "homeOpenImport"
            iconName: "nav-load-file"
            iconSize: 17
            normalColor: Theme.primaryButtonBackground
            hoverColor: Theme.primaryButtonHover
            pressedColor: Theme.primaryButtonPressed
            disabledColor: Theme.primaryButtonDisabled
            focusBorderColor: Theme.primaryButtonBorder
            textColor: Theme.textOnPrimary

            onClicked: emptyState.panelController.openImportDialog()
        }
        Components.AppButton {
            objectName: "homeOpenPacs"
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 168
            visible: emptyState.pacsController && emptyState.pacsController.pacsEnabled
            text: qsTrId("text.0927")
            iconName: "nav-pacs"
            iconSize: 17
            normalColor: Theme.primaryButtonBackground
            hoverColor: Theme.primaryButtonHover
            pressedColor: Theme.primaryButtonPressed
            disabledColor: Theme.primaryButtonDisabled
            focusBorderColor: Theme.primaryButtonBorder
            textColor: Theme.textOnPrimary
            onClicked: emptyState.workspaceController.openPacs()
        }

    }
}
