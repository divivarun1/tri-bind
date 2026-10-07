import sqlite3
from contextlib import contextmanager
from .config import DB_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS contexts (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, network_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS devices (
 device_id TEXT PRIMARY KEY, device_type TEXT NOT NULL, context_id TEXT NOT NULL REFERENCES contexts(id),
 expected_firmware_hash TEXT NOT NULL, identity_secret_hash TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'UNKNOWN',
 registered_at TEXT NOT NULL, quarantined_reason TEXT
);
CREATE TABLE IF NOT EXISTS credentials (
 device_id TEXT PRIMARY KEY REFERENCES devices(device_id) ON DELETE CASCADE,
 credential_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS onboarding_sessions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT NOT NULL REFERENCES devices(device_id),
 gateway_nonce TEXT NOT NULL, challenge TEXT, challenge_expires_at TEXT, challenge_consumed INTEGER NOT NULL DEFAULT 0,
 identity_verified INTEGER NOT NULL DEFAULT 0, firmware_verified INTEGER NOT NULL DEFAULT 0,
 context_verified INTEGER NOT NULL DEFAULT 0, cbot_verified INTEGER NOT NULL DEFAULT 0,
 started_at TEXT NOT NULL, completed_at TEXT
);
CREATE TABLE IF NOT EXISTS cbot_tokens (
 id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT NOT NULL REFERENCES devices(device_id),
 token TEXT NOT NULL UNIQUE, device_nonce TEXT NOT NULL, gateway_nonce TEXT NOT NULL, firmware_hash TEXT NOT NULL,
 context_id TEXT NOT NULL, network_id TEXT NOT NULL, issued_at TEXT NOT NULL, expires_at TEXT NOT NULL,
 consumed INTEGER NOT NULL DEFAULT 0, tamper_detected INTEGER NOT NULL DEFAULT 0, replay_detected INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS telemetry (
 id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT NOT NULL REFERENCES devices(device_id),
 timestamp TEXT NOT NULL, packet_rate REAL NOT NULL, communication_frequency REAL NOT NULL,
 destination TEXT NOT NULL, port INTEGER NOT NULL, protocol TEXT NOT NULL, connection_success REAL NOT NULL,
 scanning INTEGER NOT NULL DEFAULT 0, lateral_movement INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS trust_scores (
 id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT NOT NULL REFERENCES devices(device_id), timestamp TEXT NOT NULL,
 identity_score REAL NOT NULL, security_score REAL NOT NULL, context_score REAL NOT NULL, behavior_score REAL NOT NULL,
 weighted_score REAL NOT NULL, final_state TEXT NOT NULL, override_applied INTEGER NOT NULL DEFAULT 0, override_reason TEXT,
 telemetry_id INTEGER REFERENCES telemetry(id)
);
CREATE TABLE IF NOT EXISTS security_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT, timestamp TEXT NOT NULL, severity TEXT NOT NULL,
 event_type TEXT NOT NULL, message TEXT NOT NULL, details TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_device ON security_events(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_trust_device ON trust_scores(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_device ON telemetry(device_id, timestamp);
"""

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as db:
        db.executescript(SCHEMA)
