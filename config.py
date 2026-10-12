"""
Configuration settings, directory paths, and taxonomy definitions
for the MoveInSync Play Store Reviews Intelligence Pipeline.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Base Directory & Environment
BASE_DIR: Path = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

# Data & Output Directories
DATA_DIR: Path = BASE_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
REPORTS_DIR: Path = BASE_DIR / "reports"

# Play Store Application Configuration
APP_PACKAGES: Dict[str, str] = {
    "employee": "com.moveinsync.ets",
    "driver": "com.moveinsync.driver"
}
TARGET_APP: str = "employee"
LANG: str = "en"
COUNTRY: str = "in"
MAX_REVIEWS: int = 10000

# LLM Inference Configuration
LLM_MODEL: str = "gemini-3.8-flash"
BATCH_SIZE: int = 25

# Standardized Domain Theme Taxonomy
KNOWN_THEMES: List[str] = [
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
