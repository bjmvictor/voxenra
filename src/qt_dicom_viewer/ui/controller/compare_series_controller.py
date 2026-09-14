"""Choose a second imported image stack without duplicating catalog state."""
from PySide6.QtCore import QObject, Property, Signal, Slot

from qt_dicom_viewer.core.compare import supports_compare
from qt_dicom_viewer.core.series_sidebar import series_sort_key


class CompareSeriesController(QObject):
    changed = Signal()
    openRequested = Signal(str, str)
    multiOpenRequested = Signal(object)

    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel
        self._anchor = self._partner = ""
        self._partners = []
        self._open = False
        panel.seriesItemsChanged.connect(self._catalog_changed)

    def _record(self, uid):
        return self.panel._scan_series_record.get(uid)

    def _item(self, record):
        return dict(seriesUid=record.series_instance_uid, patientName=record.patient_name,
                    patientId=record.patient_id, studyDate=record.study_date,
                    description=record.series_description or record.modality,
                    modality=record.modality, count=len(record.instances))

    @Property(bool, notify=changed)
    def dialogOpen(self):
        return self._open

    @Property('QVariantMap', notify=changed)
    def anchor(self):
        record = self._record(self._anchor)
        return self._item(record) if record else {}

    @Property('QVariantList', notify=changed)
    def candidates(self):
        anchor = self._record(self._anchor)
        records = [record for record in self.panel._scan_series_record.values()
                   if record.series_instance_uid != self._anchor and supports_compare(record)]
        records.sort(key=lambda record: (not (anchor and self.panel._same_patient(anchor, record)),
                                        record.patient_name, record.study_date, series_sort_key(record)))
        return [self._item(record) for record in records]

    @Property(str, notify=changed)
    def partnerUid(self):
        return self._partner

    @Property(bool, notify=changed)
    def canConfirm(self):
        return 1 <= len(self._partners) <= 3 and all(supports_compare(self._record(uid))
            for uid in (self._anchor, *self._partners))

    @Slot(str, result=bool)
    def supportsSeries(self, uid):
        return supports_compare(self._record(uid))

    @Slot(str)
    def request(self, context_uid):
        if not self.supportsSeries(context_uid):
            return
        selected = self.panel.selectedSeriesUids
        if 2 <= len(selected) <= 4 and context_uid in selected and all(self.supportsSeries(uid) for uid in selected):
            self.multiOpenRequested.emit(selected)
            return
        self._anchor, self._partner = context_uid, ""
        self._partners = []
        self._open = True
        self.changed.emit()

    @Slot(str)
    def selectPartner(self, uid):
        if uid != self._anchor and self.supportsSeries(uid):
            self._partner = uid
            self._partners = [uid]
            self.changed.emit()

    @Property('QVariantList', notify=changed)
    def partnerUids(self):
        return list(self._partners)

    @Slot(str)
    def togglePartner(self, uid):
        if uid == self._anchor or not self.supportsSeries(uid): return
        if uid in self._partners: self._partners.remove(uid)
        elif len(self._partners) < 3: self._partners.append(uid)
        self._partner = self._partners[0] if self._partners else ""
        self.changed.emit()

    @Slot()
    def confirm(self):
        if self.canConfirm:
            self._open = False
            self.multiOpenRequested.emit([self._anchor, *self._partners])
            self.changed.emit()

    @Slot()
    def cancel(self):
        if self._open:
            self._open = False
            self._partner = ""
            self.changed.emit()

    def _catalog_changed(self):
        self._partners = [uid for uid in self._partners if self.supportsSeries(uid)]
        if not self.supportsSeries(self._anchor):
            self._open = False
        if not self.supportsSeries(self._partner):
            self._partner = ""
        self.changed.emit()
