"""User-editable JSON translations backed by Qt's live retranslation support."""
from qt_dicom_viewer.i18n.messages import error_message
import json
import re
from pathlib import Path
from weakref import WeakSet
from PySide6.QtCore import QObject, Property, Signal, Slot, QTranslator, QCoreApplication, QStandardPaths
from qt_dicom_viewer.i18n import messages as text
from qt_dicom_viewer.i18n.qt import refresh_properties, refresh_models
from qt_dicom_viewer.ui.file_location import reveal_path


class JsonTranslator(QTranslator):
    def __init__(self, owner):
        super().__init__(owner)
        self.set_messages(owner.messages)

    def set_messages(self, messages):
        from qt_dicom_viewer.i18n.qt_catalog import encode_catalog
        data = encode_catalog(messages)
        if not self.load(data):
            raise ValueError('Cannot load validated translation catalog')
        self._data = data  # Qt references this buffer until the next load.


class LanguageController(QObject):
    changed = Signal()
    languagesChanged = Signal()
    messageChanged = Signal()

    def __init__(self, settings, parent=None, *, root=None):
        super().__init__(parent)
        self.settings = settings
        self._external_enabled = root is not False
        self.root = Path(root) if root not in (None, False) else Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)) / 'languages'
        self._packs = {key: text.builtin(key) for key in ('zh-CN', 'en-US')}
        self._message = ''
        self._engines = WeakSet()
        self._locale = 'zh-CN'
        self.messages = dict(self._packs['zh-CN']['messages'])
        self._translator = JsonTranslator(self)
        app = QCoreApplication.instance()
        if app is not None: app.installTranslator(self._translator)
        text._active = self
        self._scan()
        requested = settings.section('appearance')['language']
        self._activate(requested if requested in self._packs else 'zh-CN')
        settings.sectionChanged.connect(self._setting_changed)

    @Property(str, notify=changed)
    def locale(self): return self._locale

    @Property('QVariantList', notify=languagesChanged)
    def languages(self):
        return [dict(locale=k, name=v['name']) for k,v in self._packs.items()]

    @Property(str, notify=messageChanged)
    def message(self): return text.localize(self._message, self.messages)

    @Property(str, constant=True)
    def directory(self): return str(self.root)

    def attach_engine(self, engine):
        if engine is not None: self._engines.add(engine)

    def _status(self, message):
        self._message = message
        self.messageChanged.emit()

    def _scan(self):
        packs = {key: text.builtin(key) for key in ('zh-CN', 'en-US')}
        errors = []
        for path in sorted(self.root.glob('*.json')) if self._external_enabled and self.root.is_dir() else []:
            try:
                if path.stat().st_size > 8 * 1024**2: raise ValueError('Pack too large')
                pack = json.loads(path.read_text(encoding='utf-8'))
                locale = pack['locale']
                if (type(pack['formatVersion']) is not int or pack['formatVersion'] != 1 or not isinstance(locale, str)
                        or not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*', locale)
                        or path.stem != locale or not isinstance(pack['name'], str)
                        or not pack['name'].strip() or len(pack['name']) > 80
                        or not isinstance(pack['messages'], dict)):
                    raise ValueError('Invalid metadata')
                pack['name'].encode('utf-8')
                base = text.builtin(locale if locale in ('zh-CN', 'en-US') else 'en-US')['messages']
                merged = dict(base)
                for key,value in pack['messages'].items():
                    if not isinstance(value, str): raise ValueError('Invalid text')
                    value.encode('utf-8')
                    if key not in base: continue
                    if text.parameters(value) != text.parameters(base[key]):
                        raise ValueError('Invalid placeholders')
                    merged[key] = value
                packs[locale] = dict(pack, messages=merged)
            except (OSError, ValueError, TypeError, KeyError):
                errors.append(path.name)
                # An invalid edit must not replace the last usable translation.
                if path.stem in self._packs: packs[path.stem] = self._packs[path.stem]
        self._packs = packs
        if errors: self._status(text.message('language.invalid', name=', '.join(errors)))
        self.languagesChanged.emit()
        return not errors

    def _activate(self, locale):
        self._locale = locale
        self.messages = dict(self._packs[locale]['messages'])
        self._translator.set_messages(self.messages)
        text._active = self
        self.changed.emit()
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QEvent
        app = QCoreApplication.instance()
        if isinstance(app, QApplication):
            widgets = app.allWidgets()
            for widget in widgets:
                QCoreApplication.sendEvent(widget, QEvent(QEvent.LanguageChange))
            # QDialogButtonBox also handles this event and can restore system
            # labels. Apply app-owned bindings after all child widgets update.
            from qt_dicom_viewer.i18n.widgets import TextBindings
            for widget in widgets:
                if isinstance(widget, TextBindings): widget.retranslate()
        refresh_properties()
        refresh_models()
        for engine in list(self._engines): engine.retranslate()
        self.messageChanged.emit()

    @Slot(str, result=bool)
    def selectLanguage(self, locale):
        if locale not in self._packs:
            self._status(text.message('language.missing', name=locale))
            return False
        return self.settings.setValue('appearance', 'language', locale)

    def _setting_changed(self, section):
        if section == 'appearance':
            locale = self.settings.section('appearance')['language']
            if locale in self._packs and locale != self._locale: self._activate(locale)

    @Slot(result=bool)
    def reload(self):
        valid = self._scan()
        locale = self._locale if self._locale in self._packs else 'zh-CN'
        self._activate(locale)
        if valid: self._status(text.message('language.reloaded'))
        return valid

    @Slot(result=bool)
    def openDirectory(self):
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            for locale in ('zh-CN', 'en-US'):
                path = self.root / (locale + '.json')
                if not path.exists():
                    # Exclusive creation never overwrites a user's edits.
                    with path.open('x', encoding='utf-8') as stream:
                        json.dump(text.builtin(locale), stream, ensure_ascii=False, indent=2)
            if not reveal_path(str(self.root)): raise OSError(str(self.root))
            return True
        except OSError as error:
            self._status(text.message('language.folderError', detail=error_message(error)))
            return False

    def snapshot(self): return dict(self.messages)

    def shutdown(self):
        app = QCoreApplication.instance()
        if app is not None: app.removeTranslator(self._translator)
        if text._active is self: text._active = None
