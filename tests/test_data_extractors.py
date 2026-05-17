from __future__ import annotations

from custom_components.cesar_smart.data_extractors import (
    extract_statuses_from_full_info,
    merge_status_sources,
)


def test_extract_statuses_direct():
    fi = {"statuses": {"ENGINE_TEMP": 90, "SALON_TEMP": 25}}
    result = extract_statuses_from_full_info(fi)
    assert result.get("ENGINE_TEMP") == 90
    assert result.get("SALON_TEMP") == 25


def test_extract_statuses_via_data():
    fi = {"data": {"statuses": {"ENGINE_TEMP": 91}}}
    result = extract_statuses_from_full_info(fi)
    assert result.get("ENGINE_TEMP") == 91


def test_extract_statuses_via_units():
    fi = {"units": [{"statuses": {"ENGINE_TEMP": 92}}]}
    result = extract_statuses_from_full_info(fi)
    assert result.get("ENGINE_TEMP") == 92


def test_extract_statuses_recursive():
    fi = {"vehicle": {"telemetry": {"ENGINE_TEMP": 93}}}
    result = extract_statuses_from_full_info(fi)
    assert result.get("ENGINE_TEMP") == 93


def test_extract_statuses_empty():
    assert extract_statuses_from_full_info({}) == {}
    assert extract_statuses_from_full_info({"data": {}}) == {}


def test_merge_full_info_wins():
    statuses = {"ENGINE_TEMP": 70, "FUEL_VALUE": 50}
    fi = {"statuses": {"ENGINE_TEMP": 90}}
    merged = merge_status_sources(statuses, fi)
    assert merged["ENGINE_TEMP"] == 90
    assert merged["FUEL_VALUE"] == 50


def test_merge_full_info_none_keeps_statuses():
    statuses = {"ENGINE_TEMP": 70}
    fi = {"statuses": {"ENGINE_TEMP": None}}
    merged = merge_status_sources(statuses, fi)
    assert merged["ENGINE_TEMP"] == 70


def test_merge_full_info_empty_string_keeps_statuses():
    statuses = {"ENGINE_TEMP": 70}
    fi = {"statuses": {"ENGINE_TEMP": ""}}
    merged = merge_status_sources(statuses, fi)
    assert merged["ENGINE_TEMP"] == 70


def test_merge_no_full_info():
    statuses = {"ENGINE_TEMP": 70}
    merged = merge_status_sources(statuses, None)
    assert merged["ENGINE_TEMP"] == 70


def test_merge_full_info_new_keys():
    statuses = {"ENGINE_TEMP": 70}
    fi = {"statuses": {"SALON_TEMP": 25}}
    merged = merge_status_sources(statuses, fi)
    assert merged["ENGINE_TEMP"] == 70
    assert merged["SALON_TEMP"] == 25
