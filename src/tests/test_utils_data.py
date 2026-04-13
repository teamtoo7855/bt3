import builtins
import importlib.util
import os
import pickle
from io import StringIO, BytesIO
from pathlib import Path


def load_real_utils_data(monkeypatch):
    fake_processed = [
        {
            "fn_range": [(1234,)],
            "year": "2020",
            "manufacturer": "New Flyer",
            "model": "XDE60",
        }
    ]

    fake_stops = (
        "stop_id,stop_code\n"
        "1001,12345\n"
        "1002,67890\n"
    )

    fake_routes = (
        "route_id,route_short_name\n"
        "R1,106\n"
        "R2,144\n"
    )

    real_open = builtins.open

    class DummyFile(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_open(path, mode="r", *args, **kwargs):
        path = str(path)
        if path.endswith("types.pkl"):
            return DummyFile(b"fake")
        if path.endswith("stops.txt"):
            return StringIO(fake_stops)
        if path.endswith("routes.txt"):
            return StringIO(fake_routes)
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(os, "listdir", lambda path: [str(i) for i in range(16)])
    monkeypatch.setattr(pickle, "load", lambda f: fake_processed)

    import tools.fetch_types as fetch_types_mod
    import tools.fetch_gtfs_static as fetch_gtfs_mod

    monkeypatch.setattr(fetch_types_mod, "fetch_types", lambda: None)
    monkeypatch.setattr(fetch_gtfs_mod, "fetch_gtfs_static", lambda: None)

    module_path = Path(__file__).resolve().parents[1] / "utils" / "data.py"
    spec = importlib.util.spec_from_file_location("real_utils_data_for_tests", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_stopcode_to_stopid(monkeypatch):
    utils_data = load_real_utils_data(monkeypatch)

    result = utils_data.load_stopcode_to_stopid("stops.txt")

    assert result == {
        "12345": "1001",
        "67890": "1002",
    }


def test_load_short_to_routeid(monkeypatch):
    utils_data = load_real_utils_data(monkeypatch)

    result = utils_data.load_short_to_routeid("routes.txt")

    assert result == {
        "106": "R1",
        "144": "R2",
    }


def test_check_id_returns_bus_name(monkeypatch):
    utils_data = load_real_utils_data(monkeypatch)

    result = utils_data.check_id(1234)

    assert result == "2020 New Flyer XDE60"


def test_check_id_returns_none_when_not_found(monkeypatch):
    utils_data = load_real_utils_data(monkeypatch)

    result = utils_data.check_id(9999)

    assert result is None