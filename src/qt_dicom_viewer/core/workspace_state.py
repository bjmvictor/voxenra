"""Versioned data-only snapshots for workspace files and edit history.

Only explicitly registered value types can be restored. Images, QObjects and
render jobs never enter a document. NumPy support is limited to small numeric
transforms and packed boolean editing masks.
"""
from __future__ import annotations

import base64
from dataclasses import fields, is_dataclass
from enum import Enum
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import tempfile
import zlib
import types
from typing import Any, Union, get_args, get_origin, get_type_hints

import numpy as np

MAX_DOCUMENT_BYTES = 64 * 1024**2
MAX_MASK_VOXELS = 512 * 1024**2


@lru_cache(maxsize=1)
def _types():
    from qt_dicom_viewer.model import dicom_core, dicom_types, image_geometry, measure, ui_models, volume_models, interaction, dicom_models
    from qt_dicom_viewer.core import volume_view, mpr_voi
    from qt_dicom_viewer.ui.controller.viewport.controller import text_annotation_controller, pet_display_controller
    names = {
        "WindowLevel", "PixelUnitOption", "PixelValueMeta", "PixelSpacing",
        "ImagePoint", "Point", "Offset", "ViewportState", "DisplayStyle",
        "ViewportDisplaySettings", "MprProjectionSettings", "MprProjectionMode",
        "MprFrame", "MprViewRolls", "MprGridSpec", "MprViewGrids",
        "MprGridAnchor", "MprViewAnchors", "MprState", "WindowLevelChange",
        "LengthMeasurement", "AngleMeasurement", "RoiMeasurement", "RoiMetrics",
        "MeasurementKind", "TextAnnotation", "VoiRegion", "VolumeViewState",
        "VolumeDisplayState", "VolumeBlendMode", "PetDisplayState", "MprPlane",
    }
    modules = (dicom_core, dicom_types, image_geometry, measure, ui_models,
               volume_models, interaction, dicom_models, volume_view, mpr_voi,
               text_annotation_controller, pet_display_controller)
    return {name: getattr(module, name) for module in modules for name in names
            if hasattr(module, name)}


def encode(value):
    if isinstance(value, Enum):
        if type(value).__name__ not in _types():
            raise ValueError(f"不支持保存的状态：{type(value).__name__}")
        return {"$enum": type(value).__name__, "value": value.value}
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    if is_dataclass(value):
        if type(value).__name__ not in _types():
            raise ValueError(f"不支持保存的状态：{type(value).__name__}")
        return {"$type": type(value).__name__, "fields": {
            f.name: encode(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, tuple):
        return {"$tuple": [encode(v) for v in value]}
    if isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, dict):
        if any(not isinstance(k, str) or k.startswith("$") for k in value):
            raise ValueError("工作区状态包含无效字段。")
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, np.ndarray):
        if value.dtype == np.bool_ and value.size <= MAX_MASK_VOXELS:
            packed = np.packbits(value.reshape(-1)).tobytes()
            return {"$mask": base64.b64encode(zlib.compress(packed)).decode("ascii"),
                    "shape": list(value.shape)}
        if value.size <= 32 and np.issubdtype(value.dtype, np.number) and np.isfinite(value).all():
            return {"$array": value.tolist()}
    raise ValueError(f"不支持保存的状态：{type(value).__name__}")


def decode(value, depth=0, *, budget=None):
    if budget is None:
        budget = [MAX_MASK_VOXELS]
    if depth > 40:
        raise ValueError("工作区嵌套层数过多。")
    descend = lambda v: decode(v, depth + 1, budget=budget)
    if isinstance(value, list):
        return [descend(v) for v in value]
    if not isinstance(value, dict):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("工作区包含无效数值。")
        return value
    if "$type" in value:
        cls = _types().get(value["$type"])
        if cls is None or not is_dataclass(cls) or set(value) != {"$type", "fields"}:
            raise ValueError("工作区状态类型不受支持。")
        payload = value["fields"]
        if not isinstance(payload, dict) or set(payload) != {f.name for f in fields(cls)}:
            raise ValueError("工作区状态字段不完整。")
        decoded = {k: descend(v) for k, v in payload.items()}
        hints = _hints(cls)
        if any(not _matches(v, hints[k]) for k, v in decoded.items()):
            raise ValueError("工作区状态字段类型无效。")
        return cls(**decoded)
    if "$enum" in value:
        cls = _types().get(value["$enum"])
        if cls is None or not issubclass(cls, Enum) or set(value) != {"$enum", "value"}:
            raise ValueError("工作区枚举类型不受支持。")
        return cls(value["value"])
    if "$tuple" in value and set(value) == {"$tuple"}:
        return tuple(descend(v) for v in value["$tuple"])
    if "$array" in value and set(value) == {"$array"}:
        array = np.asarray(value["$array"], dtype=float)
        if array.size > 32 or not np.isfinite(array).all():
            raise ValueError("工作区变换矩阵无效。")
        return array
    if "$mask" in value and set(value) == {"$mask", "shape"}:
        shape = value["shape"]
        if (not isinstance(shape, list) or len(shape) != 3
                or any(type(n) is not int or n <= 0 for n in shape)):
            raise ValueError("裁剪掩膜尺寸无效。")
        count = math.prod(shape)
        if count > MAX_MASK_VOXELS:
            raise ValueError("裁剪掩膜过大。")
        budget[0] -= count
        if budget[0] < 0:
            raise ValueError("工作区裁剪掩膜总量过大。")
        length = (count + 7) // 8
        decompressor = zlib.decompressobj()
        data = decompressor.decompress(base64.b64decode(value["$mask"], validate=True), length + 1)
        if len(data) != length or not decompressor.eof or decompressor.unused_data:
            raise ValueError("裁剪掩膜数据不完整。")
        return np.unpackbits(np.frombuffer(data, dtype=np.uint8), count=count).reshape(shape).astype(bool)
    if any(k.startswith("$") for k in value):
        raise ValueError("工作区包含未知状态标记。")
    return {k: descend(v) for k, v in value.items()}


@lru_cache(maxsize=64)
def _hints(cls):
    return get_type_hints(cls)


def _matches(value, hint):
    if hint is Any:
        return True
    origin, args = get_origin(hint), get_args(hint)
    if origin in (Union, types.UnionType):
        return any(_matches(value, part) for part in args)
    if origin is tuple:
        return isinstance(value, tuple) and (
            all(_matches(v, args[0]) for v in value) if len(args) == 2 and args[1] is Ellipsis
            else len(value) == len(args) and all(_matches(v, t) for v, t in zip(value, args)))
    if hint is float:
        return type(value) in (float, int) and math.isfinite(value)
    if hint in (int, bool, str, type(None)):
        return type(value) is hint
    return isinstance(value, hint)


def dumps(value):
    data = json.dumps(encode(value), ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("工作区文件过大，请减少保存的页签或编辑对象。")
    return data


def loads(data):
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("工作区文件超过大小限制。")
    try:
        return decode(json.loads(data))
    except (TypeError, KeyError, OverflowError, RecursionError, zlib.error) as exc:
        raise ValueError("工作区文件损坏或格式不受支持。") from exc


def atomic_write(path, data):
    """Keep the previous document intact if serialization or writing fails."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".voxenra-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
