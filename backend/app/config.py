import os

DB_PATH = os.getenv("TRIBIND_DB", os.path.join(os.path.dirname(os.path.dirname(__file__)), "tribind.db"))
NETWORK_ID = os.getenv("TRIBIND_NETWORK_ID", "SMART-HOSPITAL-IOT")
CBOT_KEY = os.getenv("TRIBIND_CBOT_KEY", "academic-prototype-change-me")
CHALLENGE_TTL_SECONDS = int(os.getenv("TRIBIND_CHALLENGE_TTL", "120"))
CBOT_TTL_SECONDS = int(os.getenv("TRIBIND_CBOT_TTL", "300"))
PROBATION_MIN_TELEMETRY = int(os.getenv("TRIBIND_PROBATION_MIN_TELEMETRY", "3"))
