import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db, get_db
from .config import (
    NETWORK_ID,
    CHALLENGE_TTL_SECONDS,
    CBOT_TTL_SECONDS,
    PROBATION_MIN_TELEMETRY,
)
from .models import *
from .security import *


app = FastAPI(
    title="TRI-BIND API",
    version="1.0.0",
    description="Academic Context-Bound Progressive Trust prototype",
)


# ============================================================
# CORS
# ============================================================
# Allows the local React/Vite frontend to communicate with
# the FastAPI backend.
#
# Vite may use port 5173 or automatically move to 5174,
# 5175, etc. during local development.
#
# In a production deployment, restrict this to the actual
# deployed frontend origin.
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATES
# ============================================================

STATES = [
    "UNKNOWN",
    "IDENTITY_VERIFIED",
    "SECURITY_STATE_VERIFIED",
    "CONTEXT_VERIFIED",
    "CBOT_VERIFIED",
    "PROBATION",
    "TRUSTED",
    "SUSPICIOUS",
    "QUARANTINED",
]


# ============================================================
# SECURITY EVENTS
# ============================================================

def event(
    db,
    device_id,
    severity,
    typ,
    msg,
    details=None,
):
    db.execute(
        """
        INSERT INTO security_events(
            device_id,
            timestamp,
            severity,
            event_type,
            message,
            details
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            device_id,
            iso(now()),
            severity,
            typ,
            msg,
            json.dumps(details) if details else None,
        ),
    )


# ============================================================
# DEVICE HELPERS
# ============================================================

def device_or_404(db, did):
    row = db.execute(
        "SELECT * FROM devices WHERE device_id=?",
        (did,),
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    return row


def transition(
    db,
    did,
    new_state,
    reason=None,
):
    device = device_or_404(db, did)

    old_state = device["state"]

    allowed = {
        "UNKNOWN": {
            "IDENTITY_VERIFIED",
        },
        "IDENTITY_VERIFIED": {
            "SECURITY_STATE_VERIFIED",
        },
        "SECURITY_STATE_VERIFIED": {
            "CONTEXT_VERIFIED",
        },
        "CONTEXT_VERIFIED": {
            "CBOT_VERIFIED",
        },
        "CBOT_VERIFIED": {
            "PROBATION",
        },
        "PROBATION": {
            "TRUSTED",
            "SUSPICIOUS",
            "QUARANTINED",
        },
        "SUSPICIOUS": {
            "PROBATION",
            "QUARANTINED",
        },
        "TRUSTED": {
            "SUSPICIOUS",
            "QUARANTINED",
        },
        "QUARANTINED": set(),
    }

    if new_state not in allowed.get(old_state, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Invalid state transition {old_state} -> {new_state}",
        )

    db.execute(
        """
        UPDATE devices
        SET state=?,
            quarantined_reason=?
        WHERE device_id=?
        """,
        (
            new_state,
            reason if new_state == "QUARANTINED" else None,
            did,
        ),
    )

    event(
        db,
        did,
        "INFO"
        if new_state not in ("QUARANTINED", "SUSPICIOUS")
        else "HIGH",
        "STATE_TRANSITION",
        f"{old_state} -> {new_state}",
        {
            "from": old_state,
            "to": new_state,
            "reason": reason,
        },
    )


# ============================================================
# ONBOARDING SESSION HELPERS
# ============================================================

def latest_session(db, did):
    return db.execute(
        """
        SELECT *
        FROM onboarding_sessions
        WHERE device_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (did,),
    ).fetchone()


def ensure_session(db, did):
    session = latest_session(db, did)

    if not session:
        db.execute(
            """
            INSERT INTO onboarding_sessions(
                device_id,
                gateway_nonce,
                started_at
            )
            VALUES(?,?,?)
            """,
            (
                did,
                nonce(24),
                iso(now()),
            ),
        )

        session = latest_session(db, did)

    return session


# ============================================================
# BEHAVIOR + TRUST EVALUATION
# ============================================================

