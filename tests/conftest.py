import os
import sys


def pytest_sessionstart(session):
    # Ensure tests/ is importable so tests/fastmcp.py satisfies `import fastmcp`
    test_dir = os.path.dirname(__file__)
    if test_dir not in sys.path:
        sys.path.insert(0, test_dir)

