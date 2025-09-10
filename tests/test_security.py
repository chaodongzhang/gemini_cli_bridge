import os
import socket

import gemini_cli_bridge as gcb


def test_is_private_url_blocks_common_privates(monkeypatch):
    assert gcb._is_private_url("http://localhost") is True
    assert gcb._is_private_url("http://127.0.0.1") is True
    assert gcb._is_private_url("http://10.0.0.1") is True
    assert gcb._is_private_url("http://192.168.1.1") is True


def test_is_private_url_allows_public_host_with_mock(monkeypatch):
    # Force DNS resolution to a public IP
    def fake_getaddrinfo(host, *_):
        return [(socket.AF_INET, 0, 0, '', ('93.184.216.34', 0))]

    monkeypatch.setattr(gcb.socket, "getaddrinfo", fake_getaddrinfo)
    assert gcb._is_private_url("https://example.com") is False

