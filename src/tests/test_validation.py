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


def test_validate_profile_data_missing_username_or_password():
    result = validate_profile_data(
        username="",
        password="",
        email="test@example.com",
        favorite_bus_type="Standard",
        favorite_bus_route="106",
        favorite_bus_stop_id="12345",
        theme="Light",
        alerts="on",
        created="today",
    )

    assert result == "please enter your username and password"


def test_validate_profile_data_non_string_username():
    result = validate_profile_data(
        username=123,
        password="password123",
        email="test@example.com",
        favorite_bus_type="Standard",
        favorite_bus_route="106",
        favorite_bus_stop_id="12345",
        theme="Light",
        alerts="on",
        created="today",
    )

    assert result == "username must be a string."


def test_validate_profile_data_valid_returns_none():
    result = validate_profile_data(
        username="faniel",
        password="password123",
        email="test@example.com",
        favorite_bus_type="Standard",
        favorite_bus_route="106",
        favorite_bus_stop_id="12345",
        theme="Light",
        alerts="on",
        created="today",
    )

    assert result is None


def test_normalize_profile_data_strips_whitespace():
    result = normalize_profile_data(
        username=" faniel ",
        password=" password123 ",
        email=" test@example.com ",
        favorite_bus_type=" Standard ",
        favorite_bus_route=" 106 ",
        favorite_bus_stop_id=" 12345 ",
        theme=" Light ",
        alerts=" on ",
        created=" today ",
    )

    assert result["username"] == "faniel"
    assert result["password"] == "password123"
    assert result["email"] == "test@example.com"
    assert result["preferences"]["favorite_bus_type"] == "Standard"
    assert result["preferences"]["favorite_bus_route"] == "106"
    assert result["preferences"]["favorite_bus_stop_id"] == "12345"
    assert result["preferences"]["theme"] == "Light"
    assert result["preferences"]["alerts"] == "on"
    assert result["created"] == "today"


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