def evaluate(db, did, telemetry_row):
    device = device_or_404(db, did)

    behavior = behavior_score(telemetry_row)

    weighted = round(
        0.30 * 1.0
        + 0.25 * (
            1.0
            if device["expected_firmware_hash"]
            else 0.0
        )
        + 0.20 * 1.0
        + 0.25 * behavior,
        4,
    )

    critical = []

    if telemetry_row["scanning"]:
        critical.append("severe network scanning")

    if telemetry_row["lateral_movement"]:
        critical.append("lateral movement")

    if device["state"] == "QUARANTINED":
        final = "QUARANTINED"

    elif critical:
        final = "QUARANTINED"

    elif weighted >= 0.80:
        final = "TRUSTED"

    elif weighted >= 0.50:
        final = "SUSPICIOUS"

    else:
        final = "QUARANTINED"

    override = bool(critical)

    reason = (
        "; ".join(critical)
        if critical
        else None
    )

    db.execute(
        """
        INSERT INTO trust_scores(
            device_id,
            timestamp,
            identity_score,
            security_score,
            context_score,
            behavior_score,
            weighted_score,
            final_state,
            override_applied,
            override_reason,
            telemetry_id
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            did,
            iso(now()),
            1.0,
            1.0,
            1.0,
            behavior,
            weighted,
            final,
            int(override),
            reason,
            telemetry_row["id"],
        ),
    )

    if final != device["state"]:

        if final == "QUARANTINED":

            db.execute(
                """
                UPDATE devices
                SET state=?,
                    quarantined_reason=?
                WHERE device_id=?
                """,
                (
                    final,
                    reason or "Trust policy violation",
                    did,
                ),
            )

            event(
                db,
                did,
                "CRITICAL",
                "CRITICAL_OVERRIDE",
                reason or "Critical trust override",
                {
                    "weighted_score": weighted,
                },
            )

        elif final in (
            "TRUSTED",
            "SUSPICIOUS",
        ) and device["state"] in (
            "PROBATION",
            "SUSPICIOUS",
        ):
            transition(
                db,
                did,
                final,
            )

    return {
        "behavior_score": behavior,
        "weighted_score": weighted,
        "final_state": final,
        "override_applied": override,
        "override_reason": reason,
    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    init_db()


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "tri-bind",
        "network": NETWORK_ID,
    }


# ============================================================
# DEVICE REGISTRATION
# ============================================================

@app.post("/devices")
def register(x: DeviceCreate):

    with get_db() as db:

        if db.execute(
            "SELECT 1 FROM devices WHERE device_id=?",
            (x.device_id,),
        ).fetchone():

            raise HTTPException(
                status_code=409,
                detail="Device ID already registered",
            )

        if not db.execute(
            "SELECT 1 FROM contexts WHERE id=?",
            (x.context_id,),
        ).fetchone():

            raise HTTPException(
                status_code=400,
                detail="Unknown context",
            )

        db.execute(
            """
            INSERT INTO devices
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                x.device_id,
                x.device_type,
                x.context_id,
                x.firmware_hash,
                hash_secret(x.credential),
                "UNKNOWN",
                iso(now()),
                None,
            ),
        )

        db.execute(
            """
            INSERT INTO credentials
            VALUES(?,?,?)
            """,
            (
                x.device_id,
                hash_secret(x.credential),
                iso(now()),
            ),
        )

        event(
            db,
            x.device_id,
            "INFO",
            "DEVICE_REGISTERED",
            "Device registered",
        )

        return {
            "device_id": x.device_id,
            "state": "UNKNOWN",
        }


# ============================================================
# DEVICE LIST
# ============================================================

@app.get("/devices")
def devices():

    with get_db() as db:
        return [
            dict(row)
            for row in db.execute(
                """
                SELECT *
                FROM devices
                ORDER BY device_id
                """
            )
        ]


# ============================================================
# DEVICE DETAILS
# ============================================================

