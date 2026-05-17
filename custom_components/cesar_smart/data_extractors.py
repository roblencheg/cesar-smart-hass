from __future__ import annotations

import logging
from typing import Any

from .const import (
    MERGE_MODE_FILL_MISSING_ONLY,
    MERGE_MODE_PREFER_FULL_INFO,
    MERGE_MODE_PREFER_STATUSES,
)

_LOGGER = logging.getLogger(__name__)

_MERGE_SUMMARY_KEYS = {
    "ENGINE_TEMP",
    "SALON_TEMP",
    "OUTDOOR_TEMP",
    "FUEL_VALUE",
    "MILEAGE_KM",
    "VEHICLE_CHARGE_VOLT",
}

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


_BALANCE_VALUE_KEYS = {
    "balance", "value", "amount", "sum", "money",
    "accountBalance", "simBalance", "rest",
    "currentBalance", "availableBalance", "balanceValue",
    "balanceAmount", "\u043e\u0441\u0442\u0430\u0442\u043e\u043a",
    "balans",
}
_BALANCE_CURRENCY_KEYS = {
    "currency", "currencyCode", "curr", "unit", "balanceCurrency",
}
_BALANCE_DATE_KEYS = {
    "updatedAt", "updateDate", "date", "timestamp",
    "actualDate", "lastUpdate", "lastUpdated",
}
_BALANCE_NESTED_PARENT_KEYS = {
    "data", "result", "payload", "balanceInfo",
    "account", "sim", "unitBalance", "securityObjectBalance",
}


def _recursive_find_key(
    data: Any, target_keys: set[str], depth: int, max_depth: int = 5,
) -> Any:
    if depth > max_depth:
        return None
    if isinstance(data, dict):
        for key, val in data.items():
            if key in target_keys and val is not None:
                return _to_number(val) if target_keys is _BALANCE_VALUE_KEYS else val
            result = _recursive_find_key(val, target_keys, depth + 1, max_depth)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _recursive_find_key(item, target_keys, depth + 1, max_depth)
            if result is not None:
                return result
    return None


def _normalize_number_string(s: str) -> float | str | None:
    if not s:
        return None
    s = s.strip()
    s = s.replace(",", ".")
    import re
    match = re.search(r"-?\d+(?:\.\d+)?", s)
    if match:
        try:
            return float(match.group())
        except (ValueError, TypeError):
            return s
    return s


def _to_number(val: Any) -> float | str | None:
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        return _normalize_number_string(val)
    return None


def _extract_currency_from_string(balance: Any) -> str | None:
    if balance is None:
        return None
    text = ""
    if isinstance(balance, dict):
        text = " ".join(
            str(v) for v in balance.values() if isinstance(v, (str, int, float))
        )
        for val in balance.values():
            if isinstance(val, dict):
                nested = _extract_currency_from_string(val)
                if nested:
                    text += " " + nested
    elif isinstance(balance, str):
        text = balance
    upper = text.upper()
    if "\u20bd" in text:
        return "RUB"
    if "RUB" in upper:
        return "RUB"
    return None


def extract_balance_value(balance: dict | None) -> float | str | None:
    if balance is None:
        return None
    if isinstance(balance, (int, float)):
        return float(balance)
    if isinstance(balance, str):
        return _normalize_number_string(balance)

    for parent_key in _BALANCE_NESTED_PARENT_KEYS:
        parent = balance.get(parent_key)
        if isinstance(parent, dict):
            for key in _BALANCE_VALUE_KEYS:
                val = parent.get(key)
                if val is not None:
                    return _to_number(val)

    for key in _BALANCE_VALUE_KEYS:
        val = balance.get(key)
        if val is not None:
            return _to_number(val)

    found = _recursive_find_key(balance, _BALANCE_VALUE_KEYS, 0)
    if found is not None:
        return found

    for val in balance.values():
        if isinstance(val, (int, float)):
            return float(val)
    return None


def extract_balance_currency(balance: dict | None) -> str | None:
    if not isinstance(balance, dict):
        return None
    for parent_key in _BALANCE_NESTED_PARENT_KEYS:
        parent = balance.get(parent_key)
        if isinstance(parent, dict):
            for key in _BALANCE_CURRENCY_KEYS:
                val = parent.get(key)
                if val is not None:
                    return str(val)
    for key in _BALANCE_CURRENCY_KEYS:
        val = balance.get(key)
        if val is not None:
            return str(val)
    found = _recursive_find_key(balance, _BALANCE_CURRENCY_KEYS, 0)
    if found is not None:
        return str(found)
    return _extract_currency_from_string(balance)


def extract_balance_updated_at(balance: dict | None) -> str | None:
    if not isinstance(balance, dict):
        return None
    for parent_key in _BALANCE_NESTED_PARENT_KEYS:
        parent = balance.get(parent_key)
        if isinstance(parent, dict):
            for key in _BALANCE_DATE_KEYS:
                val = parent.get(key)
                if val is not None:
                    return str(val)
    for key in _BALANCE_DATE_KEYS:
        val = balance.get(key)
        if val is not None:
            return str(val)
    found = _recursive_find_key(balance, _BALANCE_DATE_KEYS, 0)
    if found is not None:
        return str(found)
    return None


def merge_status_sources(
    statuses: dict,
    full_info: dict | None,
    mode: str = MERGE_MODE_PREFER_FULL_INFO,
) -> dict:
    merged = dict(statuses)
    if not full_info:
        return merged

    extracted = extract_statuses_from_full_info(full_info)

    for key, val in extracted.items():
        old = merged.get(key)

        if mode == MERGE_MODE_PREFER_FULL_INFO:
            if val is not None and val != "":
                merged[key] = val
        elif mode == MERGE_MODE_PREFER_STATUSES:
            if key not in merged:
                if val is not None and val != "":
                    merged[key] = val
        elif mode == MERGE_MODE_FILL_MISSING_ONLY:
            if old is None or old == "":
                if val is not None and val != "":
                    merged[key] = val

        new = merged.get(key)
        if key in _MERGE_SUMMARY_KEYS:
            _LOGGER.debug(
                "Status merge summary %s: raw=%s full_info=%s merged=%s mode=%s",
                key, old, val, new, mode,
            )

    return merged
