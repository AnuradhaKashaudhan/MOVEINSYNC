import os
from pathlib import Path
from dotenv import load_dotenv

# Paths
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"

# Play Store Config
APP_PACKAGES = {
    "employee": "com.moveinsync.ets",
    "driver": "com.moveinsync.driver"
}
TARGET_APP = "employee"
LANG = "en"
COUNTRY = "in"
MAX_REVIEWS = 10000

# LLM Config
LLM_MODEL = "gemini-3.8-flash"
BATCH_SIZE = 25

# Standardized Theme Taxonomy
KNOWN_THEMES = [
    "LOCATION_ETA",
    "APP_CRASH_OPEN",
    "SLOW_PERFORMANCE",
    "SUPPORT",
    "NO_SHOW",
    "LOGIN_OTP",
    "BOOKING",
    "NOTIFICATIONS",
    "UI_REDESIGN",
    "DRIVER_CONTACT",
    "PERMISSIONS",
    "ROUTING_STOPS",
    "FEATURE_REQUEST",
    "PARKING_SEAT",
    "RATING_FEEDBACK",
    "OTHER_DRIVER_BEHAVIOUR",
    "POSITIVE"
]
