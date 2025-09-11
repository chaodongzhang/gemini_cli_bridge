import json
import socket
import sys

import gemini_cli_bridge as gcb


class DummyResp:
    def __init__(self, text: str, status_code: int = 200, ok: bool = True):
        self.text = text
        self.status_code = status_code
        self.ok = ok


def test_webfetch_blocks_private(monkeypatch):
    out = gcb.WebFetch("http://127.0.0.1")
    data = json.loads(out)
    assert data.get("ok") is False
    assert "Blocked" in (data.get("error") or "")


def test_webfetch_truncates_and_ok_true(monkeypatch):
    # Force DNS to public IP for example.com
    def fake_getaddrinfo(host, *_):
        return [(socket.AF_INET, 0, 0, '', ('93.184.216.34', 0))]

    monkeypatch.setattr(gcb.socket, "getaddrinfo", fake_getaddrinfo)

    # Limit output size
    monkeypatch.setenv("GEMINI_BRIDGE_MAX_OUT", "100")

    # Monkeypatch requests.get
    class DummyRequests:
        @staticmethod
        def get(url, headers=None, timeout=None):
            return DummyResp("X" * 500)

    monkeypatch.setitem(sys.modules, 'requests', DummyRequests())

    out = gcb.WebFetch("https://example.com")
    data = json.loads(out)
    assert data.get("ok") is True
    content = data.get("content") or ""
    assert len(content) <= 120  # allow for marker overhead
    assert "...[truncated]..." in content
