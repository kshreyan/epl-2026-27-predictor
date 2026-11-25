"""espn_get retries transient ESPN failures (the 2026-11-21 weekly run
died on a single TLS error) but never retries a real 4xx answer and
never swallows the final failure."""
import sys
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.data_collection import espn_api  # noqa: E402


def _response(status: int) -> requests.Response:
    r = requests.Response()
    r.status_code = status
    r.url = "https://site.api.espn.com/x"
    r._content = b"{}"
    return r


def _fake_get(outcomes):
    calls = []

    def fake(url, params=None, headers=None, timeout=None):
        calls.append(url)
        outcome = outcomes[len(calls) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return _response(outcome)
    return fake, calls


def test_ssl_error_is_retried_then_succeeds(monkeypatch):
    fake, calls = _fake_get([requests.exceptions.SSLError("tlsv1 alert internal error"), 200])
    monkeypatch.setattr(espn_api.requests, "get", fake)
    sleeps = []
    resp = espn_api.espn_get("https://site.api.espn.com/x", _sleep=sleeps.append)
    assert resp.status_code == 200
    assert len(calls) == 2
    assert sleeps == [espn_api.RETRY_BACKOFF_SECONDS]


def test_server_errors_back_off_exponentially(monkeypatch):
    fake, calls = _fake_get([503, 502, 200])
    monkeypatch.setattr(espn_api.requests, "get", fake)
    sleeps = []
    assert espn_api.espn_get("https://site.api.espn.com/x", _sleep=sleeps.append).status_code == 200
    assert sleeps == [espn_api.RETRY_BACKOFF_SECONDS, espn_api.RETRY_BACKOFF_SECONDS * 2]


def test_persistent_connection_failure_raises_after_all_attempts(monkeypatch):
    fake, calls = _fake_get([requests.exceptions.ConnectionError("down")] * espn_api.RETRY_ATTEMPTS)
    monkeypatch.setattr(espn_api.requests, "get", fake)
    with pytest.raises(requests.exceptions.ConnectionError):
        espn_api.espn_get("https://site.api.espn.com/x", _sleep=lambda s: None)
    assert len(calls) == espn_api.RETRY_ATTEMPTS


def test_persistent_server_error_raises_http_error(monkeypatch):
    fake, calls = _fake_get([500] * espn_api.RETRY_ATTEMPTS)
    monkeypatch.setattr(espn_api.requests, "get", fake)
    with pytest.raises(requests.exceptions.HTTPError):
        espn_api.espn_get("https://site.api.espn.com/x", _sleep=lambda s: None)
    assert len(calls) == espn_api.RETRY_ATTEMPTS


def test_client_error_is_not_retried(monkeypatch):
    fake, calls = _fake_get([404])
    monkeypatch.setattr(espn_api.requests, "get", fake)
    with pytest.raises(requests.exceptions.HTTPError):
        espn_api.espn_get("https://site.api.espn.com/x", _sleep=lambda s: None)
    assert len(calls) == 1
