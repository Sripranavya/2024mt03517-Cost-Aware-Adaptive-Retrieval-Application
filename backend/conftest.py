"""Pytest configuration: make the backend package importable and force local mode."""

import os
import sys
from pathlib import Path

# Ensure the backend root (containing the `app` package) is importable.
BACKEND_ROOT = Path(__file__).parent.resolve()
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Tests must never touch real AWS.
os.environ.setdefault("USE_LOCAL_MOCKS", "true")
os.environ.setdefault("APP_ENV", "test")
