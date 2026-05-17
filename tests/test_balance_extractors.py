from custom_components.cesar_smart.data_extractors import (
    extract_balance_currency,
    extract_balance_updated_at,
    extract_balance_value,
)


def test_direct_balance_key():
    assert extract_balance_value({"balance": 123.45}) == 123.45


def test_nested_data_balance():
    assert extract_balance_value({"data": {"balance": 123.45}}) == 123.45


def test_alternative_key():
    assert extract_balance_value({"accountBalance": 55}) == 55.0


def test_string_value():
    result = extract_balance_value({"balance": "123.45"})
    assert result == 123.45


def test_currency_key():
    assert extract_balance_currency({"currency": "RUB"}) == "RUB"


def test_currency_nested_data():
    assert extract_balance_currency({"data": {"currency": "RUB"}}) == "RUB"


def test_updated_at():
    assert extract_balance_updated_at({"updatedAt": "2026-05-17T10:00:00Z"}) == "2026-05-17T10:00:00Z"


def test_none_input():
    assert extract_balance_value(None) is None
    assert extract_balance_currency(None) is None
    assert extract_balance_updated_at(None) is None


def test_sim_balance_key():
    assert extract_balance_value({"simBalance": 42.5}) == 42.5
