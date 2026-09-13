"""Offline operation manual and reading state owned by its workspace tab."""
from qt_dicom_viewer.i18n import message as _msg
from qt_dicom_viewer.i18n.messages import localize
from qt_dicom_viewer.i18n.qt import translated_property as _TextProperty
import json
import math
import re
from html import escape
from functools import lru_cache
from importlib.resources import files

from PySide6.QtCore import Property, Signal, Slot

from qt_dicom_viewer.model import TabType
from qt_dicom_viewer.ui.controller.utility_tab_controller import UtilityTabController


@lru_cache(maxsize=1)
def manual_content():
    content = json.loads(files("qt_dicom_viewer").joinpath("qml/assets/help/manual.json").read_text(encoding="utf-8"))
    for category in content['categories']:
        category['title'] = _msg('manual.category.' + category['id'])
    for chapter in content['chapters']:
        prefix = 'manual.' + chapter['id'] + '.'
        for field in ('title', 'summary', 'caption'):
            if field in chapter: chapter[field] = _msg(prefix + field)
        for index, section in enumerate(chapter['sections']):
            for field in ('title', 'body'):
                section[field] = _msg(prefix + f'section{index}.' + field)
        for index, shortcut in enumerate(chapter.get('shortcuts', [])):
            shortcut['label'] = _msg(prefix + f'shortcut{index}')
    return content


def manual_rich_text(text):
    """Only emphasis and inline keys are markup; never interpret embedded HTML."""
    parts = re.split(r"(\*\*[^\n*]+\*\*|`[^\n`]+`)", localize(text))
    return "".join(
        "<b>" + escape(part[2:-2]) + "</b>" if re.fullmatch(r"\*\*[^\n*]+\*\*", part)
        else "<b>" + escape(part[1:-1]) + "</b>" if re.fullmatch(r"`[^\n`]+`", part)
        else escape(part).replace("\n", "<br>")
        for part in parts
    )


class ManualTabController(UtilityTabController):
    _i18n_currentChapter = Signal()
    _i18n_navigation = Signal()

    chapterChanged = Signal()
    navigationChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(TabType.MANUAL, _msg('text.0495'), parent)
        self._content = manual_content()
        self._chapters = {c["id"]: c for c in self._content["chapters"]}
        self._chapter = "quick-start"
        self._search = ""
        self._positions = {}

    @Property(str, notify=chapterChanged)
    def chapterId(self):
        return self._chapter

    @_TextProperty('QVariantMap', notify=_i18n_currentChapter, notify_name='_i18n_currentChapter', source_notify='chapterChanged')
    def currentChapter(self):
        chapter = dict(self._chapters[self._chapter])
        from qt_dicom_viewer.i18n import messages
        if messages._active is not None and messages._active.locale != 'zh-CN':
            if chapter.get('example'): chapter['example'] = 'en/' + chapter['example']
            if chapter.get('examples'): chapter['examples'] = ['en/' + name for name in chapter['examples']]
        category = next(c for c in self._content["categories"] if c["id"] == chapter["category"])
        return dict(chapter, categoryTitle=category["title"],
                    sections=[dict(section, bodyHtml=manual_rich_text(section["body"]))
                              for section in chapter["sections"]],
                    relatedChapters=[dict(id=key, title=self._chapters[key]["title"])
                                     for key in chapter.get("related", []) if key in self._chapters])

    @Property(str, notify=navigationChanged)
    def search(self):
        return self._search

    @Slot(str)
    def setSearch(self, value):
        if self._search != value:
            self._search = value
            self.navigationChanged.emit()

    @_TextProperty('QVariantList', notify=_i18n_navigation, notify_name='_i18n_navigation', source_notify='navigationChanged')
    def navigation(self):
        query = self._search.strip().casefold()
        rows = []
        for category in self._content["categories"]:
            chapters = [c for c in self._content["chapters"] if c["category"] == category["id"]
                        and (not query or query in json.dumps(localize(c), ensure_ascii=False).casefold()
                             or query in localize(category["title"]).casefold())]
            if chapters:
                rows.append(dict(category, chapters=[dict(id=c["id"], title=c["title"]) for c in chapters]))
        return rows

    @Slot(str)
    def selectChapter(self, chapter_id):
        if chapter_id not in self._chapters:
            chapter_id = "quick-start"
        self._chapter = chapter_id
        self._positions[chapter_id] = 0.0
        self.chapterChanged.emit()

    @Property(float, notify=chapterChanged)
    def scrollPosition(self):
        return self._positions.get(self._chapter, 0.0)

    @Slot(float)
    def setScrollPosition(self, value):
        if math.isfinite(value):
            self._positions[self._chapter] = max(0.0, value)
