from custom_components.cesar_smart.data_extractors import (
    extract_balance_currency,
    extract_balance_updated_at,
    extract_balance_value,
)


def test_direct_balance_key():
    assert extract_balance_value({"balance": 123.45}) == 123.45


def test_nested_data_balance():
    assert extract_balance_value({"data": {"balance": 123.45}}) == 123.45


def test_nested_result():
    assert extract_balance_value({"result": {"accountBalance": "123.45"}}) == 123.45


def test_comma_string():
    assert extract_balance_value({"balance": "123,45"}) == 123.45


def test_rub_suffix():
    val = extract_balance_value({"balance": "123,45 \u20bd"})
    assert val == 123.45


def test_rub_string_currency():
    cur = extract_balance_currency({"balance": "123,45 \u20bd"})
    assert cur == "RUB"


def test_nested_payload_sim():
    data = {"payload": {"sim": {"currentBalance": "55 RUB"}}}
    assert extract_balance_value(data) == 55.0
    assert extract_balance_currency(data) == "RUB"


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
    assert (
        extract_balance_updated_at({"updatedAt": "2026-05-17T10:00:00Z"})
        == "2026-05-17T10:00:00Z"
    )


def test_none_input():
    assert extract_balance_value(None) is None
    assert extract_balance_currency(None) is None
    assert extract_balance_updated_at(None) is None


def test_empty_dict():
    assert extract_balance_value({}) is None
    assert extract_balance_currency({}) is None
    assert extract_balance_updated_at({}) is None


def test_sim_balance_key():
    assert extract_balance_value({"simBalance": 42.5}) == 42.5


def test_available_balance_key():
    assert extract_balance_value({"availableBalance": 200}) == 200.0


def test_balance_info_parent():
    data = {"balanceInfo": {"currentBalance": "500.00"}}
    assert extract_balance_value(data) == 500.0


def test_number_input():
    assert extract_balance_value(123.45) == 123.45
    assert extract_balance_value(100) == 100.0


def test_recursive_nested():
    data = {"securityObjectBalance": {"unitBalance": {"sim": {"rest": "99.99"}}}}
    assert extract_balance_value(data) == 99.99