@app.get("/devices/{did}")
def device(did: str):

    with get_db() as db:

        device_data = dict(
            device_or_404(
                db,
                did,
            )
        )

        trust_score = db.execute(
            """
            SELECT *
            FROM trust_scores
            WHERE device_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (did,),
        ).fetchone()

        device_data["trust"] = (
            dict(trust_score)
            if trust_score
            else None
        )

        return device_data


# ============================================================
# CHALLENGE GENERATION
# ============================================================

@app.post("/devices/{did}/challenge")
def challenge(did: str):

    with get_db() as db:

        device_or_404(
            db,
            did,
        )

        session = ensure_session(
            db,
            did,
        )

        challenge_value = nonce(24)

        expiration = now().replace(
            microsecond=0
        )

        expiration = (
            expiration
            + __import__("datetime").timedelta(
                seconds=CHALLENGE_TTL_SECONDS
            )
        )

        db.execute(
            """
            UPDATE onboarding_sessions
            SET challenge=?,
                challenge_expires_at=?,
                challenge_consumed=0
            WHERE id=?
            """,
            (
                challenge_value,
                iso(expiration),
                session["id"],
            ),
        )

        return {
            "challenge": challenge_value,
            "expires_at": iso(expiration),
        }


# ============================================================
# IDENTITY VERIFICATION
# ============================================================

@app.post("/devices/{did}/verify-identity")
def verify_identity(
    did: str,
    x: IdentityVerify,
):

    with get_db() as db:

        device_data = device_or_404(
            db,
            did,
        )

        session = latest_session(
            db,
            did,
        )

        if (
            not session
            or session["challenge"] != x.challenge
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid challenge",
            )

        if session["challenge_consumed"]:
            raise HTTPException(
                status_code=409,
                detail="Challenge already consumed",
            )

        if now() > parse_ts(
            session["challenge_expires_at"]
        ):
            raise HTTPException(
                status_code=400,
                detail="Challenge expired",
            )

        expected = hmac.new(
            device_data["identity_secret_hash"].encode(),
            x.challenge.encode(),
            __import__("hashlib").sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            expected,
            x.response,
        ):

            event(
                db,
                did,
                "HIGH",
                "IDENTITY_FAILURE",
                "Challenge response failed",
            )

            raise HTTPException(
                status_code=401,
                detail="Identity verification failed",
            )

        db.execute(
            """
            UPDATE onboarding_sessions
            SET identity_verified=1,
                challenge_consumed=1
            WHERE id=?
            """,
            (session["id"],),
        )

        if device_data["state"] == "UNKNOWN":

            transition(
                db,
                did,
                "IDENTITY_VERIFIED",
            )

        return {
            "verified": True,
            "state": "IDENTITY_VERIFIED",
        }


# ============================================================
# FIRMWARE VERIFICATION
# ============================================================

@app.post("/devices/{did}/firmware")
def firmware(
    did: str,
    x: FirmwareVerify,
):

    with get_db() as db:

        device_data = device_or_404(
            db,
            did,
        )

        ok = hmac.compare_digest(
            device_data["expected_firmware_hash"],
            x.current_firmware_hash,
        )

        session = latest_session(
            db,
            did,
        )

        if (
            not session
            or not session["identity_verified"]
        ):
            raise HTTPException(
                status_code=409,
                detail="Identity must be verified first",
            )

        if not ok:

            event(
                db,
                did,
                "CRITICAL",
                "FIRMWARE_INTEGRITY_FAILURE",
                "Firmware hash mismatch",
                {
                    "expected": device_data[
                        "expected_firmware_hash"
                    ],
                    "actual": x.current_firmware_hash,
                },
            )

            db.execute(
                """
                UPDATE devices
                SET state=?,
                    quarantined_reason=?
                WHERE device_id=?
                """,
                (
                    "QUARANTINED",
                    "Critical firmware integrity violation",
                    did,
                ),
            )

            db.commit()

            raise HTTPException(
                status_code=403,
                detail="Firmware integrity failed; device quarantined",
            )

        db.execute(
            """
            UPDATE onboarding_sessions
            SET firmware_verified=1
            WHERE id=?
            """,
            (session["id"],),
        )

        transition(
            db,
            did,
            "SECURITY_STATE_VERIFIED",
        )

        return {
            "verified": True,
            "state": "SECURITY_STATE_VERIFIED",
        }


@app.post("/devices/{did}/verify-firmware")
def verify_firmware_alias(
    did: str,
    x: FirmwareVerify,
):
    return firmware(
        did,
        x,
    )


# ============================================================
# CONTEXT VERIFICATION
# ============================================================

@app.post("/devices/{did}/verify-context")
def verify_context(
    did: str,
    x: ContextVerify,
):

    with get_db() as db:

        device_data = device_or_404(
            db,
            did,
        )

        session = latest_session(
            db,
            did,
        )

        if (
            not session
            or not session["firmware_verified"]
        ):
            raise HTTPException(
                status_code=409,
                detail="Security state must be verified first",
            )

        if x.context_id != device_data["context_id"]:

            event(
                db,
                did,
                "HIGH",
                "CONTEXT_MISMATCH",
                "Unexpected deployment context",
                {
                    "expected": device_data[
                        "context_id"
                    ],
                    "actual": x.context_id,
                },
            )

            db.execute(
                """
                UPDATE devices
                SET state=?,
                    quarantined_reason=?
                WHERE device_id=?
                """,
                (
                    "SUSPICIOUS",
                    "Context mismatch",
                    did,
                ),
            )

            db.commit()

            raise HTTPException(
                status_code=403,
                detail="Context mismatch",
            )

        db.execute(
            """
            UPDATE onboarding_sessions
            SET context_verified=1
            WHERE id=?
            """,
            (session["id"],),
        )

        transition(
            db,
            did,
            "CONTEXT_VERIFIED",
        )

        return {
            "verified": True,
            "state": "CONTEXT_VERIFIED",
        }


# ============================================================
# CBOT GENERATION
# ============================================================

@app.post("/devices/{did}/cbot/generate")
def generate_cbot(
    did: str,
    x: CbotGenerate,
):

    with get_db() as db:

        device_data = device_or_404(
            db,
            did,
        )

        session = latest_session(
            db,
            did,
        )

        if (
            not session
            or not session["context_verified"]
        ):
            raise HTTPException(
                status_code=409,
                detail="Context must be verified first",
            )

        device_nonce = nonce(24)

        timestamp = iso(now())

        expiration = iso(
            now()
            + __import__("datetime").timedelta(
                seconds=CBOT_TTL_SECONDS
            )
        )

        token = cbot_hmac(
            device_id=did,
            firmware_hash=x.firmware_hash,
            device_nonce=device_nonce,
            gateway_nonce=session["gateway_nonce"],
            network_id=NETWORK_ID,
            context_id=device_data["context_id"],
            timestamp=timestamp,
        )

        db.execute(
            """
            INSERT INTO cbot_tokens(
                device_id,
                token,
                device_nonce,
                gateway_nonce,
                firmware_hash,
                context_id,
                network_id,
                issued_at,
                expires_at
            )
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                did,
                token,
                device_nonce,
                session["gateway_nonce"],
                x.firmware_hash,
                device_data["context_id"],
                NETWORK_ID,
                timestamp,
                expiration,
            ),
        )

        return {
            "token": token,
            "device_nonce": device_nonce,
            "gateway_nonce": session["gateway_nonce"],
            "issued_at": timestamp,
            "expires_at": expiration,
        }


