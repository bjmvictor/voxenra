pragma ComponentBehavior: Bound
import QtQuick

Canvas {
    id: figure
    objectName: "voiManualFigure"
    required property string chapter
    implicitHeight: 220
    readonly property string languageMarker: qsTrId("text.0931")
    onLanguageMarkerChanged: requestPaint()
    onChapterChanged: requestPaint()
    onWidthChanged: requestPaint()
    onPaint: {
        const c = getContext("2d")
        c.reset()
        const scale = width / 760
        c.scale(scale, scale)
        c.fillStyle = "#111c26"
        c.fillRect(0, 0, 760, 220)
        c.lineWidth = 2
        function label(text, x, y, color) {
            c.fillStyle = color || "#c9d5df"
            c.font = "13px sans-serif"
            c.fillText(text, x, y)
        }
        function line(x1, y1, x2, y2, color) {
            c.strokeStyle = color
            c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke()
        }
        function ellipse(x, y, rx, ry, color) {
            c.save(); c.translate(x, y); c.scale(rx, ry)
            c.beginPath(); c.arc(0, 0, 1, 0, 2 * Math.PI)
            c.restore()
            c.fillStyle = "#333745"; c.fill()
            c.strokeStyle = color; c.stroke()
        }
        if (chapter === "segmentation") {
            c.strokeStyle = "#ed55ed"
            c.fillStyle = "#303040"
            c.fillRect(66, 80, 180, 100); c.strokeRect(66, 80, 180, 100)
            c.strokeRect(113, 43, 180, 100)
            line(66,80,113,43,"#ed55ed"); line(246,80,293,43,"#ed55ed")
            line(246,180,293,143,"#ed55ed")
            label(qsTrId("text.0928"), 118, 204)
            label(qsTrId("text.0929"), 6, 129)
            label(qsTrId("text.0930"), 242, 35, "#62c9ec")
            label(qsTrId("text.0931"), 391, 78, "#62c9ec")
            label(qsTrId("text.0932"), 391, 113)
            label(qsTrId("text.0933"), 391, 145)
            label(qsTrId("text.0934"), 391, 177)
        } else if (chapter === "voi") {
            ellipse(118, 110, 67, 67, "#ed55ed")
            line(118,110,185,110,"#62c9ec")
            ellipse(118,110,3,3,"#62c9ec")
            label(qsTrId("text.0935"), 75, 22)
            label(qsTrId("text.0936"), 122, 102, "#62c9ec")
            label(qsTrId("text.0937"), 32, 206)
            ellipse(385, 110, 67, 39, "#62c9ec")
            label(qsTrId("text.0938"), 300, 206)
            ellipse(625, 92, 61, 61, "#ed55ed")
            ellipse(625, 92, 33, 33, "#62c9ec")
            label(qsTrId("text.0939"), 540, 206)
        } else if (chapter === "quantification") {
            label(qsTrId("text.0940"), 38, 28)
            for (let i=0; i<12; ++i) {
                const h = 18 + ((i*37)%90)
                c.fillStyle = i >= 6 ? "#ed55ed" : "#526576"
                c.fillRect(40+i*22, 166-h, 17, h)
            }
            line(169,42,169,178,"#62c9ec")
            label(qsTrId("text.0941"), 152, 199, "#62c9ec")
            label("CT：HU ≥ 300", 368, 65, "#ed55ed")
            label(qsTrId("text.0942"), 368, 99, "#ed55ed")
            label(qsTrId("text.0943"), 368, 141)
            label(qsTrId("text.0944"), 368, 177)
        } else {
            c.fillStyle = "#263744"; c.fillRect(60, 37, 640, 46)
            label(qsTrId("text.0945"), 81, 65)
            c.strokeStyle = "#62c9ec"; c.strokeRect(60, 122, 310, 42)
            c.strokeRect(389, 122, 310, 42)
            label(qsTrId("text.0946"), 135, 148)
            label(qsTrId("text.0947"), 454, 148)
            label(qsTrId("text.0948"), 106, 204)
        }
    }
}
