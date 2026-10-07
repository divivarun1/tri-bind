# TRI-BIND Professor Demo

All actions are against the fictional local Smart Hospital IoT Network.

1. Start backend and frontend.
2. Open `/demo`.
3. Use `TEMP-001`.
4. Register device if database is empty (`python -m app.seed` seeds the five devices).
5. Run challenge → challenge response → firmware verification → ICU-ZONE-A context verification → CBOT generation/verification → onboarding.
6. Send normal telemetry: MQTT, destination `GATEWAY`, port 1883, normal low packet rate. Evaluate behavior. The device becomes TRUSTED.
7. Open Attack Lab and select `network_scanning` for TEMP-001.
8. The backend inserts simulated malicious telemetry, detects scanning, evaluates behavior and applies a critical override.
9. TEMP-001 becomes QUARANTINED even if its weighted score would otherwise be high.
10. Open device details/security logs/trust history to show the evidence.

No real network attack is performed.
