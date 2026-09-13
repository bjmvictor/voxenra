pragma ComponentBehavior: Bound
import QtQuick
import "../../../../components" as Components
import QtQuick.Layouts
import QtQuick.Controls.Basic as Basic
import "../../../../theme"

Rectangle {
    id: root
    property var visibleMetrics: ({})
    property int metricFontSize: 13
    required property var measurement
    required property color accentColor
    readonly property var metrics: measurement.metrics ?? ({})
    readonly property var secondary: measurement.secondaryMetrics ?? null
    readonly property string unitSuffix: metrics.unit ? " " + metrics.unit : ""
    function format(value) {
        if (typeof value !== "number" || !Number.isFinite(value))
            return "—"
        const unit = String(metrics.unit ?? "")
        const isPetUnit = unit.indexOf("SUV") === 0
            || unit.indexOf("Bq/ml") >= 0
        if (!isPetUnit)
            return value.toFixed(1)
        return value.toFixed(Math.abs(value) < 1 ? 3 : 2)
    }
    readonly property var geometryRows: [
        {key: "dimensions", label: measurement.type === "ellipse" ? qsTrId("text.1003") : qsTrId("text.1004"), value: format(metrics.width_mm) + " × " + format(metrics.height_mm) + " mm"},
        {key: "area", label: qsTrId("text.1005"), value: format(metrics.area_mm2) + " mm²"}
    ].filter(row => root.visibleMetrics[row.key] !== false)
    readonly property var rows: [
        {key: "mean", label: qsTrId("text.0173"), value: format(metrics.mean) + unitSuffix},
        {key: "std", label: qsTrId("text.1006"), value: format(metrics.std) + unitSuffix},
        {key: "minimum", label: qsTrId("text.0174"), value: format(metrics.minimum) + unitSuffix},
        {key: "maximum", label: qsTrId("text.0175"), value: format(metrics.maximum) + unitSuffix},
        {key: "count", label: qsTrId("text.1007"), value: String(metrics.pixel_count ?? 0)}
    ].concat(secondary ? [
        {key: "mean", label: qsTrId("text.1008"), value: format(secondary.mean) + " HU"},
        {key: "std", label: qsTrId("text.1009"), value: format(secondary.std) + " HU"},
        {key: "minimum", label: qsTrId("text.1010"), value: format(secondary.minimum) + " HU"},
        {key: "maximum", label: qsTrId("text.1011"), value: format(secondary.maximum) + " HU"},
        {key: "count", label: qsTrId("text.1012"), value: String(secondary.pixel_count ?? 0)}
    ] : []).filter(row => root.visibleMetrics[row.key] !== false)
    TextMetrics {
        id: geometryMetrics
        font.pixelSize: root.metricFontSize
        text: root.geometryRows.map(row => row.value).join("   ")
    }
    implicitWidth: Math.max(238, geometryMetrics.advanceWidth + 32)
    implicitHeight: content.implicitHeight + 20
    height: implicitHeight
    radius: 6
    color: Qt.rgba(0.035, 0.065, 0.095, 0.92)
    border.width: 1
    border.color: Qt.rgba(accentColor.r, accentColor.g, accentColor.b, 0.55)

    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        spacing: 5
        Text {
            text: root.measurement.label ?? "ROI"
            color: root.accentColor
            font.pixelSize: root.metricFontSize
            font.weight: Font.DemiBold
        }
        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Theme.overlayDivider }
        Flow {
            id: geometryFlow
            Layout.fillWidth: true
            visible: root.geometryRows.length > 0
            spacing: 12
            Repeater {
                model: root.geometryRows
                delegate: Text {
                    id: geometryValue
                    required property var modelData
                    objectName: "roiGeometry-" + modelData.key
                    width: Math.min(implicitWidth, geometryFlow.width)
                    text: modelData.value
                    font.pixelSize: root.metricFontSize
                    color: Theme.overlayText
                    wrapMode: Text.Wrap
                    Accessible.name: modelData.label + " " + modelData.value
                    Components.AppToolTip {
                        text: geometryValue.modelData.label
                        visible: hover.hovered
                    }
                    HoverHandler { id: hover }
                }
            }
        }
        Repeater {
            model: root.rows
            RowLayout {
                id: metricRow
                required property var modelData
                Layout.fillWidth: true
                spacing: 8
                Text { Layout.minimumWidth: 0; Layout.preferredWidth: implicitWidth; wrapMode: Text.Wrap; text: metricRow.modelData.label; color: Theme.overlayMuted; font.pixelSize: root.metricFontSize }
                Text {
                    Layout.fillWidth: true
                    text: metricRow.modelData.value
                    color: Theme.overlayText
                    font.pixelSize: root.metricFontSize
                    horizontalAlignment: Text.AlignRight
                    wrapMode: Text.Wrap
                    Layout.minimumWidth: 0
                }
            }
        }
    }
}
