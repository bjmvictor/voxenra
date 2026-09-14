"""Choose a second imported image stack without duplicating catalog state."""
from PySide6.QtCore import QObject, Property, Signal, Slot

from qt_dicom_viewer.core.compare import supports_compare, supports_mpr_compare


class CompareSeriesController(QObject):
    changed = Signal()
    openRequested = Signal(str, str)
    mprOpenRequested = Signal(str, str)

    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel
        self._anchor = self._partner = ""
        self._open = False
        self._mode = "2d"
        panel.seriesItemsChanged.connect(self._catalog_changed)

    def _record(self, uid):
        return self.panel._scan_series_record.get(uid)

    def _item(self, record):
        return dict(seriesUid=record.series_instance_uid, patientName=record.patient_name,
                    patientId=record.patient_id, studyDate=record.study_date,
                    description=record.series_description or record.modality,
                    modality=record.modality, count=sum(max(1, i.number_of_frames) for i in record.instances))

    @Property(str, notify=changed)
    def mode(self):
        return self._mode

    def _supports(self, record):
        return (supports_mpr_compare if self._mode == "mpr" else supports_compare)(record)

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
                   if record.series_instance_uid != self._anchor and self._supports(record)]
        records.sort(key=lambda record: (not (anchor and self.panel._same_patient(anchor, record)),
                                        record.patient_name, record.study_date, record.series_number or 0))
        return [self._item(record) for record in records]

    @Property(str, notify=changed)
    def partnerUid(self):
        return self._partner

    @Property(bool, notify=changed)
    def canConfirm(self):
        return self._anchor != self._partner and all(self._supports(self._record(uid))
            for uid in (self._anchor, self._partner))

    @Slot(str, result=bool)
    def supportsSeries(self, uid):
        return supports_compare(self._record(uid))

    @Slot(str, result=bool)
    def supportsMprSeries(self, uid):
        return supports_mpr_compare(self._record(uid))

    @Slot(QObject)
    def requestFromViewport(self, viewport):
        selected = [uid for uid in self.panel.selectedSeriesUids if self.supportsSeries(uid)]
        config = getattr(viewport, "viewport_config", None)
        context_uid = (self.panel.activeSeriesUid if self.panel.activeSeriesUid in selected else selected[0]) if selected else (
            config.series_uid if config is not None else self.panel.activeSeriesUid)
        self.request(context_uid)

    @Slot(str)
    def request(self, context_uid):
        self._request(context_uid, "2d")

    @Slot(str)
    def requestMpr(self, context_uid):
        self._request(context_uid, "mpr")

    def _open_pair(self, first, second):
        (self.mprOpenRequested if self._mode == "mpr" else self.openRequested).emit(first, second)

    def _request(self, context_uid, mode):
        self._mode = mode
        if not self._supports(self._record(context_uid)):
            return
        selected = self.panel.selectedSeriesUids
        if len(selected) == 2 and context_uid in selected and all(self._supports(self._record(uid)) for uid in selected):
            self._open_pair(*selected)
            return
        self._anchor, self._partner = context_uid, ""
        self._open = True
        self.changed.emit()

    @Slot(str)
    def selectPartner(self, uid):
        if uid != self._anchor and self._supports(self._record(uid)):
            self._partner = uid
            self.changed.emit()

    @Slot()
    def confirm(self):
        if self.canConfirm:
            self._open = False
            self._open_pair(self._anchor, self._partner)
            self.changed.emit()

    @Slot()
    def cancel(self):
        if self._open:
            self._open = False
            self._partner = ""
            self.changed.emit()

    def _catalog_changed(self):
        if not self._supports(self._record(self._anchor)):
            self._open = False
        if not self._supports(self._record(self._partner)):
            self._partner = ""
        self.changed.emit()