# ============================================================
# CBOT VERIFICATION
# ============================================================

@app.post("/devices/{did}/cbot/verify")
def verify_cbot(
    did: str,
    x: CbotVerify,
):

    with get_db() as db:

        device_or_404(
            db,
            did,
        )

        row = db.execute(
            """
            SELECT *
            FROM cbot_tokens
            WHERE device_id=?
              AND token=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                did,
                x.token,
            ),
        ).fetchone()

        if not row:

            latest = db.execute(
                """
                SELECT id
                FROM cbot_tokens
                WHERE device_id=?
                ORDER BY id DESC
                LIMIT 1
                """,
                (did,),
            ).fetchone()

            if latest:

                db.execute(
                    """
                    UPDATE cbot_tokens
                    SET tamper_detected=1
                    WHERE id=?
                    """,
                    (latest["id"],),
                )

                event(
                    db,
                    did,
                    "CRITICAL",
                    "CBOT_TAMPERING",
                    "Unknown CBOT presented for a device with an issued token",
                )

                db.execute(
                    """
                    UPDATE devices
                    SET state=?,
                        quarantined_reason=?
                    WHERE device_id=?
                    """,
                    (
                        "QUARANTINED",
                        "CBOT tampering",
                        did,
                    ),
                )

                db.commit()

                raise HTTPException(
                    status_code=403,
                    detail="CBOT verification failed",
                )

            raise HTTPException(
                status_code=400,
                detail="Invalid or tampered CBOT",
            )

        if row["consumed"]:

            db.execute(
                """
                UPDATE cbot_tokens
                SET replay_detected=1
                WHERE id=?
                """,
                (row["id"],),
            )

            event(
                db,
                did,
                "CRITICAL",
                "CBOT_REPLAY",
                "Previously consumed CBOT replayed",
            )

            db.execute(
                """
                UPDATE devices
                SET state=?,
                    quarantined_reason=?
                WHERE device_id=?
                """,
                (
                    "QUARANTINED",
                    "CBOT replay",
                    did,
                ),
            )

            db.commit()

            raise HTTPException(
                status_code=409,
                detail="CBOT replay detected",
            )

        if now() > parse_ts(
            row["expires_at"]
        ):
            raise HTTPException(
                status_code=400,
                detail="CBOT expired",
            )

        expected = cbot_hmac(
            device_id=did,
            firmware_hash=row["firmware_hash"],
            device_nonce=row["device_nonce"],
            gateway_nonce=row["gateway_nonce"],
            network_id=row["network_id"],
            context_id=row["context_id"],
            timestamp=row["issued_at"],
        )

        if not hmac.compare_digest(
            expected,
            x.token,
        ):

            db.execute(
                """
                UPDATE cbot_tokens
                SET tamper_detected=1
                WHERE id=?
                """,
                (row["id"],),
            )

            event(
                db,
                did,
                "CRITICAL",
                "CBOT_TAMPERING",
                "CBOT tampering detected",
            )

            db.execute(
                """
                UPDATE devices
                SET state=?,
                    quarantined_reason=?
                WHERE device_id=?
                """,
                (
                    "QUARANTINED",
                    "CBOT tampering",
                    did,
                ),
            )

            db.commit()

            raise HTTPException(
                status_code=403,
                detail="CBOT verification failed",
            )

        db.execute(
            """
            UPDATE cbot_tokens
            SET consumed=1
            WHERE id=?
            """,
            (row["id"],),
        )

        session = latest_session(
            db,
            did,
        )

        db.execute(
            """
            UPDATE onboarding_sessions
            SET cbot_verified=1
            WHERE id=?
            """,
            (session["id"],),
        )

        transition(
            db,
            did,
            "CBOT_VERIFIED",
        )

        return {
            "verified": True,
            "state": "CBOT_VERIFIED",
        }


# ============================================================
# ONBOARD DEVICE
# ============================================================

@app.post("/devices/{did}/onboard")
def onboard(did: str):

    with get_db() as db:

        device_data = device_or_404(
            db,
            did,
        )

        session = latest_session(
            db,
            did,
        )

        if (
            not session
            or not all(
                [
                    session["identity_verified"],
                    session["firmware_verified"],
                    session["context_verified"],
                    session["cbot_verified"],
                ]
            )
        ):
            raise HTTPException(
                status_code=409,
                detail="All onboarding stages must be verified",
            )

        transition(
            db,
            did,
            "PROBATION",
        )

        db.execute(
            """
            UPDATE onboarding_sessions
            SET completed_at=?
            WHERE id=?
            """,
            (
                iso(now()),
                session["id"],
            ),
        )

        return {
            "state": "PROBATION",
            "message": "Device admitted to restricted probation",
        }


# ============================================================
# ONBOARDING DETAILS
# ============================================================

@app.get("/devices/{did}/onboarding")
def onboarding(did: str):

    with get_db() as db:

        device_or_404(
            db,
            did,
        )

        session = latest_session(
            db,
            did,
        )

        return (
            dict(session)
            if session
            else {}
        )


# ============================================================
# TELEMETRY
# ============================================================

@app.post("/devices/{did}/telemetry")
def telemetry(
    did: str,
    x: TelemetryIn,
):

    with get_db() as db:

        device_data = device_or_404(
            db,
            did,
        )

        cursor = db.execute(
            """
            INSERT INTO telemetry(
                device_id,
                timestamp,
                packet_rate,
                communication_frequency,
                destination,
                port,
                protocol,
                connection_success,
                scanning,
                lateral_movement
            )
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                did,
                iso(now()),
                x.packet_rate,
                x.communication_frequency,
                x.destination,
                x.port,
                x.protocol,
                x.connection_success,
                int(x.scanning),
                int(x.lateral_movement),
            ),
        )

        if x.scanning:
            event(
                db,
                did,
                "CRITICAL",
                "NETWORK_SCANNING",
                "Simulated scanning telemetry detected",
            )

        if x.lateral_movement:
            event(
                db,
                did,
                "CRITICAL",
                "LATERAL_MOVEMENT",
                "Simulated lateral movement telemetry detected",
            )

        return {
            "telemetry_id": cursor.lastrowid,
            "accepted": True,
            "state": device_data["state"],
        }


