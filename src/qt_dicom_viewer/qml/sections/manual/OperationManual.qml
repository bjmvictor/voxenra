pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"
import "../center/viewportArea" as ViewportUi

Rectangle {
    id: manual
    objectName: "operationManual"
    required property var controller
    readonly property var article: controller?.currentChapter ?? ({})
    readonly property string chapter: controller?.chapterId ?? ""
    property bool restoring: true
    property bool active: true
    onActiveChanged: {
        if (active) restorePosition()
        else restoring = true
    }
    property bool petExample: false
    color: Theme.panelBackgroundStrong

    function revealChapter(button) {
        Qt.callLater(function() {
            if (!button.checked) return
            const scroller = navigationScroll.contentItem
            const top = button.mapToItem(scroller.contentItem, 0, 0).y
            const bottom = top + button.height
            if (top < scroller.contentY)
                scroller.contentY = top
            else if (bottom > scroller.contentY + scroller.height)
                scroller.contentY = bottom - scroller.height
        })
    }

    function restorePosition() {
        restoring = true
        restoreTimer.restart()
    }
    Timer {
        id: restoreTimer
        // Incubation completes before wrapped text and images finish layout.
        // Restore only after their geometry has settled, without saving the
        // temporary zero/clamped offset back into the chapter controller.
        interval: 16
        onTriggered: {
            if (!manual.controller || !manual.active) return
            readingArea.contentY = Math.max(0, Math.min(manual.controller.scrollPosition,
                readingArea.contentHeight - readingArea.height))
            manual.restoring = false
        }
    }
    Component.onCompleted: restorePosition()
    Connections {
        target: manual.controller
        function onChapterChanged() { manual.restorePosition() }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            id: navigation
            objectName: "manualNavigation"
            Layout.preferredWidth: manual.width < 760 ? 154 : 190
            Layout.fillHeight: true
            color: Theme.panelBackground
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10
                RowLayout {
                    Components.AppIcon { iconName: "manual"; iconSize: 18; iconColor: Theme.primaryColor }
                    Text { text: qsTrId("text.0495"); color: Theme.textPrimary; font.pixelSize: 16; font.weight: Font.DemiBold }
                }
                Components.AppTextField {
                    id: search
                    objectName: "manualSearch"
                    Layout.fillWidth: true
                    placeholderText: qsTrId("text.0949")
                    text: manual.controller?.search ?? ""
                    onTextEdited: manual.controller?.setSearch(text)
                }
                Basic.ScrollView {
                    id: navigationScroll
                    objectName: "manualNavigationScroll"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: availableWidth
                    rightPadding: 10
                    clip: true
                    Basic.ScrollBar.vertical: Components.AppScrollBar {}
                    Basic.ScrollBar.horizontal.policy: Basic.ScrollBar.AlwaysOff
                    ColumnLayout {
                        width: navigationScroll.availableWidth
                        spacing: 4
                        Repeater {
                            model: manual.controller?.navigation ?? []
                            delegate: ColumnLayout {
                                id: categoryEntry
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.minimumWidth: 0
                                spacing: 3
                                Text {
                                    objectName: "manualCategory-" + categoryEntry.modelData.id
                                    Layout.fillWidth: true
                                    Layout.topMargin: 10
                                    Layout.bottomMargin: 4
                                    text: categoryEntry.modelData.title
                                    color: Theme.textMuted
                                    font.pixelSize: 11
                                    wrapMode: Text.Wrap
                                }
                                Repeater {
                                    model: categoryEntry.modelData.chapters
                                    delegate: Components.AppButton {
                                        id: chapterButton
                                        required property var modelData
                                        objectName: "manualChapter-" + modelData.id
                                        Layout.fillWidth: true
                                        implicitHeight: Math.max(32, chapterTitle.implicitHeight + 12)
                                        minimumButtonWidth: 0
                                        leftPadding: 8
                                        rightPadding: 8
                                        momentary: true
                                        normalColor: "transparent"
                                        activeBorderColor: "transparent"
                                        checked: manual.chapter === modelData.id
                                        onCheckedChanged: if (checked) manual.revealChapter(chapterButton)
                                        Component.onCompleted: if (checked) manual.revealChapter(chapterButton)
                                        Accessible.name: categoryEntry.modelData.title + " · " + modelData.title
                                        onClicked: manual.controller.selectChapter(modelData.id)
                                        contentItem: Text {
                                            id: chapterTitle
                                            text: chapterButton.modelData.title
                                            color: chapterButton.checked ? Theme.primaryColor : Theme.textSecondary
                                            font.pixelSize: 12
                                            wrapMode: Text.Wrap
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                    }
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: (manual.controller?.navigation.length ?? 0) === 0
                            text: qsTrId("text.0950")
                            color: Theme.textMuted
                            font.pixelSize: 12
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }
        }
        Flickable {
            id: readingArea
            objectName: "manualReadingArea"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            contentWidth: width
            contentHeight: readingContent.implicitHeight + 40
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            onMovementStarted: { restoreTimer.stop(); manual.restoring = false }
            onContentHeightChanged: if (manual.active && manual.restoring) restoreTimer.restart()
            onHeightChanged: if (manual.active && manual.restoring) restoreTimer.restart()
            onContentYChanged: if (manual.active && !manual.restoring) manual.controller?.setScrollPosition(contentY)
            Basic.ScrollBar.vertical: Components.AppScrollBar {}
            ColumnLayout {
                id: readingContent
                x: (readingArea.width - width) / 2; y: 20
                width: Math.min(900, Math.max(1, readingArea.width - 48))
                spacing: 16
                Text {
                    Layout.fillWidth: true
                    text: qsTrId("text.0951") + (manual.article.categoryTitle ?? "")
                    color: Theme.textMuted
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                }
                Text {
                    objectName: "manualChapterTitle"
                    Layout.fillWidth: true
                    text: manual.article.title ?? ""
                    color: Theme.textPrimary
                    font.pixelSize: 22
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                }
                Text {
                    objectName: "manualChapterSummary"
                    Layout.fillWidth: true
                    text: manual.article.summary ?? ""
                    textFormat: Text.PlainText
                    color: Theme.textMuted
                    font.pixelSize: 13
                    wrapMode: Text.Wrap
                }
                Flow {
                    objectName: "manualShortcuts"
                    Layout.fillWidth: true
                    visible: (manual.article.shortcuts?.length ?? 0) > 0
                    spacing: 8
                    Repeater {
                        model: manual.article.shortcuts ?? []
                        delegate: Rectangle {
                            id: shortcut
                            required property var modelData
                            required property int index
                            objectName: "manualShortcut-" + index
                            readonly property string keys: Qt.platform.os === "osx"
                                ? modelData.mac : modelData.keys
                            width: Math.min(shortcutRow.implicitWidth + 20, parent.width)
                            height: 30
                            radius: 5
                            color: Theme.controlBackground
                            Accessible.role: Accessible.StaticText
                            Accessible.name: modelData.label + " " + keys
                            RowLayout {
                                id: shortcutRow
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                spacing: 8
                                Text { text: shortcut.modelData.label; color: Theme.textSecondary; font.pixelSize: 12 }
                                Text {
                                    text: shortcut.keys
                                    color: Theme.primaryColor
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                }
                            }
                        }
                    }
                }
                RowLayout {
                    visible: (manual.article.examples?.length ?? 0) > 0
                    Text { text: qsTrId("text.0952"); color: Theme.textMuted; font.pixelSize: 11 }
                    Components.AppButton { text: "CT"; compact: true; checked: !manual.petExample; onClicked: manual.petExample = false }
                    Components.AppButton { text: "PET"; compact: true; checked: manual.petExample; onClicked: manual.petExample = true }
                }
                ManualScreenshot {
                    Layout.fillWidth: true
                    maximumPreviewHeight: readingArea.height < 620 ? 180 : 240
                    file: manual.article.example
                        ?? ((manual.article.examples?.length ?? 0) > 0 ? manual.article.examples[manual.petExample ? 1 : 0] : "")
                    caption: manual.article.caption ?? qsTrId("text.0952")
                }
                VoiManualFigure {
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? width * 220 / 760 : 0
                    visible: !!manual.article.figure
                    chapter: manual.article.figure ?? ""
                }
                Repeater {
                    model: manual.article.sections ?? []
                    delegate: Rectangle {
                        id: step
                        required property var modelData
                        required property int index
                        objectName: "manualSection-" + index
                        readonly property bool important: modelData.important ?? false
                        Layout.fillWidth: true
                        implicitHeight: sectionContent.implicitHeight + (important ? 20 : 0)
                        color: important ? Theme.selectionBackground : "transparent"
                        radius: 5
                        Rectangle {
                            visible: step.important
                            width: 3
                            height: parent.height
                            radius: 1
                            color: Theme.primaryColor
                        }
                        ColumnLayout {
                            id: sectionContent
                            x: step.important ? 14 : 0
                            y: step.important ? 10 : 0
                            width: step.width - (step.important ? 28 : 0)
                            spacing: 6
                            Text {
                                Layout.fillWidth: true
                                text: step.modelData.title
                                textFormat: Text.PlainText
                                color: Theme.textPrimary
                                font.pixelSize: 15
                                font.weight: Font.DemiBold
                                wrapMode: Text.Wrap
                            }
                            Text {
                                objectName: "manualSectionBody-" + step.index
                                Layout.fillWidth: true
                                text: step.modelData.bodyHtml
                                textFormat: Text.StyledText
                                color: Theme.textSecondary
                                font.pixelSize: 13
                                lineHeight: 1.45
                                wrapMode: Text.Wrap
                            }
                        }
                    }
                }
                GridLayout {
                    Layout.fillWidth: true
                    visible: manual.article.cursorLegend ?? false
                    columns: width < 600 ? 2 : 3
                    columnSpacing: 8; rowSpacing: 8
                    Repeater {
                        model: [{key:"segmentation",label:qsTrId("text.0953")}, {key:"voi",label:qsTrId("text.0954")},
                            {key:"pan",label:qsTrId("text.0955")}, {key:"resize",label:qsTrId("text.0956")},
                            {key:"crosshair-move",label:qsTrId("text.0957")}, {key:"crosshair-rotate",label:qsTrId("text.0958")},
                            {key:"window",label:qsTrId("text.0285")}, {key:"zoom",label:qsTrId("text.0033")}, {key:"scroll",label:qsTrId("text.0287")}]
                        delegate: Rectangle {
                            id: legend
                            required property var modelData
                            Layout.fillWidth: true
                            implicitHeight: 50
                            color: Theme.panelBackground
                            radius: 4
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 8
                                ViewportUi.CursorGlyph {
                                    visible: true
                                    Layout.preferredWidth: 40; Layout.preferredHeight: 32; iconName: legend.modelData.key
                                }
                                Text { Layout.fillWidth: true; text: legend.modelData.label; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.Wrap }
                            }
                        }
                    }
                }
                Flow {
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                        model: manual.article.relatedChapters ?? []
                        delegate: Components.AppLinkButton {
                            required property var modelData
                            objectName: "manualRelated-" + modelData.id
                            text: modelData.title + " →"
                            onClicked: manual.controller.selectChapter(modelData.id)
                        }
                    }
                }
            }
        }
    }
}
