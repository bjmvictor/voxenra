pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../../components" as Components
import "../../../theme"
Item {
    id: root
    required property var tabController
    readonly property var controller: tabController?.twoDLayout ?? null
    readonly property string focusedId: tabController?.focusedViewportId ?? ""
    function activeExportItem() {
        for (let i = 0; i < cells.count; ++i) {
            const cell = cells.itemAt(i)
            if (cell?.modelData.viewport === tabController?.activeViewport) return cell.exportItem
        }
        return null
    }
    GridLayout {
        anchors.fill: parent
        columns: root.controller?.columns ?? 1
        rows: root.controller?.rows ?? 1
        uniformCellWidths: true; uniformCellHeights: true
        columnSpacing: 3; rowSpacing: 3
        Repeater {
            id: cells
            model: root.controller?.cells ?? []
            delegate: Item {
                id: cell
                required property var modelData
                readonly property var view: modelData.viewport ?? null
                readonly property bool active: root.controller?.activeCell === modelData.index
                readonly property var exportItem: imageLoader.item
                objectName: "twoDCell-" + modelData.index
                visible: root.focusedId === "" || root.focusedId === view?.viewportId
                Layout.fillWidth: true; Layout.fillHeight: true
                Layout.minimumWidth: 0; Layout.minimumHeight: 0
                Layout.row: root.focusedId ? 0 : modelData.row
                Layout.column: root.focusedId ? 0 : modelData.column
                Layout.rowSpan: root.focusedId ? root.controller.rows : modelData.rowSpan
                Layout.columnSpan: root.focusedId ? root.controller.columns : modelData.columnSpan
                clip: true
                Rectangle {
                    id: heading
                    anchors.top: parent.top; anchors.left: parent.left; anchors.right: parent.right
                    height: 30
                    color: cell.active ? Theme.selectionBackground : Theme.panelBackground
                    Text {
                        anchors.left: parent.left; anchors.leftMargin: 6
                        anchors.right: plane.left; anchors.rightMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                        text: cell.modelData.label
                        // Series identity is supplied by the cell controller;
                        // do not expose Python implementation fields to QML.
                        textFormat: Text.PlainText
                        elide: Text.ElideRight
                        color: Theme.textSecondary
                        font.pixelSize: 11
                    }
                    TapHandler { onTapped: root.controller.activateCell(cell.modelData.index) }
                    Components.AppComboBox {
                        id: plane
                        objectName: "twoDPlane-" + cell.modelData.index
                        anchors.right: parent.right; anchors.rightMargin: 3
                        anchors.verticalCenter: parent.verticalCenter
                        width: Math.min(136, heading.width - 6); height: 26
                        font.pixelSize: 11
                        enabled: !!cell.view
                        model: [{label: qsTrId("layout.stack"), value: "stack"},
                                {label: qsTrId("layout.axial"), value: "axial"},
                                {label: qsTrId("layout.coronal"), value: "coronal"},
                                {label: qsTrId("layout.sagittal"), value: "sagittal"}]
                        textRole: "label"
                        currentIndex: model.findIndex(m => m.value === cell.modelData.mode)
                        onActivated: root.controller.setMode(cell.modelData.index, model[currentIndex].value)
                    }
                }
                Rectangle {
                    id: surface
                    anchors.top: heading.bottom; anchors.bottom: parent.bottom
                    anchors.left: parent.left; anchors.right: slider.visible ? slider.left : parent.right
                    color: Theme.canvasBackground
                    Loader {
                        id: imageLoader
                        anchors.fill: parent; anchors.margins: frame.contentInset
                        active: !!cell.view
                        sourceComponent: Component {
                            Viewport {
                                objectName: "imageViewport-" + cell.view.viewportId
                                viewportController: cell.view
                                hasTabs: true
                                multiViewport: cells.count > 1 && !root.focusedId
                            }
                        }
                    }
                    Text {
                        anchors.fill: parent; anchors.margins: 12
                        visible: !cell.view
                        text: qsTrId("layout.dropHere")
                        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.Wrap
                        color: Theme.textMuted; font.pixelSize: 12
                    }
                    ViewportFrame {
                        id: frame
                        objectName: "viewportFrame-" + (cell.view?.viewportId ?? "empty")
                        anchors.fill: parent
                        active: cell.active
                        hovered: hover.hovered || dropArea.containsDrag
                        z: 30
                    }
                    HoverHandler { id: hover }
                    TapHandler {
                        onPressedChanged: if (pressed) root.controller.activateCell(cell.modelData.index)
                        onDoubleTapped: {
                            if (cell.view && cells.count > 1)
                                root.tabController.focusSingleViewport(root.focusedId ? "" : cell.view.viewportId)
                        }
                    }
                }
                SliceSlider {
                    id: slider
                    anchors.top: surface.top; anchors.bottom: parent.bottom; anchors.right: parent.right
                    viewportController: cell.view
                    allowOrthogonal: true
                }
                Components.AppButton {
                    objectName: "twoDRetry-" + cell.modelData.index
                    anchors.horizontalCenter: surface.horizontalCenter
                    anchors.bottom: parent.bottom; anchors.bottomMargin: 12
                    visible: cell.view?.loadState === "error"
                    text: qsTrId("layout.retry")
                    compact: true
                    onClicked: root.controller.retryCell(cell.modelData.index)
                }
                DropArea {
                    id: dropArea
                    objectName: "twoDSeriesDrop-" + cell.modelData.index
                    anchors.fill: parent
                    keys: ["application/x-voxenra-series"]
                    onEntered: drag => drag.accept(Qt.CopyAction)
                    onDropped: drop => {
                        if (root.controller.loadSeries(cell.modelData.index, drop.getDataAsString("application/x-voxenra-series")))
                            drop.accept(Qt.CopyAction)
                    }
                }
                Rectangle {
                    anchors.fill: parent
                    visible: dropArea.containsDrag
                    color: Theme.selectionBackground; opacity: 0.25
                    border.width: 2; border.color: Theme.primaryColor
                }
            }
        }
    }
}
