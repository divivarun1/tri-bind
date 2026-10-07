# Security Notes

## Identity
Registration stores a SHA-256 digest of the prototype credential. Challenge nonces are generated with Python `secrets`; challenges expire and are one-time consumable.

## Firmware
Expected firmware is represented by a SHA-256 digest. A mismatch produces a critical security event and prevents trust establishment.

## Context
Each device has an expected deployment context. A mismatch is recorded and cannot lead to TRUSTED.

## CBOT
CBOT is HMAC-SHA-256 over canonical JSON containing device identity, firmware hash, device/gateway nonces, network, context and timestamp. Tokens have expiry and are one-time consumable. Replay and tampering are detected.

## Trust
Progressive trust uses identity/security/context/behavior confidence. Critical security events can override the weighted score and force QUARANTINED. Quarantine requires remediation/re-onboarding; there is no automatic return to TRUSTED.

## Prototype limitations
The default key is intentionally development-only. Production deployments need secure key provisioning, rotation, hardware-backed identity, authenticated gateways, secure boot/attestation, transport security, access control and tamper-evident audit storage. Gateway compromise is a major limitation.
