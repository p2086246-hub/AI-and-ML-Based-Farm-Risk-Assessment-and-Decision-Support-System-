import base64
import hashlib
import hmac
import json
import os
import time
import sqlite3
from fastapi import Depends, Header, HTTPException
from app.core.config import settings
from app.db.session import get_db

ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"{ITERATIONS}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        it, salt_b64, digest_b64 = stored.split("$", 2)
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(it))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign_payload(payload: dict) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64(hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def _decode_signed(token: str) -> dict:
    try:
        body, sig = token.split(".", 1)
        expected = _b64(hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        payload = json.loads(_unb64(body))
        if payload.get("exp", 0) < time.time():
            raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def create_token(user_id: int) -> str:
    return _sign_payload({"kind": "access", "sub": user_id, "exp": int(time.time()) + settings.access_token_hours * 3600})


def decode_token(token: str) -> int:
    payload = _decode_signed(token)
    if payload.get("kind") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")
    return int(payload["sub"])


def create_verification_token(mobile_no: str, purpose: str) -> str:
    return _sign_payload({"kind": "otp-verification", "mobile_no": mobile_no, "purpose": purpose, "exp": int(time.time()) + settings.verification_token_minutes * 60})


def verify_verification_token(token: str, mobile_no: str, purpose: str) -> None:
    payload = _decode_signed(token)
    if payload.get("kind") != "otp-verification" or payload.get("mobile_no") != mobile_no or payload.get("purpose") != purpose:
        raise HTTPException(status_code=401, detail="Verification token does not match this request")


def hash_otp(mobile_no: str, purpose: str, otp: str) -> str:
    raw = f"{mobile_no}|{purpose}|{otp}|{settings.secret_key}".encode()
    return hashlib.sha256(raw).hexdigest()


def get_current_user(authorization: str | None = Header(default=None), db: sqlite3.Connection = Depends(get_db)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    user_id = decode_token(authorization.split(" ", 1)[1])
    row = db.execute("SELECT id,name,mobile_no,preferred_language FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(row)
