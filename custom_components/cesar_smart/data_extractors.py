from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

_DIFF_KEYS = (
    "ENGINE_TEMP",
    "SALON_TEMP",
    "OUTDOOR_TEMP",
    "FUEL_VALUE",
    "MILEAGE_KM",
    "VEHICLE_CHARGE_VOLT",
)

_STATUS_KEYS = {
    "ENGINE_TEMP",
    "SALON_TEMP",
    "OUTDOOR_TEMP",
    "FUEL_VALUE",
    "MILEAGE_KM",
    "VEHICLE_CHARGE_VOLT",
    "ENGINE_STATE",
    "MODE",
    "L_SIDE_TEMP",
    "R_SIDE_TEMP",
    "IGNITION",
    "HOOD",
    "DOOR_FRONT_LEFT",
    "DOOR_FRONT_RIGHT",
    "DOOR_BACK_LEFT",
    "DOOR_BACK_RIGHT",
    "DOOR_BOOT",
    "LABEL",
    "FUEL_TYPE",
}


def extract_statuses_from_full_info(full_info: dict) -> dict:
    candidates = {}

    for key in ("statuses", "status"):
        val = full_info.get(key)
        if isinstance(val, dict):
            candidates.update(val)

    data = full_info.get("data")
    if isinstance(data, dict):
        for key in ("statuses", "status"):
            val = data.get(key)
            if isinstance(val, dict):
                candidates.update(val)

    unit = full_info.get("unit")
    if isinstance(unit, dict):
        for key in ("statuses", "status"):
            val = unit.get(key)
            if isinstance(val, dict):
                candidates.update(val)

    units = full_info.get("units")
    if isinstance(units, list) and units:
        for u in units:
            if isinstance(u, dict):
                for key in ("statuses", "status"):
                    val = u.get(key)
                    if isinstance(val, dict):
                        candidates.update(val)

    _recursive_find_statuses(full_info, candidates, depth=0)

    return candidates


def _recursive_find_statuses(
    data: Any, result: dict, depth: int, max_depth: int = 5
) -> None:
    if depth > max_depth:
        return
    if isinstance(data, dict):
        for key, val in data.items():
            if key in _STATUS_KEYS and val is not None:
                result.setdefault(key, val)
            _recursive_find_statuses(val, result, depth + 1, max_depth)
    elif isinstance(data, list):
        for item in data:
            _recursive_find_statuses(item, result, depth + 1, max_depth)


def merge_status_sources(statuses: dict, full_info: dict | None) -> dict:
    merged = dict(statuses)
    if not full_info:
        return merged

    extracted = extract_statuses_from_full_info(full_info)
    for key, val in extracted.items():
        if val is not None and val != "":
            old = merged.get(key)
            if old != val:
                if key in _DIFF_KEYS:
                    _LOGGER.debug(
                        "Status merge %s: statuses=%s full_info=%s merged=%s",
                        key, old, val, val,
                    )
            merged[key] = val

    return merged
