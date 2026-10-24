"""Settings loaded from the repo-root .env file (copy .env.example to .env).

Every external service has a MOCK_* flag. With all mocks on (the default), the whole
flow runs locally with no API keys. Owner of this file: Bereket.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    # Core (Bereket)
    app_env: str = "dev"
    database_url: str = f"sqlite:///{BACKEND_DIR / 'dev.db'}"
    public_web_url: str = "http://localhost:5173"  # the React site; MUST be public https for Terac
    public_api_url: str = "http://localhost:8000"  # used for links in emails/texts
    secret_key: str = "dev-secret-change-me"
    data_dir: Path = BACKEND_DIR / "data"  # screenshots / proofs

    # Claude (shared)
    anthropic_api_key: str = ""  # passed to the SDK explicitly (.env values are not exported)
    claude_model: str = "claude-opus-5-5"
    claude_effort: str = "medium"
    mock_llm: bool = True

    # Page reading + testing (Bereket)
    solari_api_key: str = ""
    mock_solari: bool = True
    test_participants: int = 4  # per test ($4.50 each on Terac), split evenly between original and rewrite
    test_seconds: int = 10  # how long each participant sees the page
    min_answers_per_arm: int = 2  # grade once both arms have this many...
    test_timeout_minutes: int = 120  # ...or after this long, with whatever answers came in

    # Whop: Natnael ONLY (his account). Never set these on anyone else's machine.
    whop_api_key: str = ""
    whop_company_id: str = ""
    whop_product_id: str = ""
    whop_plan_id: str = ""
    whop_webhook_secret: str = ""
    mock_whop: bool = True

    # Email + text (Natnael)
    resend_api_key: str = ""
    email_from: str = "FirstGlance <hello@example.com>"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    mock_notify: bool = True

    # Growth + research (Yared)
    exa_api_key: str = ""
    mock_exa: bool = True
    terac_api_key: str = ""
    mock_terac: bool = True
    bluesky_handle: str = ""  # e.g. firstglance.bsky.social; empty = Growth posts only on our site
    bluesky_app_password: str = ""

    # Guardrails (Bereket). Agents can never go outside these.
    starting_price_usd: float = 15.0
    price_min_usd: float = 5.0
    price_max_usd: float = 30.0
    price_change_cooldown_minutes: int = 60
    ad_budget_usd_per_day: float = 20.0
    kill_switch: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
