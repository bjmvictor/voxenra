pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../../components" as Components
import "../../theme"

ColumnLayout {
    id: page
    required property var settingsController
    readonly property var language: appController.languageController
    spacing: 12
    SettingsSection {
        Layout.fillWidth: true
        title: qsTrId("appearance.theme")
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Repeater {
                model: ["dark", "light"]
                delegate: Components.AppButton {
                    id: choice
                    required property string modelData
                    objectName: "themeChoice-" + modelData
                    Layout.fillWidth: true
                    Layout.maximumWidth: 220
                    Layout.preferredHeight: 92
                    checked: page.settingsController.values.appearance.theme === modelData
                    Accessible.name: modelData === "dark" ? qsTrId("appearance.dark") : qsTrId("appearance.light")
                    onClicked: page.settingsController.setValue("appearance", "theme", modelData)
                    contentItem: ColumnLayout {
                        spacing: 8
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 36
                            radius: 4
                            color: choice.modelData === "dark" ? "#171c22" : "#eef4f8"
                            border.color: choice.modelData === "dark" ? "#566675" : "#839cad"
                            Rectangle { x: 8; y: 8; width: 24; height: 20; radius: 2; color: choice.modelData === "dark" ? "#203b4c" : "#dfedf6" }
                            Rectangle { x: 38; y: 8; width: parent.width - 46; height: 20; radius: 2; color: "#050709" }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: choice.Accessible.name
                            color: Theme.textPrimary
                            font.pixelSize: 13
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                }
            }
        }
    }
    SettingsSection {
        Layout.fillWidth: true
        title: qsTrId("appearance.language")
        description: qsTrId("appearance.languageHint")
        Components.AppComboBox {
            id: languages
            objectName: "languageChoice"
            Layout.fillWidth: true
            Layout.maximumWidth: 320
            model: page.language.languages
            textRole: "name"
            valueRole: "locale"
            currentIndex: model.findIndex(item => item.locale === page.language.locale)
            onActivated: page.language.selectLanguage(currentValue)
        }
        Flow {
            Layout.fillWidth: true
            spacing: 8
            Components.AppButton { objectName: "openLanguageDirectory"; baseBorderWidth: 1; compact: true; text: qsTrId("appearance.openPacks"); onClicked: page.language.openDirectory() }
            Components.AppButton { objectName: "reloadLanguagePacks"; baseBorderWidth: 1; compact: true; text: qsTrId("appearance.reloadPacks"); onClicked: page.language.reload() }
        }
        Text { Layout.fillWidth: true; text: qsTrId("appearance.packsHint"); color: Theme.textMuted; font.pixelSize: 12; wrapMode: Text.Wrap }
        Text { objectName: "languagePackStatus"; Layout.fillWidth: true; Layout.minimumHeight: 36; text: page.language.message; color: Theme.textSecondary; font.pixelSize: 12; wrapMode: Text.Wrap }
    }
}
