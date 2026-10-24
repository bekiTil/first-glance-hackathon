import os
import sys
from pathlib import Path

# Isolated DB + all mocks on, before the app is imported.
_db = Path(__file__).parent / "test.db"
_db.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
for flag in ("LLM", "SOLARI", "WHOP", "NOTIFY", "EXA", "TERAC"):
    os.environ[f"MOCK_{flag}"] = "true"
os.environ["KILL_SWITCH"] = "false"
# Never let tests reach real services, whatever is in .env.
for key in (
    "ANTHROPIC_API_KEY",
    "BLUESKY_HANDLE",
    "BLUESKY_APP_PASSWORD",
    "RESEND_API_KEY",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "WHOP_API_KEY",
    "WHOP_WEBHOOK_SECRET",
    "TERAC_API_KEY",
    "EXA_API_KEY",
    "SOLARI_API_KEY",
):
    os.environ[key] = ""
os.environ["PUBLIC_WEB_URL"] = "http://localhost:5173"
os.environ["PUBLIC_API_URL"] = "http://localhost:8000"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
