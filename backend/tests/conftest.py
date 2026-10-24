import os
import sys
from pathlib import Path

# Isolated DB + all mocks on, before the app is imported.
_db = Path(__file__).parent / "test.db"
_db.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
for flag in ("LLM", "TICKETS", "SOLARI", "WHOP", "NOTIFY", "EXA", "TERAC"):
    os.environ[f"MOCK_{flag}"] = "true"
os.environ["KILL_SWITCH"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
