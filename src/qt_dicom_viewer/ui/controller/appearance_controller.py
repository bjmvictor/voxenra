"""One palette for QML, widget dialogs and native captions; image colors stay independent."""
from PySide6.QtCore import QObject, Property, Signal
from PySide6.QtGui import QGuiApplication, QPalette, QColor
from PySide6.QtCore import Qt

DARK = {'primaryColor': '#66d0ff',
 'primaryStrong': '#2a95e4',
 'primaryHover': '#7bd8ff',
 'primaryPressed': '#237fbd',
 'primarySoft': '#17354a',
 'primarySoftHover': '#1d425b',
 'secondaryColor': '#91a4b6',
 'secondaryStrong': '#61768a',
 'secondaryHover': '#a8bac9',
 'secondaryPressed': '#4d6072',
 'secondarySoft': '#28323c',
 'accentWarm': '#ff8a5b',
 'appBackground': '#101317',
 'shellBackground': '#101317',
 'panelBackground': '#171c22',
 'panelBackgroundSoft': '#14191f',
 'panelBackgroundStrong': '#1b2128',
 'workspaceBackground': '#0c0f13',
 'canvasBackground': '#050709',
 'cardBackground': '#1d242c',
 'cardBackgroundHover': '#252e38',
 'elevatedBackground': '#29333e',
 'borderSubtle': '#29313a',
 'borderDefault': '#36414d',
 'borderStrong': '#566675',
 'dividerColor': '#303a45',
 'focusBorder': '#66d0ff',
 'textPrimary': '#edf1f5',
 'textSecondary': '#c3ccd5',
 'textMuted': '#a1adb9',
 'textSubtle': '#909daa',
 'textDisabled': '#73808c',
 'textOnPrimary': '#f8fbff',
 'overlayText': '#eaf3fb',
 'overlayOutline': '#cc000000',
 'controlBackground': '#202831',
 'controlHover': '#2b3743',
 'controlPressed': '#17212b',
 'controlDisabled': '#1b2128',
 'controlBorder': '#3a4856',
 'controlHoverBorder': '#758b9d',
 'selectionBackground': '#203b4c',
 'selectionHover': '#28485b',
 'selectionPressed': '#173044',
 'selectionBorder': '#579fc6',
 'activeIndicator': '#66d0ff',
 'iconDefault': '#b0bfcc',
 'iconDisabled': '#73808c',
 'iconHover': '#dce8f1',
 'iconActive': '#66d0ff',
 'folderAccent': '#66d0ff',
 'folderSurface': '#17354a',
 'fusionAccent': '#77c8bb',
 'inputBorder': '#667888',
 'sliderTrack': '#667888',
 'primaryButtonBackground': '#21698f',
 'primaryButtonHover': '#2879a1',
 'primaryButtonPressed': '#195574',
 'primaryButtonDisabled': '#183344',
 'primaryButtonBorder': '#70c9ef',
 'infoColor': '#66d0ff',
 'infoSurface': '#123247',
 'successColor': '#7bd7a4',
 'successSurface': '#17392b',
 'warningColor': '#f3c66b',
 'warningSurface': '#3d3119',
 'dangerColor': '#ef7777',
 'dangerSurface': '#412124',
 'dangerButtonHover': '#5b2a2f',
 'dangerButtonPressed': '#32191d',
 'resetActionColor': '#f3c66b',
 'resetActionSurface': '#302819',
 'resetActionHover': '#40351e',
 'resetActionPressed': '#241e14',
 'resetActionBorder': '#8f7438',
 'measurementPrimary': '#ffd45c',
 'measurementSelected': '#66d0ff',
 'measurementHandle': '#f8fbff'}

