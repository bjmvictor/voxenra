"""Read Enhanced MR frames without changing their original DICOM identities.

Only standard functional groups are flattened; private nested copies must not
override authoritative geometry. Unknown non-spatial dimension indices remain
part of the grouping key, so they cannot silently become spatial slices.
"""
from copy import copy
from pydicom.dataset import Dataset

ENHANCED_MR_STORAGE = "1.2.840.10008.5.1.4.1.1.4.1"
LEGACY_ENHANCED_MR_STORAGE = "1.2.840.10008.5.1.4.1.1.4.4"
ENHANCED_MR_CLASSES = {ENHANCED_MR_STORAGE, LEGACY_ENHANCED_MR_STORAGE}
_GROUPS = (
    "PixelMeasuresSequence", "PlanePositionSequence", "PlaneOrientationSequence",
    "FrameContentSequence", "MRTimingAndRelatedParametersSequence",
    "MREchoSequence", "MRModifierSequence", "MRImageFrameTypeSequence",
    "PixelValueTransformationSequence", "FrameVOILUTSequence",
)
_SPATIAL_DIMENSIONS = {0x00209057, 0x00200032, 0x00201041}


def is_enhanced_mr(dataset):
    return str(getattr(dataset, "SOPClassUID", "")) in ENHANCED_MR_CLASSES


def enhanced_header_error(dataset):
    from qt_dicom_viewer.i18n import message
    try:
        count = int(dataset.NumberOfFrames)
        groups = dataset.PerFrameFunctionalGroupsSequence
        if count < 1 or len(groups) != count:
            raise ValueError()
        shared = getattr(dataset, "SharedFunctionalGroupsSequence", ())
        if len(shared) > 1:
            raise ValueError()
    except (AttributeError, TypeError, ValueError):
        return message("mr.invalidFrames")
    return ""


def frame_metadata(dataset, frame_index):
    """Detached metadata for one zero-based frame; no pixel/sequence copies."""
    if not is_enhanced_mr(dataset):
        if frame_index not in (None, 0):
            raise ValueError("Single-frame object has no requested frame")
        return dataset
    error = enhanced_header_error(dataset)
    if error:
        raise ValueError(error)
    if frame_index is None or not 0 <= frame_index < int(dataset.NumberOfFrames):
        raise ValueError("Enhanced MR requires an explicit valid frame index")
    result = Dataset()
    excluded = {0x52009229, 0x52009230, 0x7fe00010, 0x7fe00008, 0x7fe00009}
    for element in dataset:
        if element.tag not in excluded:
            result.add(copy(element))
    for group in (*getattr(dataset, "SharedFunctionalGroupsSequence", ()),
                  dataset.PerFrameFunctionalGroupsSequence[frame_index]):
        for keyword in _GROUPS:
            items = getattr(group, keyword, ())
            if len(items) > 1:
                raise ValueError("Invalid Enhanced MR functional group cardinality")
            if items:
                for element in items[0]:
                    result.add(copy(element))
        for keyword in ("MRDiffusionSequence", "RealWorldValueMappingSequence"):
            if keyword in group:
                result.add(copy(group.data_element(keyword)))
    # These Enhanced attributes replace their classic counterparts for display.
    for enhanced, classic in (("EffectiveEchoTime", "EchoTime"),
                              ("InversionTimes", "InversionTime"),
                              ("TemporalPositionIndex", "TemporalPositionIdentifier"),
                              ("FrameType", "ImageType")):
        if enhanced in result:
            value = getattr(result, enhanced)
            if enhanced == "InversionTimes" and hasattr(value, "__len__"):
                value = value[0] if len(value) else None
            if value is not None:
                setattr(result, classic, value)
    result._voxenra_frame_index = frame_index
    # A missing per-frame geometry is an error, never a fabricated 1mm grid.
    from math import isfinite
    for keyword, length in (("ImagePositionPatient", 3), ("ImageOrientationPatient", 6), ("PixelSpacing", 2)):
        values = getattr(result, keyword, ())
        if len(values) != length or not all(isfinite(float(v)) for v in values):
            raise ValueError("Enhanced MR frame is missing valid patient geometry")
    if any(float(v) <= 0 for v in result.PixelSpacing):
        raise ValueError("Enhanced MR frame has invalid pixel spacing")
    return result


def dimension_indices(dataset, metadata):
    indices = getattr(metadata, "DimensionIndexValues", ())
    if isinstance(indices, int):
        indices = (indices,)
    definitions = getattr(dataset, "DimensionIndexSequence", ())
    if definitions and len(indices) != len(definitions):
        raise ValueError("Enhanced MR dimension index count does not match its definitions")
    return tuple((str(item.DimensionIndexPointer), str(getattr(item, "FunctionalGroupPointer", "")),
                  str(getattr(item, "DimensionIndexPrivateCreator", "")), int(value))
                 for item, value in zip(definitions, indices)
                 if int(item.DimensionIndexPointer) not in _SPATIAL_DIMENSIONS)
