from io import BytesIO
from unittest.mock import Mock

from tools.fetch_gtfs_static import fetch_gtfs_static
from tools.fetch_types import fetch_types
from tools.hash import hash_pw, verify_pw


def test_hash_pw_and_verify_pw():
    password = "password123"

    hashed = hash_pw(password)

    assert hashed != password.encode("utf-8")
    assert verify_pw(password, hashed) is True
    assert verify_pw("wrongpassword", hashed) is False


def test_fetch_gtfs_static_downloads_and_extracts(monkeypatch):
    fake_response = Mock()
    fake_response.content = b"fake_zip_bytes"

    class FakeZipFile:
        def __init__(self, file_obj):
            self.file_obj = file_obj
            self.extracted_to = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extractall(self, path):
            self.extracted_to = path

    monkeypatch.setattr("tools.fetch_gtfs_static.requests.get", lambda url: fake_response)
    monkeypatch.setattr("tools.fetch_gtfs_static.zipfile.ZipFile", FakeZipFile)

    fetch_gtfs_static()


def test_fetch_types_scrapes_and_writes_pickle(monkeypatch):
    html = """
    <html>
      <body>
        <table></table>
        <table>
          <tbody>
            <tr>
              <td>1000-1001</td><td>x</td><td>2020</td><td>New Flyer</td><td>XDE60</td>
              <td>x</td><td>x</td><td>x</td><td>Yes</td>
            </tr>
          </tbody>
        </table>
        <table></table>
        <table>
          <tbody>
            <tr>
              <td>2000-2001</td><td>x</td><td>2021</td><td>Skoda</td><td>TrolleyBus</td>
              <td>x</td><td>x</td><td>Yes</td>
            </tr>
          </tbody>
        </table>
        <table></table>
        <table>
          <tbody>
            <tr>
              <td>3000-3001</td><td>x</td><td>2022</td><td>Ford</td><td>Shuttle</td>
              <td>x</td><td>x</td><td>x</td><td>No</td>
            </tr>
          </tbody>
        </table>
      </body>
    </html>
    """

    fake_response = Mock()
    fake_response.text = html

    captured = {}

    def fake_dump(data, file_obj):
        captured["data"] = data

    class DummyFile(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("tools.fetch_types.requests.get", lambda url: fake_response)
    monkeypatch.setattr("tools.fetch_types.pickle.dump", fake_dump)
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: DummyFile())

    fetch_types()

    assert "data" in captured
    assert len(captured["data"]) == 3
    assert captured["data"][0]["year"] == "2020"
    assert captured["data"][0]["manufacturer"] == "New Flyer"
    assert captured["data"][0]["model"] == "XDE60"
    assert captured["data"][0]["fn_range"] == [(1000, 1001)]