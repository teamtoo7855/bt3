from io import StringIO, BytesIO
import builtins


def test_load_stopcode_to_stopid(monkeypatch):
    from utils.data import load_stopcode_to_stopid

    fake_csv = (
        "stop_id,stop_code\n"
        "1001,12345\n"
        "1002,67890\n"
    )

    def fake_open(*args, **kwargs):
        return StringIO(fake_csv)

    monkeypatch.setattr(builtins, "open", fake_open)

    result = load_stopcode_to_stopid("fake_path.txt")

    assert result == {
        "12345": "1001",
        "67890": "1002",
    }


def test_load_short_to_routeid(monkeypatch):
    from utils.data import load_short_to_routeid

    fake_csv = (
        "route_id,route_short_name\n"
        "R1,106\n"
        "R2,144\n"
    )

    def fake_open(*args, **kwargs):
        return StringIO(fake_csv)

    monkeypatch.setattr(builtins, "open", fake_open)

    result = load_short_to_routeid("fake_path.txt")

    assert result == {
        "106": "R1",
        "144": "R2",
    }


def test_check_id_returns_bus_name(monkeypatch):
    from utils import data as utils_data

    fake_processed = [
        {
            "fn_range": [(1234,)],
            "year": "2020",
            "manufacturer": "New Flyer",
            "model": "XDE60",
        }
    ]

    class DummyFile(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_open(*args, **kwargs):
        return DummyFile(b"fake")

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(utils_data.pickle, "load", lambda f: fake_processed)

    result = utils_data.check_id(1234)

    assert result == "2020 New Flyer XDE60"


def test_check_id_returns_none_when_not_found(monkeypatch):
    from utils import data as utils_data

    fake_processed = [
        {
            "fn_range": [(1234,)],
            "year": "2020",
            "manufacturer": "New Flyer",
            "model": "XDE60",
        }
    ]

    class DummyFile(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_open(*args, **kwargs):
        return DummyFile(b"fake")

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(utils_data.pickle, "load", lambda f: fake_processed)

    result = utils_data.check_id(9999)

    assert result is None