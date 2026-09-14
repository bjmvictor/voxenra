"""Eligibility and relative stack navigation for side-by-side comparison."""


SYNC_OPERATIONS = ("scroll", "window", "pan", "zoom", "rotate", "flip",
                   "pseudocolor", "invert", "viewport")


def supports_compare(series):
    """Use the same image stacks as 2D; exclude reports and unsupported PET."""
    return bool(series and series.instances and all(
        (item.rows or 0) > 0 and (item.columns or 0) > 0
        and (item.modality.upper() != "PT" or item.pet_2d_supported)
        for item in series.instances))


def relative_slice(index, source_count, target_count):
    if source_count <= 1 or target_count <= 1:
        return 0
    fraction = max(0, min(index, source_count - 1)) / (source_count - 1)
    return int(fraction * (target_count - 1) + 0.5)


def supports_mpr_compare(series):
    """Offer reconstructable scalar stacks; the volume loader validates geometry."""
    if not supports_compare(series):
        return False
    instances = series.instances
    return bool(len(instances) >= 2 and all(
        i.photometric_interpretation.upper() in ("", "MONOCHROME1", "MONOCHROME2")
        and i.image_position_patient is not None
        and i.image_orientation_patient is not None
        and i.pixel_spacing is not None
        for i in instances))