# ============================================================
# BEHAVIOR EVALUATION
# ============================================================

@app.post("/devices/{did}/evaluate-behavior")
def eval_behavior(did: str):

    with get_db() as db:

        device_data = device_or_404(
            db,
            did,
        )

        telemetry_row = db.execute(
            """
            SELECT *
            FROM telemetry
            WHERE device_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (did,),
        ).fetchone()

        if not telemetry_row:
            raise HTTPException(
                status_code=400,
                detail="No telemetry available",
            )

        if device_data["state"] not in (
            "PROBATION",
            "SUSPICIOUS",
            "TRUSTED",
        ):
            raise HTTPException(
                status_code=409,
                detail="Behavior evaluation unavailable in current state",
            )

        return evaluate(
            db,
            did,
            telemetry_row,
        )


# ============================================================
# TRUST
# ============================================================

@app.get("/devices/{did}/trust")
def trust(did: str):

    with get_db() as db:

        device_or_404(
            db,
            did,
        )

        row = db.execute(
            """
            SELECT *
            FROM trust_scores
            WHERE device_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (did,),
        ).fetchone()

        if row:
            return dict(row)

        return {
            "message": "No trust evaluation yet"
        }


# ============================================================
# TRUST HISTORY
# ============================================================

@app.get("/devices/{did}/trust-history")
def trust_history(did: str):

    with get_db() as db:

        device_or_404(
            db,
            did,
        )

        return [
            dict(row)
            for row in db.execute(
                """
                SELECT *
                FROM trust_scores
                WHERE device_id=?
                ORDER BY id
                """,
                (did,),
            )
        ]