LIGHT = {'primaryColor': '#2f6f97',
 'primaryStrong': '#245e85',
 'primaryHover': '#245e85',
 'primaryPressed': '#194866',
 'primarySoft': '#e1edf5',
 'primarySoftHover': '#d1e4f0',
 'secondaryColor': '#536d82',
 'secondaryStrong': '#405b70',
 'secondaryHover': '#3a586f',
 'secondaryPressed': '#2c485e',
 'secondarySoft': '#e1e9ef',
 'accentWarm': '#926123',
 'appBackground': '#e9f0f5',
 'shellBackground': '#e9f0f5',
 'panelBackground': '#f7fafc',
 'panelBackgroundSoft': '#eef4f8',
 'panelBackgroundStrong': '#e5edf3',
 'workspaceBackground': '#dbe6ee',
 'canvasBackground': '#050709',
 'cardBackground': '#f0f5f8',
 'cardBackgroundHover': '#e2ecf3',
 'elevatedBackground': '#f8fbfd',
 'borderSubtle': '#d0dce5',
 'borderDefault': '#becdd9',
 'borderStrong': '#839cad',
 'dividerColor': '#c5d4df',
 'focusBorder': '#2f6f97',
 'textPrimary': '#142235',
 'textSecondary': '#203245',
 'textMuted': '#435263',
 'textSubtle': '#526679',
 'textDisabled': '#84929e',
 'textOnPrimary': '#ffffff',
 'overlayText': '#eaf3fb',
 'overlayOutline': '#cc000000',
 'controlBackground': '#f7fafc',
 'controlHover': '#e4eef5',
 'controlPressed': '#d2e2ed',
 'controlDisabled': '#e4ebf0',
 'controlBorder': '#a9bdcc',
 'controlHoverBorder': '#65879f',
 'selectionBackground': '#dfedf6',
 'selectionHover': '#d1e4f0',
 'selectionPressed': '#c1d9e9',
 'selectionBorder': '#4f8fb8',
 'activeIndicator': '#2f6f97',
 'iconDefault': '#466075',
 'iconDisabled': '#91a0ab',
 'iconHover': '#244d69',
 'iconActive': '#2f6f97',
 'folderAccent': '#2f6f97',
 'folderSurface': '#e1edf5',
 'fusionAccent': '#237963',
 'inputBorder': '#829daf',
 'sliderTrack': '#9bb2c2',
 'primaryButtonBackground': '#2f6f97',
 'primaryButtonHover': '#245e85',
 'primaryButtonPressed': '#194866',
 'primaryButtonDisabled': '#cfdee8',
 'primaryButtonBorder': '#2b648a',
 'infoColor': '#2f6f97',
 'infoSurface': '#e1edf5',
 'successColor': '#176445',
 'successSurface': '#e3f1e9',
 'warningColor': '#80591a',
 'warningSurface': '#f8efd9',
 'dangerColor': '#a3303b',
 'dangerSurface': '#f9e8ea',
 'dangerButtonHover': '#f1d3d8',
 'dangerButtonPressed': '#e9bfc6',
 'resetActionColor': '#80591a',
 'resetActionSurface': '#f8efd9',
 'resetActionHover': '#f1e3bd',
 'resetActionPressed': '#e8d39e',
 'resetActionBorder': '#ab8b4d',
 'measurementPrimary': '#ffd45c',
 'measurementSelected': '#66d0ff',
 'measurementHandle': '#f8fbff'}

DARK.update(chartX='#41cce5', chartY='#f6bf66')
LIGHT.update(chartX='#176780', chartY='#80591a')

_current = None


def current_colors():
    from shiboken6 import isValid
    owner = _current() if _current is not None else None
    return owner.colors if owner is not None and isValid(owner) else dict(DARK)


class AppearanceController(QObject):
    changed = Signal()
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        global _current
        from weakref import ref
        _current = ref(self)
        self.settings = settings
        self._theme = settings.section('appearance')['theme']
        settings.sectionChanged.connect(self._setting_changed)
        self._apply()

    @Property(str, notify=changed)
    def theme(self): return self._theme

    @Property('QVariantMap', notify=changed)
    def colors(self): return dict(LIGHT if self._theme == 'light' else DARK)

    def _setting_changed(self, section):
        if section == 'appearance':
            theme = self.settings.section('appearance')['theme']
            if theme != self._theme:
                self._theme = theme
                self._apply()
                self.changed.emit()

    def _apply(self):
        app = QGuiApplication.instance()
        if app is None: return
        app.styleHints().setColorScheme(Qt.ColorScheme.Light if self._theme == 'light' else Qt.ColorScheme.Dark)
        c, palette = self.colors, QPalette()
        for role, key in {
            QPalette.Window: 'panelBackground', QPalette.WindowText: 'textPrimary',
            QPalette.Base: 'controlBackground', QPalette.AlternateBase: 'panelBackgroundSoft',
            QPalette.Text: 'textPrimary', QPalette.Button: 'controlBackground', QPalette.ButtonText: 'textPrimary',
            QPalette.Highlight: 'selectionBackground', QPalette.HighlightedText: 'textPrimary',
            QPalette.ToolTipBase: 'elevatedBackground', QPalette.ToolTipText: 'textPrimary',
            QPalette.Link: 'primaryColor', QPalette.PlaceholderText: 'textSubtle'
        }.items():
            palette.setColor(role, QColor(c[key]))
        for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
            palette.setColor(QPalette.Disabled, role, QColor(c['textDisabled']))
        app.setPalette(palette)
