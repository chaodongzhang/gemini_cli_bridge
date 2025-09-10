import json
import os
import sys
import socket

import gemini_cli_bridge as gcb


def check(cond: bool, msg: str) -> None:
    if not cond:
        print(f"[FAIL] {msg}")
        sys.exit(1)
    print(f"[OK]   {msg}")


def main() -> None:
    # _is_private_url blocks private
    check(gcb._is_private_url("http://localhost") is True, "localhost blocked")
    check(gcb._is_private_url("http://127.0.0.1") is True, "127.0.0.1 blocked")

    # allow public with mocked DNS
    def fake_getaddrinfo(host, *_):
        return [(socket.AF_INET, 0, 0, '', ('93.184.216.34', 0))]

    orig_getaddrinfo = gcb.socket.getaddrinfo
    gcb.socket.getaddrinfo = fake_getaddrinfo  # type: ignore
    try:
        check(gcb._is_private_url("https://example.com") is False, "public host allowed")
    finally:
        gcb.socket.getaddrinfo = orig_getaddrinfo  # type: ignore

    # Env-driven truncation
    os.environ["GEMINI_BRIDGE_MAX_OUT"] = "1234"
    check(gcb.get_max_out() == 1234, "GEMINI_BRIDGE_MAX_OUT honored")

    # PATH whitelist behavior
    extra = "/tmp/gcb_test/bin"
    os.makedirs(extra, exist_ok=True)
    os.environ["GEMINI_BRIDGE_EXTRA_PATHS"] = extra
    env = gcb._env_with_path({})
    check(extra not in env.get("PATH", ""), "extra path blocked by default whitelist")

    real_tmp = os.path.realpath("/tmp")
    os.environ["GEMINI_BRIDGE_ALLOWED_PATH_PREFIXES"] = real_tmp
    env = gcb._env_with_path({})
    check(extra in env.get("PATH", ""), "extra path allowed with whitelist")

    # Alias availability and behavior
    check(hasattr(gcb, "GeminiGoogleSearch"), "GeminiGoogleSearch alias exists")
    out = gcb.GeminiGoogleSearch(query="test", limit=1, mode="gcs")
    data = json.loads(out)
    check(data.get("mode") == "gcs", "GeminiGoogleSearch returns gcs mode without keys")
    check(data.get("ok") is False, "GeminiGoogleSearch ok=false without keys")

    # Wrapper returns structured JSON and truncates
    long_out = "X" * 5000
    os.environ["GEMINI_BRIDGE_MAX_OUT"] = "100"
    # Directly validate truncation helper
    tout = gcb._truncate(long_out)
    check("...[truncated]..." in tout and len(tout) < len(long_out), "_truncate applies marker and reduces length")
    # Validate wrapper JSON shape and ok flag (mock run without truncation expectations)
    orig_run = gcb._run
    try:
        def fake_run(cmd, **kwargs):
            return {"cmd": cmd, "exit_code": 0, "stdout": long_out, "stderr": ""}
        gcb._run = fake_run  # type: ignore
        res = json.loads(gcb.gemini_prompt(prompt="hello"))
        check(res.get("ok") is True, "gemini_prompt ok=true on exit 0")
    finally:
        gcb._run = orig_run  # type: ignore

    print("All smoke checks passed.")


if __name__ == "__main__":
    main()