# ============================================================
# SECURITY EVENTS
# ============================================================

@app.get("/security-events")
def events(
    device_id: str | None = None,
):

    with get_db() as db:

        query = """
            SELECT *
            FROM security_events
        """

        args = ()

        if device_id:

            query += """
                WHERE device_id=?
            """

            args = (
                device_id,
            )

        query += """
            ORDER BY id DESC
            LIMIT 200
        """

        return [
            dict(row)
            for row in db.execute(
                query,
                args,
            )
        ]


# ============================================================
# ATTACK LAB
# ============================================================

@app.post("/attack-lab/simulate")
def attack_lab(
    x: AttackSim,
):

    with get_db() as db:

        device_data = device_or_404(
            db,
            x.device_id,
        )

        # ----------------------------------------------------
        # Rogue device / cloned device / stolen credential
        # ----------------------------------------------------

        if x.attack_type in (
            "rogue_device",
            "cloned_device",
            "stolen_credential",
        ):

            event(
                db,
                x.device_id,
                "HIGH",
                x.attack_type.upper(),
                "Safe simulation: identity/credential threat",
                {
                    "simulation": True,
                },
            )

            return {
                "simulation": x.attack_type,
                "detected": True,
                "state": device_data["state"],
            }

        # ----------------------------------------------------
        # CBOT replay
        # ----------------------------------------------------

        if x.attack_type == "cbot_replay":

            row = db.execute(
                """
                SELECT token
                FROM cbot_tokens
                WHERE device_id=?
                ORDER BY id DESC
                LIMIT 1
                """,
                (x.device_id,),
            ).fetchone()

            if not row:

                raise HTTPException(
                    status_code=400,
                    detail="Generate a CBOT first",
                )

            try:

                verify_cbot(
                    x.device_id,
                    CbotVerify(
                        token=row["token"]
                    ),
                )

            except HTTPException as exc:

                return {
                    "simulation": x.attack_type,
                    "detected": True,
                    "status_code": exc.status_code,
                    "state": "QUARANTINED",
                }

        # ----------------------------------------------------
        # CBOT tampering / firmware tampering / context mismatch
        # ----------------------------------------------------

        if x.attack_type in (
            "cbot_tampering",
            "firmware_tampering",
            "context_mismatch",
        ):

            event_type = {
                "cbot_tampering": "CBOT_TAMPERING",
                "firmware_tampering": "FIRMWARE_INTEGRITY_FAILURE",
                "context_mismatch": "CONTEXT_MISMATCH",
            }[x.attack_type]

            event(
                db,
                x.device_id,
                "CRITICAL",
                event_type,
                f"Safe simulation: {x.attack_type}",
                {
                    "simulation": True,
                },
            )

            db.execute(
                """
                UPDATE devices
                SET state=?,
                    quarantined_reason=?
                WHERE device_id=?
                """,
                (
                    "QUARANTINED",
                    x.attack_type,
                    device_data["device_id"],
                ),
            )

            return {
                "simulation": x.attack_type,
                "detected": True,
                "state": "QUARANTINED",
            }

        # ----------------------------------------------------
        # Network scanning / lateral movement /
        # compromised legitimate device
        # ----------------------------------------------------

        if x.attack_type in (
            "network_scanning",
            "lateral_movement",
            "compromised_legitimate_device",
        ):

            values = {
                "network_scanning": (
                    100,
                    100,
                    "UNKNOWN",
                    445,
                    "TCP",
                    0.2,
                    True,
                    False,
                ),
                "lateral_movement": (
                    40,
                    40,
                    "UNKNOWN",
                    445,
                    "TCP",
                    0.2,
                    False,
                    True,
                ),
                "compromised_legitimate_device": (
                    30,
                    30,
                    "UNKNOWN",
                    4444,
                    "TCP",
                    0.4,
                    False,
                    False,
                ),
            }[x.attack_type]

            cursor = db.execute(
                """
                INSERT INTO telemetry(
                    device_id,
                    timestamp,
                    packet_rate,
                    communication_frequency,
                    destination,
                    port,
                    protocol,
                    connection_success,
                    scanning,
                    lateral_movement
                )
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    device_data["device_id"],
                    iso(now()),
                    *values,
                ),
            )

            telemetry_row = db.execute(
                """
                SELECT *
                FROM telemetry
                WHERE id=?
                """,
                (cursor.lastrowid,),
            ).fetchone()

            result = evaluate(
                db,
                device_data["device_id"],
                telemetry_row,
            )

            event(
                db,
                device_data["device_id"],
                "CRITICAL"
                if result["final_state"] == "QUARANTINED"
                else "HIGH",
                "ATTACK_LAB",
                f"Safe simulation: {x.attack_type}",
                {
                    "result": result,
                },
            )

            return {
                "simulation": x.attack_type,
                "detected": True,
                **result,
            }


# ============================================================
# ATTACK LAB HISTORY
# ============================================================

@app.get("/attack-lab/history")
def attack_history():

    with get_db() as db:

        return [
            dict(row)
            for row in db.execute(
                """
                SELECT *
                FROM security_events
                WHERE event_type='ATTACK_LAB'
                ORDER BY id DESC
                """
            )
        ]


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@app.get("/dashboard/summary")
def summary():

    with get_db() as db:

        states = {
            state: db.execute(
                """
                SELECT COUNT(*)
                FROM devices
                WHERE state=?
                """,
                (state,),
            ).fetchone()[0]
            for state in STATES
        }

        recent_events = db.execute(
            """
            SELECT *
            FROM security_events
            ORDER BY id DESC
            LIMIT 10
            """
        ).fetchall()

        scores = db.execute(
            """
            SELECT
                final_state,
                COUNT(*) c
            FROM trust_scores
            GROUP BY final_state
            """
        ).fetchall()

        return {
            "total_devices": sum(
                states.values()
            ),
            "states": states,
            "recent_events": [
                dict(row)
                for row in recent_events
            ],
            "trust_distribution": [
                dict(row)
                for row in scores
            ],
        }