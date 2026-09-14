"""Data-only measurement export; formatted values never replace source statistics."""
import csv
from datetime import datetime
import io
import math

COLUMNS = (
    ("patient", "患者"), ("patient_id", "患者 ID"), ("series", "序列"),
    ("modality", "模态"), ("view", "视图"), ("slice", "切片（从 1 开始）"),
    ("phase", "时相（从 1 开始）"), ("id", "编号"), ("kind", "类型"),
    ("length_mm", "长度 mm"), ("angle_deg", "角度 °"),
    ("width_mm", "宽度 mm"), ("height_mm", "高度 mm"), ("area_mm2", "面积 mm²"),
    ("volume_cm3", "体积 cm³"), ("pixel_count", "像素／体素数"),
    ("mean", "均值"), ("std", "SD"), ("minimum", "最小值"), ("maximum", "最大值"),
    ("unit", "强度单位"), ("threshold", "有效阈值"),
    ("origin", "平面原点 LPS mm"), ("orientation", "平面方向"), ("text", "标注文字"),
)


def cell(value):
    if value is None or isinstance(value, float) and not math.isfinite(value):
        return ""
    if isinstance(value, float):
        return format(value, ".10g")
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def csv_bytes(rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([label for _, label in COLUMNS])
    for row in rows:
        writer.writerow([cell(row.get(key)) for key, _ in COLUMNS])
    return output.getvalue().encode("utf-8-sig")


def pdf_bytes(rows, *, anonymous=True, images=(), created=None):
    """Use the Qt runtime already shipped with Voxenra; no extra packaging cost."""
    from PySide6.QtCore import QBuffer, QIODevice, QRectF, Qt, QMarginsF
    from PySide6.QtGui import QPdfWriter, QPageSize, QPageLayout, QPainter, QFont, QColor, QFontMetricsF
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    writer = QPdfWriter(buffer)
    writer.setResolution(144)
    writer.setPageSize(QPageSize(QPageSize.A4))
    writer.setPageMargins(QMarginsF(16, 16, 16, 16), QPageLayout.Millimeter)
    writer.setTitle("Voxenra 测量结果")
    writer.setCreator("Voxenra")
    painter = QPainter(writer)
    if not painter.isActive():
        raise OSError("无法创建 PDF 文件。")
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    width, height = writer.width(), writer.height()
    page, y = 0, 0
    stamp = created or datetime.now().strftime("%Y-%m-%d %H:%M")

    def text(value, x, yy, w, h, size=10, bold=False, color="#213443", single=False):
        font = QFont()
        font.setPointSizeF(size)
        font.setBold(bold)
        painter.setFont(font)
        painter.setPen(QColor(color))
        value = QFontMetricsF(font, writer).elidedText(str(value), Qt.ElideRight, w) if single else str(value)
        painter.drawText(QRectF(x, yy, w, h), Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, value)

    def new_page():
        nonlocal page, y
        if page:
            writer.newPage()
        page += 1
        text("Voxenra  /  测量结果", 0, 0, width, 46, 17, True)
        text(f"{stamp}    ·    {'匿名' if anonymous else '包含身份信息'}    ·    {len(rows)} 项结果",
             0, 50, width, 35, 9, color="#596f7e")
        painter.setPen(QColor("#c8d4db"))
        painter.drawLine(0, 96, width, 96)
        text(f"Voxenra  ·  {page}", 0, height - 28, width, 28, 9, color="#596f7e")
        y = 116

    try:
        new_page()
        for row in rows:
            metrics = [(label, cell(row.get(key))) for key, label in COLUMNS[9:22]
                       if row.get(key) is not None and row.get(key) != ""]
            lines = ["  ·  ".join(f"{label}: {value}" for label, value in metrics[i:i+2])
                     for i in range(0, len(metrics), 2)]
            if row.get("text"):
                lines.append("标注: " + row["text"][:180])
            block = 96 + len(lines) * 34
            if y + block > height - 55:
                new_page()
            painter.fillRect(QRectF(0, y, width, 40), QColor("#edf3f6"))
            text(f"{row['id']}  {row['kind']}  ·  {row['patient']} / {row['series']}",
                 12, y, width-24, 40, 10, True, single=True)
            location = f"{row['modality']} · {row['view']}"
            if row.get("slice"): location += f" · 切片 {row['slice']}"
            if row.get("phase"): location += f" · 时相 {row['phase']}"
            text(location, 12, y + 44, width - 24, 34, 9, color="#596f7e")
            for i, line in enumerate(lines):
                text(line, 12, y + 78 + i * 34, width - 24, 34, 10, single=True)
            y += block + 14
        if not rows:
            text("没有已完成的测量。", 0, y, width, 40)
        for caption, image in images:
            new_page()
            text(caption, 0, y, width, 64, 11, True, single=True)
            y += 80
            target = image.size().scaled(int(width), int(height-y-70), Qt.KeepAspectRatio)
            painter.drawImage(QRectF((width-target.width())/2, y, target.width(), target.height()), image)
            text("当前切片参考图；统计数值来自影像像素，显示窗值不改变统计结果。", 0, height-64, width, 30, 9)
    finally:
        painter.end()
    result = bytes(buffer.data())
    buffer.close()
    return result
