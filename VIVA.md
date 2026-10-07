# TRI-BIND Viva — Questions & Answers

**What is TRI-BIND?** A context-bound progressive trust scheme for IoT onboarding.

**Authentication vs trust?** Authentication establishes identity; trust also considers security state, deployment context and later behavior.

**What is CBOT?** A Context-Bound Onboarding Token binding identity, firmware, fresh nonces, network and context with HMAC-SHA-256.

**Why HMAC?** It provides integrity/authentication for data when the trusted parties share a secret key.

**What is a nonce?** A fresh unpredictable value used to prevent replay and make each protocol run distinct.

**How is replay prevented?** Challenges and CBOTs expire and are marked consumed; reuse generates a security event.

**Why SHA-256 firmware hashes?** To compare the observed firmware measurement with the expected registered measurement.

**Why bind context?** A valid device in the wrong deployment zone should not automatically receive the same trust.

**Why probation?** Successful onboarding is not sufficient evidence of safe ongoing behavior.

**What does behavior monitoring detect?** Abnormal packet/communication rates, destinations, ports/protocols, failures, scanning and lateral movement indicators.

**Trust formula?** `0.30I + 0.25S + 0.20C + 0.25B`.

**Why critical override?** Gradual weighted trust can hide severe events. A confirmed critical event can immediately quarantine the device without manipulating unrelated component scores.

**What is quarantine?** A restrictive terminal state requiring remediation/re-onboarding; it cannot automatically become TRUSTED.

**What is Attack Lab?** Safe local simulations that feed the real backend engine rather than directly editing state from the UI.

**Why FastAPI?** Typed validation, clear REST endpoints and simple Python integration.

**Why React?** Component-based dashboard UI and route-based views.

**Why SQLite?** Lightweight persistence suitable for an academic prototype.

**Main limitation?** Gateway compromise remains a major limitation; this prototype is not a production hospital security system.
