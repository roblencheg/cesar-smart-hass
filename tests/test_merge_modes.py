from custom_components.cesar_smart.data_extractors import merge_status_sources


def test_prefer_full_info_overwrites():
    statuses = {"ENGINE_TEMP": 50, "FUEL_VALUE": 30}
    full_info = {"statuses": {"ENGINE_TEMP": 88, "SALON_TEMP": 22}}
    merged = merge_status_sources(statuses, full_info, mode="prefer_full_info")
    assert merged["ENGINE_TEMP"] == 88
    assert merged["FUEL_VALUE"] == 30
    assert merged["SALON_TEMP"] == 22


def test_prefer_full_info_skips_empty_value():
    statuses = {"ENGINE_TEMP": 50}
    full_info = {"statuses": {"ENGINE_TEMP": ""}}
    merged = merge_status_sources(statuses, full_info, mode="prefer_full_info")
    assert merged["ENGINE_TEMP"] == 50


def test_prefer_statuses_keeps_original():
    statuses = {"ENGINE_TEMP": 50, "FUEL_VALUE": 30}
    full_info = {"statuses": {"ENGINE_TEMP": 88, "SALON_TEMP": 22}}
    merged = merge_status_sources(statuses, full_info, mode="prefer_statuses")
    assert merged["ENGINE_TEMP"] == 50
    assert merged["FUEL_VALUE"] == 30
    assert merged["SALON_TEMP"] == 22


def test_prefer_statuses_adds_missing():
    statuses = {"ENGINE_TEMP": 50}
    full_info = {"statuses": {"SALON_TEMP": 22}}
    merged = merge_status_sources(statuses, full_info, mode="prefer_statuses")
    assert merged["ENGINE_TEMP"] == 50
    assert merged["SALON_TEMP"] == 22


def test_fill_missing_only_fills_none():
    statuses = {"ENGINE_TEMP": None}
    full_info = {"statuses": {"ENGINE_TEMP": 88}}
    merged = merge_status_sources(statuses, full_info, mode="fill_missing_only")
    assert merged["ENGINE_TEMP"] == 88


def test_fill_missing_only_fills_empty_string():
    statuses = {"ENGINE_TEMP": ""}
    full_info = {"statuses": {"ENGINE_TEMP": 88}}
    merged = merge_status_sources(statuses, full_info, mode="fill_missing_only")
    assert merged["ENGINE_TEMP"] == 88


def test_fill_missing_only_does_not_overwrite():
    statuses = {"ENGINE_TEMP": 50, "FUEL_VALUE": 30}
    full_info = {"statuses": {"ENGINE_TEMP": 88}}
    merged = merge_status_sources(statuses, full_info, mode="fill_missing_only")
    assert merged["ENGINE_TEMP"] == 50
    assert merged["FUEL_VALUE"] == 30


def test_no_full_info_returns_statuses():
    statuses = {"ENGINE_TEMP": 50}
    merged = merge_status_sources(statuses, None, mode="prefer_full_info")
    assert merged == statuses


def test_empty_full_info_returns_statuses():
    statuses = {"ENGINE_TEMP": 50}
    merged = merge_status_sources(statuses, {}, mode="prefer_full_info")
    assert merged == statuses
