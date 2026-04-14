import builtins
from io import StringIO

import pytest
from utils.validation import (
    validate_email,
    validate_password,
    validate_profile_data,
    normalize_profile_data,
    validate_favorite_stops,
)


@pytest.mark.parametrize(
    "email, expected",
    [
        ("test@example.com", True),
        ("student@bcit.ca", True),
        ("bademail", False),
        ("missingatsign.com", False),
        ("", False),
    ],
)
def test_validate_email(email, expected):
    result = validate_email(email)

    assert result == expected


@pytest.mark.parametrize(
    "password, expected",
    [
        ("12345678", True),
        ("password123", True),
        ("short", False),
        ("", False),
    ],
)
def test_validate_password(password, expected):
    result = validate_password(password)

    assert result == expected

def test_normalize_profile_data_strips_whitespace():
    result = normalize_profile_data(
        email=" test@example.com ",
        favorite_bus_types=[" Standard "],
        favorite_routes=[" 106 "],
        favorite_stops=[" 60607 "],
        theme=" Light ",
        alerts=" on "
    )

    assert result["email"] == "test@example.com"
    assert result["prefs"]["favorite_bus_types"] == ["Standard"]
    assert result["prefs"]["favorite_routes"] == ["106"]
    assert result["prefs"]["favorite_stops"] == ["60607"]
    assert result["prefs"]["theme"] == "Light"
    assert result["prefs"]["alerts"] == "on"


def test_validate_favorite_stops_valid(monkeypatch):
    fake_csv = "stop_code\n12345\n67890\n"

    def fake_open(*args, **kwargs):
        return StringIO(fake_csv)

    monkeypatch.setattr(builtins, "open", fake_open)

    assert validate_favorite_stops("12345") is True


def test_validate_favorite_stops_invalid(monkeypatch):
    fake_csv = "stop_code\n12345\n67890\n"

    def fake_open(*args, **kwargs):
        return StringIO(fake_csv)

    monkeypatch.setattr(builtins, "open", fake_open)

    assert validate_favorite_stops("99999") is False