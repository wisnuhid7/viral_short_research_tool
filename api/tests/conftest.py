"""Test bootstrap. Sets VST_DB_PATH to a throwaway file *before* importing the
app so the settings singleton never touches the real repo `data.db`.
"""
import os
import tempfile
from pathlib import Path

_TMP_DIR = Path(tempfile.mkdtemp(prefix="vst-api-test-"))
os.environ["VST_DB_PATH"] = str(_TMP_DIR / "test.db")
os.environ["VST_MEDIA_ROOT"] = str(_TMP_DIR / "media")
os.environ.setdefault("NODE_ENV", "test")
os.environ.setdefault("YOUTUBE_API_KEY", "test-youtube-key")
# Keep the periodic Whop MCP sync from spawning `npx mcp-remote` during tests.
os.environ["VST_WHOP_SYNC_ENABLED"] = "false"

import pytest  # noqa: E402

from api.app.db.database import close_db, reset_db  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    reset_db()
    yield
    close_db()