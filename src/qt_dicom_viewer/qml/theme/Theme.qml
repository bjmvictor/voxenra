pragma Singleton

import QtQuick

QtObject {
    readonly property var palette: typeof appController !== "undefined" && appController.appearanceController
        ? appController.appearanceController.colors : ({})

    // Brand colors: cold cyan is the main interaction color, while steel blue
    // is used for neutral secondary actions. Warm orange is intentionally rare.
    readonly property color primaryColor: palette.primaryColor ?? "#66d0ff"
    readonly property color primaryStrong: palette.primaryStrong ?? "#2a95e4"
    readonly property color primaryHover: palette.primaryHover ?? "#7bd8ff"
    readonly property color primaryPressed: palette.primaryPressed ?? "#237fbd"
    readonly property color primarySoft: palette.primarySoft ?? "#17354a"
    readonly property color primarySoftHover: palette.primarySoftHover ?? "#1d425b"

    readonly property color secondaryColor: palette.secondaryColor ?? "#91a4b6"
    readonly property color secondaryStrong: palette.secondaryStrong ?? "#61768a"
    readonly property color secondaryHover: palette.secondaryHover ?? "#a8bac9"
    readonly property color secondaryPressed: palette.secondaryPressed ?? "#4d6072"
    readonly property color secondarySoft: palette.secondarySoft ?? "#28323c"

    readonly property color accentWarm: palette.accentWarm ?? "#ff8a5b"

    // Surface hierarchy. Keep the DICOM canvas darker than application chrome.
    readonly property color appBackground: palette.appBackground ?? "#101317"
    readonly property color shellBackground: palette.shellBackground ?? "#101317"
    readonly property color panelBackground: palette.panelBackground ?? "#171c22"
    readonly property color panelBackgroundSoft: palette.panelBackgroundSoft ?? "#14191f"
    readonly property color panelBackgroundStrong: palette.panelBackgroundStrong ?? "#1b2128"
    readonly property color workspaceBackground: palette.workspaceBackground ?? "#0c0f13"
    readonly property color canvasBackground: palette.canvasBackground ?? "#050709"
    readonly property color cardBackground: palette.cardBackground ?? "#1d242c"
    readonly property color cardBackgroundHover: palette.cardBackgroundHover ?? "#252e38"
    readonly property color elevatedBackground: palette.elevatedBackground ?? "#29333e"

    // Image cards retain their contrast independently from application chrome.
    readonly property color overlayMuted: "#a1adb9"
    readonly property color overlayDivider: "#303a45"
    readonly property color overlayCard: "#e60d1722"
    readonly property color chartX: palette.chartX ?? "#41cce5"
    readonly property color chartY: palette.chartY ?? "#f6bf66"

    // Borders and separators.
    readonly property color borderSubtle: palette.borderSubtle ?? "#29313a"
    readonly property color borderDefault: palette.borderDefault ?? "#36414d"
    readonly property color borderStrong: palette.borderStrong ?? "#566675"
    readonly property color dividerColor: palette.dividerColor ?? "#303a45"
    readonly property color focusBorder: palette.focusBorder ?? "#66d0ff"

    // Typography.
    readonly property color textPrimary: palette.textPrimary ?? "#edf1f5"
    readonly property color textSecondary: palette.textSecondary ?? "#c3ccd5"
    readonly property color textMuted: palette.textMuted ?? "#a1adb9"
    readonly property color textSubtle: palette.textSubtle ?? "#909daa"
    readonly property color textDisabled: palette.textDisabled ?? "#73808c"
    readonly property color textOnPrimary: palette.textOnPrimary ?? "#f8fbff"
    readonly property color overlayText: palette.overlayText ?? "#eaf3fb"
    readonly property color overlayOutline: palette.overlayOutline ?? "#cc000000"

    // Generic controls.
    readonly property color controlBackground: palette.controlBackground ?? "#202831"
    readonly property color controlHover: palette.controlHover ?? "#2b3743"
    readonly property color controlPressed: palette.controlPressed ?? "#17212b"
    readonly property color controlDisabled: palette.controlDisabled ?? "#1b2128"
    readonly property color controlBorder: palette.controlBorder ?? "#3a4856"
    readonly property color controlHoverBorder: palette.controlHoverBorder ?? "#758b9d"

    // Selection / active interaction. A selected item is not a status message.
    readonly property color selectionBackground: palette.selectionBackground ?? "#203b4c"
    readonly property color selectionHover: palette.selectionHover ?? "#28485b"
    readonly property color selectionPressed: palette.selectionPressed ?? "#173044"
    readonly property color selectionBorder: palette.selectionBorder ?? "#579fc6"
    readonly property color activeIndicator: palette.activeIndicator ?? "#66d0ff"
    readonly property color iconDefault: palette.iconDefault ?? "#b0bfcc"
    readonly property color iconDisabled: palette.iconDisabled ?? "#73808c"
    readonly property color iconHover: palette.iconHover ?? "#dce8f1"
    readonly property color iconActive: palette.iconActive ?? "#66d0ff"

    // 两侧工具栏使用图标；完整操作名称由悬停和键盘焦点提示提供。
    readonly property int toolbarIconSize: 24
    readonly property int navigationIconSize: 28
    readonly property int toolbarLabelSize: 11
    readonly property int toolbarButtonHeight: 48
    readonly property int controlRadius: 6
    readonly property int bodyFontSize: 13

    readonly property color folderAccent: palette.folderAccent ?? "#66d0ff"
    readonly property color folderSurface: palette.folderSurface ?? "#17354a"
    readonly property color fusionAccent: palette.fusionAccent ?? "#77c8bb"
    readonly property int controlHeight: 32
    readonly property int compactControlHeight: 32
    readonly property color inputBorder: palette.inputBorder ?? "#667888"
    readonly property color sliderTrack: palette.sliderTrack ?? "#667888"

    // Primary command buttons, such as "Open DICOM folder".
    readonly property color primaryButtonBackground: palette.primaryButtonBackground ?? "#21698f"
    readonly property color primaryButtonHover: palette.primaryButtonHover ?? "#2879a1"
    readonly property color primaryButtonPressed: palette.primaryButtonPressed ?? "#195574"
    readonly property color primaryButtonDisabled: palette.primaryButtonDisabled ?? "#183344"
    readonly property color primaryButtonBorder: palette.primaryButtonBorder ?? "#70c9ef"

    // Semantic status colors. Use their surface variants for backgrounds.
    readonly property color infoColor: palette.infoColor ?? "#66d0ff"
    readonly property color infoSurface: palette.infoSurface ?? "#123247"
    readonly property color successColor: palette.successColor ?? "#7bd7a4"
    readonly property color successSurface: palette.successSurface ?? "#17392b"
    readonly property color warningColor: palette.warningColor ?? "#f3c66b"
    readonly property color warningSurface: palette.warningSurface ?? "#3d3119"
    readonly property color dangerColor: palette.dangerColor ?? "#ef7777"
    readonly property color dangerSurface: palette.dangerSurface ?? "#412124"
    readonly property color dangerButtonHover: palette.dangerButtonHover ?? "#5b2a2f"
    readonly property color dangerButtonPressed: palette.dangerButtonPressed ?? "#32191d"

    // 重置保留琥珀图标提示；常态使用中性表面，避免抢占影像注意力。
    readonly property color resetActionColor: palette.resetActionColor ?? "#f3c66b"
    readonly property color resetActionSurface: palette.resetActionSurface ?? "#302819"
    readonly property color resetActionHover: palette.resetActionHover ?? "#40351e"
    readonly property color resetActionPressed: palette.resetActionPressed ?? "#241e14"
    readonly property color resetActionBorder: palette.resetActionBorder ?? "#8f7438"

    // Measurement colors are separate from UI selection colors so overlays
    // remain visible on grayscale and pseudo-color images.
    readonly property color measurementPrimary: palette.measurementPrimary ?? "#ffd45c"
    readonly property color measurementSelected: palette.measurementSelected ?? "#66d0ff"
    readonly property color measurementHandle: palette.measurementHandle ?? "#f8fbff"
}
