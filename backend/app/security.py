import hashlib, hmac, json, secrets
from datetime import datetime, timezone, timedelta
from .config import CBOT_KEY

def now(): return datetime.now(timezone.utc)
def iso(dt): return dt.isoformat()
def parse_ts(v): return datetime.fromisoformat(v.replace('Z','+00:00'))
def sha256_hex(value: str): return hashlib.sha256(value.encode()).hexdigest()
def hash_secret(secret: str): return sha256_hex(secret)
def verify_secret(secret: str, digest: str): return hmac.compare_digest(hash_secret(secret), digest)
def nonce(n=32): return secrets.token_urlsafe(n)

def canonical_cbot_payload(device_id, firmware_hash, device_nonce, gateway_nonce, network_id, context_id, timestamp):
    return json.dumps({"context_id":context_id,"device_id":device_id,"device_nonce":device_nonce,"firmware_hash":firmware_hash,"gateway_nonce":gateway_nonce,"network_id":network_id,"timestamp":timestamp}, separators=(',', ':'), sort_keys=True).encode()

def cbot_hmac(**kwargs):
    return hmac.new(CBOT_KEY.encode(), canonical_cbot_payload(**kwargs), hashlib.sha256).hexdigest()

def behavior_score(t):
    # Prototype weights; thresholds are academic demonstration values, not security standards.
    communication = max(0.0, min(1.0, 1.0 - abs(float(t['packet_rate'])-2.0)/20.0))
    destination = 1.0 if t['destination'] == 'GATEWAY' else 0.0
    port = 1.0 if int(t['port']) == 1883 else 0.0
    protocol = 1.0 if t['protocol'].upper() == 'MQTT' else 0.0
    communication_normality = (communication + protocol) / 2
    connection_success = max(0.0, min(1.0, float(t['connection_success'])))
    scanning_safety = 0.0 if t['scanning'] else 1.0
    lateral_safety = 0.0 if t['lateral_movement'] else 1.0
    return round(0.25*communication_normality + 0.20*destination + 0.15*port + 0.15*connection_success + 0.15*scanning_safety + 0.10*lateral_safety, 4)
