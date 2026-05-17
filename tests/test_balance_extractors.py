import json

from custom_components.cesar_smart.data_extractors import (
    extract_balance_communication_service,
    extract_balance_currency,
    extract_balance_phone,
    extract_balance_unit_class,
    extract_balance_unit_id,
    extract_balance_updated_at,
    extract_balance_value,
    redact_phone,
    redact_sensitive_balance,
    redact_unit_id,
)

BALANCE_LIST_RESPONSE = [
    {
        "unitId": "<REDACTED_UNIT_ID>",
        "unitClass": "GUARD",
        "balance1": {
            "phone": "<REDACTED_PHONE>",
            "client": False,
            "communicationService": True,
            "balance": "18",
            "message": None,
            "lastUpdated": "2026-01-01T00:00:00.000",
        },
        "balance2": None,
    }
]


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


def test_extract_balance_value_from_cesar_list():
    assert extract_balance_value(BALANCE_LIST_RESPONSE) == 18.0


def test_extract_balance_updated_from_cesar_list():
    assert extract_balance_updated_at(BALANCE_LIST_RESPONSE) == "2026-01-01T00:00:00.000"


def test_extract_balance_currency_defaults_to_rub_for_cesar_list():
    assert extract_balance_currency(BALANCE_LIST_RESPONSE) == "RUB"


def test_extract_balance_phone_redacted():
    assert redact_phone(extract_balance_phone(BALANCE_LIST_RESPONSE)) == "<REDACTED_PHONE>"


def test_extract_balance_unit_id_redacted():
    assert redact_unit_id(extract_balance_unit_id(BALANCE_LIST_RESPONSE)) == "<REDACTED_UNIT_ID>"


def test_extract_balance_unit_class():
    assert extract_balance_unit_class(BALANCE_LIST_RESPONSE) == "GUARD"


def test_extract_balance_communication_service():
    assert extract_balance_communication_service(BALANCE_LIST_RESPONSE) is True


def test_empty_balance_list():
    assert extract_balance_value([]) is None


def test_balance2_used_when_balance1_empty():
    response = [
        {
            "unitId": "<REDACTED_UNIT_ID>",
            "unitClass": "GUARD",
            "balance1": None,
            "balance2": {
                "phone": "<REDACTED_PHONE>",
                "balance": "25",
                "lastUpdated": "2026-01-01T01:00:00.000",
            },
        }
    ]
    assert extract_balance_value(response) == 25.0


def test_redact_sensitive_balance_removes_phone_and_unit_id():
    redacted = redact_sensitive_balance(BALANCE_LIST_RESPONSE)
    text = json.dumps(redacted, ensure_ascii=False)
    assert "<REDACTED_PHONE>" in text
    assert "<REDACTED_UNIT_ID>" in text
    assert "+7" not in text
    assert "869" not in text


def test_extractors_return_none_for_empty_dict():
    assert extract_balance_phone({}) is None
    assert extract_balance_unit_id({}) is None
    assert extract_balance_unit_class({}) is None
    assert extract_balance_communication_service({}) is None


def test_redact_none():
    assert redact_phone(None) is None
    assert redact_unit_id(None) is None


def test_redact_sensitive_balance_list():
    data = [{"phone": "123", "unitId": "abc"}, {"vin": "xyz"}]
    redacted = redact_sensitive_balance(data)
    assert redacted == [
        {"phone": "<REDACTED_PHONE>", "unitId": "<REDACTED_UNIT_ID>"},
        {"vin": "<REDACTED_VIN>"},
    ]


def test_redact_sensitive_balance_secrets():
    data = {"access_token": "secret123", "refresh_token": "secret456", "normal": "keep"}
    redacted = redact_sensitive_balance(data)
    assert redacted == {"access_token": "<REDACTED>", "refresh_token": "<REDACTED>", "normal": "keep"}
