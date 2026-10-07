# TRI-BIND — Context-Bound Progressive Trust for Secure IoT Device Onboarding

Academic prototype for a **fictional Smart Hospital IoT Network**. It demonstrates that authentication is the beginning of trust establishment rather than the end.

## Architecture
React/Vite → REST API → FastAPI → Security/Trust Engine → SQLite.

The backend is authoritative for device state and trust. The frontend only requests actions and renders results.

## Security mechanisms
- Device registration and hashed credentials
- Cryptographically random onboarding challenges with expiry and one-time consumption
- Challenge-response using HMAC-SHA-256 over the hashed prototype credential
- SHA-256 firmware integrity verification
- Expected deployment-context verification
- Context-Bound Onboarding Token (CBOT) using HMAC-SHA-256 and canonical JSON serialization
- CBOT expiry, consumption/replay detection and tamper detection
- Progressive state machine with invalid-transition rejection
- Probation telemetry monitoring
- Behavior and weighted trust scores
- Critical-event override and quarantine
- Security event and trust history persistence

CBOT prototype key is configured by `TRIBIND_CBOT_KEY`. In a real deployment, key storage/rotation and device/gateway provisioning require a dedicated key-management architecture. HMAC does not magically authenticate an arbitrary device.

## Trust model
`TrustScore = 0.30I + 0.25S + 0.20C + 0.25B`.

`B = 0.25 communication_normality + 0.20 destination_normality + 0.15 port_normality + 0.15 connection_success + 0.15 scanning_safety + 0.10 lateral_movement_safety`.

Prototype thresholds: >= 0.80 TRUSTED; 0.50–0.79 SUSPICIOUS/PROBATION; < 0.50 QUARANTINED. Critical events can override a high weighted score. The weights are academic prototype values, not universal security standards.

## Smart Hospital case study
Fictional devices: TEMP-001, ENV-001, PATIENT-001, OXY-001, CAM-001. Contexts: ICU-ZONE-A, WARD-ZONE-B, SECURITY-ZONE. No real hospital is represented or claimed as a deployment.

## Run
Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
PYTHONPATH=. python -m app.seed
PYTHONPATH=. uvicorn app.main:app --reload
```
Frontend:
```bash
cd frontend
npm install
npm run dev
```

## API
See FastAPI `/docs` after starting the backend. Required routes include `/health`, device onboarding endpoints, telemetry/evaluation, trust history, security events, `/attack-lab/simulate`, `/attack-lab/history`, and `/dashboard/summary`.

## Testing
```bash
cd backend
PYTHONPATH=. pytest -q
```

## Limitations
Gateway compromise is a major limitation. The prototype does not provide hardware-rooted identity, secure boot, remote attestation, production key management, or real network enforcement. Attack Lab simulations are intentionally safe and local.

## Future work
Add hardware-backed keys, remote attestation, signed firmware metadata, gateway authorization, policy-driven access control, persistent audit integrity, production secret management, and calibrated behavioral baselines.
