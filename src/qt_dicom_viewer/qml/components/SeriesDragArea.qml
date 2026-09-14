pragma ComponentBehavior: Bound
import QtQuick
MouseArea {
    id: root
    property string seriesUid: ""
    required property var panelController
    property point pressPoint
    property bool draggingSeries: false
    onPressed: mouse => { pressPoint = Qt.point(mouse.x, mouse.y); draggingSeries = false }
    onPositionChanged: mouse => {
        if (!draggingSeries && seriesUid !== "" && (pressedButtons & Qt.LeftButton)
                && Math.abs(mouse.x - pressPoint.x) + Math.abs(mouse.y - pressPoint.y) >= Qt.styleHints.startDragDistance) {
            draggingSeries = true
            const uid = seriesUid
            Qt.callLater(() => root.panelController.startSeriesDrag(uid))
        }
    }
}
