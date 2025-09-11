# Changelog

All notable changes to this project will be documented in this file.

## [0.1.2] - 2025-09-11
- CI: Add GitHub Actions workflow to publish to PyPI on tag push (requires `PYPI_API_TOKEN`).
- Docs: Document PyPI installation and GitHub Releases downloads in both READMEs.

## [0.1.1] - 2025-09-11
- Refactor: Introduce `_run_gemini_and_format_output` and refactor all `gemini_*` tools to use it for consistent JSON output.
- Fix: Simplify `WebFetch` to use `requests` only; fix truncation using `get_max_out()` (previously referred to undefined `MAX_OUT`).
- Tests: Add `tests/test_webfetch.py` and `tests/conftest.py` (fastmcp shim); update smoke checks.
- Docs: Add Developer Notes for wrapper helper and WebFetch behavior.

