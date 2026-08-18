import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    max_discount_pct: int = int(os.getenv("MAX_DISCOUNT_PCT", "15"))
    ambiguous_band_low: int = int(os.getenv("AMBIGUOUS_BAND_LOW", "40"))
    ambiguous_band_high: int = int(os.getenv("AMBIGUOUS_BAND_HIGH", "70"))
    audit_log_path: str = os.getenv("AUDIT_LOG_PATH", "audit_log.jsonl")


settings = Settings()
