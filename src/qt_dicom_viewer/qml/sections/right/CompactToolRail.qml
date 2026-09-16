pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import "../../components" as Components
import "../../theme"
Flickable {
    id: rail
    objectName: "compactToolRail"
    required property var toolController
    required property var viewportController
    property var tabController: null
    property string expandedTool: ""
    signal panelRequested(string tool)
    readonly property var directTools: ["window", "ct-window", "pet-window", "scroll", "pan", "zoom", "volume-rotate", "mpr-rotate-3d"]
    readonly property var groupedTools: ["rotate", "measure", "annotate", "pseudocolor", "volume-direction"]
    readonly property var panelTools: viewportController?.viewportType === "volume"
        ? ["volume-preset", "mpr-layout"] : []
    contentWidth: width
    contentHeight: entries.height + 8
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    Basic.ScrollBar.vertical: Components.AppScrollBar { width: 3 }
    onToolControllerChanged: expandedTool = ""
    onVisibleChanged: if (!visible) expandedTool = ""
    Connections {
        target: rail.toolController ?? null
        function onActiveToolChanged() {
            if (rail.expandedTool !== rail.toolController.activeTool)
                rail.expandedTool = ""
        }
    }
    function childrenFor(tool) {
        if (tool === "volume-direction") return (viewportController?.directionOptions ?? []).map(d => ({
            action: d.face, label: d.label, iconName: "volume-direction", face: d.face, color: d.color}))
        if (tool === "measure") return toolController?.measureActions ?? []
        if (tool === "rotate") return toolController?.rotateActions ?? []
        if (tool === "annotate") return [
            {action: "annotate:arrow", label: qsTrId("text.0377"), iconName: "annotate-arrow"},
            {action: "annotate:text", label: qsTrId("text.0378"), iconName: "annotate-text"}]
        if (tool === "pseudocolor") return (viewportController?.colorMapOptions ?? []).map(c => ({
            action: c.colorMap, label: c.label, iconName: "pseudocolor", stops: c.stops}))
        return []
    }
    function activateGroup(tool) {
        if (["play", "slice-play"].includes(tool)) {
            toolController.activateTool(tool)
            tabController?.togglePlaybackMode(tool === "slice-play" || !tabController.temporalPlayback ? "slice" : "phase")
        } else if (panelTools.includes(tool)) {
            expandedTool = ""
            toolController.activateTool(tool)
            rail.panelRequested(tool)
        } else if (groupedTools.includes(tool)) {
            const close = expandedTool === tool
            toolController.activateTool(tool)
            expandedTool = close ? "" : tool
        } else {
            expandedTool = ""
            toolController.activateDirectTool(tool)
        }
    }
    function activateChild(tool, action) {
        if (tool === "volume-direction") viewportController.setViewFace(action)
        else if (tool === "rotate") viewportController.applyTransformAction(action)
        else if (tool === "pseudocolor") viewportController.applyColorMap(action)
        else if (tool === "annotate") viewportController.setAnnotationMode(action === "annotate:text")
        else toolController.selectInteraction(action)
    }
    Column {
        id: entries
        y: 4
        width: rail.width
        spacing: 4
        Repeater {
            model: (rail.toolController?.tools ?? []).filter(t => t.available !== false &&
                (["play", "slice-play"].includes(t.toolType) || rail.directTools.includes(t.toolType) || rail.groupedTools.includes(t.toolType)
                    || rail.panelTools.includes(t.toolType)))
            delegate: Column {
                id: group
                required property var modelData
                readonly property bool playback: ["play", "slice-play"].includes(modelData.toolType)
                readonly property string playMode: modelData.toolType === "slice-play" || !rail.tabController?.temporalPlayback ? "slice" : "phase"
                readonly property bool running: playback && !!rail.tabController?.playing && rail.tabController.playbackMode === playMode
                width: entries.width
                spacing: 4
                bottomPadding: secondary.visible ? 10 : 0
                Components.ToolbarAction {
                    width: 40; height: 38
                    x: (group.width - width) / 2
                    buttonObjectName: "compactTool-" + group.modelData.toolType
                    tooltipPlacement: "left"
                    label: group.running
                        ? qsTrId("playback.stop") : group.modelData.label
                    iconName: group.running
                        ? (group.playMode === "phase" ? "cine-4d-stop" : "cine-stop") : group.modelData.iconName
                    iconSize: 22
                    directionFace: group.modelData.toolType === "volume-direction" ? rail.viewportController?.currentFace ?? "A" : ""
                    directionColor: rail.viewportController?.currentFaceColor ?? Theme.iconDefault
                    checked: group.playback ? group.running
                        : rail.toolController?.activeTool === group.modelData.toolType
                    actionEnabled: !!rail.viewportController && group.modelData.enabled !== false
                        && (!rail.tabController?.playing || group.playback)
                        && (!group.playback || group.running || (group.playMode === "phase" ? (rail.tabController?.phaseCount ?? 0) > 1 : !!rail.tabController?.slicePlaybackAvailable))
                    onTriggered: rail.activateGroup(group.modelData.toolType)
                    Rectangle {
                        visible: rail.groupedTools.includes(group.modelData.toolType) || rail.panelTools.includes(group.modelData.toolType)
                        anchors.right: parent.right; anchors.bottom: parent.bottom
                        anchors.margins: 3
                        width: 4; height: 4; radius: 1
                        color: rail.expandedTool === group.modelData.toolType ? Theme.primaryColor : Theme.textMuted
                    }
                }
                Rectangle {
                    id: secondary
                    objectName: "compactGroup-" + group.modelData.toolType
                    x: 2
                    width: group.width - 4
                    height: visible ? subbuttons.height + 12 : 0
                    visible: rail.expandedTool === group.modelData.toolType
                    radius: 5
                    color: Theme.secondarySoft
                    Column {
                        id: subbuttons
                        x: (secondary.width - width) / 2
                        y: 6
                        width: 32
                        spacing: 4
                        Repeater {
                            model: secondary.visible ? rail.childrenFor(group.modelData.toolType) : []
                            delegate: Components.ToolbarAction {
                                id: child
                                required property var modelData
                                width: 32; height: 32
                                buttonObjectName: "compactAction-" + modelData.action
                                label: modelData.label
                                iconName: modelData.iconName
                                iconSize: 19
                                directionFace: modelData.face ?? ""
                                directionColor: modelData.color ?? Theme.iconDefault
                                tooltipPlacement: "left"
                                actionEnabled: !!rail.viewportController && !rail.tabController?.playing
                                    && (group.modelData.toolType !== "volume-direction" || rail.viewportController.loadState === "ready")
                                checked: group.modelData.toolType === "volume-direction"
                                    ? rail.viewportController?.currentFace === modelData.action
                                    : group.modelData.toolType === "pseudocolor"
                                    ? rail.viewportController?.activeColorMap === modelData.action
                                    : rail.toolController?.activeInteraction === modelData.action
                                onTriggered: rail.activateChild(group.modelData.toolType, modelData.action)
                                Canvas {
                                    visible: !!child.modelData.stops
                                    anchors.centerIn: parent
                                    width: 24; height: 16
                                    onPaint: {
                                        if (!child.modelData.stops) return
                                        const ctx = getContext("2d")
                                        ctx.reset()
                                        const gradient = ctx.createLinearGradient(0, 0, width, 0)
                                        for (const stop of child.modelData.stops) gradient.addColorStop(stop.position, stop.color)
                                        ctx.fillStyle = gradient
                                        ctx.fillRect(0, 0, width, height)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
