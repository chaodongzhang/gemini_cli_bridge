import json

import gemini_cli_bridge as gcb


def test_gemini_google_search_alias_exists():
    assert hasattr(gcb, "GeminiGoogleSearch")


def test_gemini_google_search_alias_gcs_mode_without_keys():
    # Force mode=gcs without keys should return ok:false and mode:gcs (no network call)
    out = gcb.GeminiGoogleSearch(query="x", limit=1, mode="gcs")
    data = json.loads(out)
    assert data.get("mode") == "gcs"
    assert data.get("ok") is False

