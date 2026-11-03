import secrets
import sqlite3
import time
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.security import (
    create_token, create_verification_token, get_current_user, hash_otp,
    hash_password, verify_password, verify_verification_token,
)
from app.db.session import get_db
from app.schemas.auth import LoginRequest, OTPRequest, OTPVerifyRequest, RegisterRequest, ResetPasswordRequest
from app.services.sms import send_otp_sms

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/request-otp")
async def request_otp(payload: OTPRequest, db: sqlite3.Connection = Depends(get_db)):
    user = db.execute("SELECT id FROM users WHERE mobile_no=?", (payload.mobile_no,)).fetchone()
    if not user:
        raise HTTPException(404, "No account found for this mobile number")
    now = int(time.time())
    latest = db.execute(
        "SELECT * FROM otp_codes WHERE mobile_no=? AND purpose='forgot_password' ORDER BY id DESC LIMIT 1",
        (payload.mobile_no,),
    ).fetchone()
    if latest and now - latest["created_at_unix"] < settings.otp_resend_seconds:
        wait_for = settings.otp_resend_seconds - (now - latest["created_at_unix"])
        raise HTTPException(429, f"Please wait {wait_for} seconds before requesting another OTP")
    otp = f"{secrets.randbelow(1_000_000):06d}"
    db.execute(
        "INSERT INTO otp_codes(mobile_no,purpose,code_hash,created_at_unix,expires_at_unix,used,attempts) VALUES(?,?,?,?,?,0,0)",
        (payload.mobile_no, "forgot_password", hash_otp(payload.mobile_no, "forgot_password", otp), now, now + settings.otp_expire_minutes * 60),
    )
    db.commit()
    try:
        delivery = await send_otp_sms(payload.mobile_no, otp, "forgot_password")
    except Exception as exc:
        raise HTTPException(502, f"Could not send OTP: {exc}")
    return {"ok": True, "delivery": delivery, "expires_in_seconds": settings.otp_expire_minutes * 60, "resend_after_seconds": settings.otp_resend_seconds}


@router.post("/verify-otp")
def verify_otp(payload: OTPVerifyRequest, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM otp_codes WHERE mobile_no=? AND purpose='forgot_password' AND used=0 ORDER BY id DESC LIMIT 1",
        (payload.mobile_no,),
    ).fetchone()
    if not row:
        raise HTTPException(400, "Request a new OTP first")
    if row["expires_at_unix"] < int(time.time()):
        db.execute("UPDATE otp_codes SET used=1 WHERE id=?", (row["id"],)); db.commit()
        raise HTTPException(400, "OTP has expired")
    if row["attempts"] >= 5:
        db.execute("UPDATE otp_codes SET used=1 WHERE id=?", (row["id"],)); db.commit()
        raise HTTPException(400, "Too many incorrect attempts. Request a new OTP")
    db.execute("UPDATE otp_codes SET attempts=attempts+1 WHERE id=?", (row["id"],)); db.commit()
    if row["code_hash"] != hash_otp(payload.mobile_no, "forgot_password", payload.otp):
        raise HTTPException(400, "Incorrect OTP")
    db.execute("UPDATE otp_codes SET used=1 WHERE id=?", (row["id"],)); db.commit()
    return {"verified": True, "verification_token": create_verification_token(payload.mobile_no, "forgot_password")}


@router.post("/register")
def register(payload: RegisterRequest, db: sqlite3.Connection = Depends(get_db)):
    if db.execute("SELECT id FROM users WHERE mobile_no=?", (payload.mobile_no,)).fetchone():
        raise HTTPException(409, "Mobile number already registered")
    cur = db.execute(
        "INSERT INTO users(name,mobile_no,password_hash,preferred_language) VALUES(?,?,?,?)",
        (payload.name.strip(), payload.mobile_no, hash_password(payload.password), payload.preferred_language),
    )
    db.commit(); uid = cur.lastrowid
    return {"token": create_token(uid), "user": {"id": uid, "name": payload.name.strip(), "mobile_no": payload.mobile_no, "preferred_language": payload.preferred_language}}


@router.post("/login")
def login(payload: LoginRequest, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM users WHERE mobile_no=?", (payload.mobile_no,)).fetchone()
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(401, "Invalid mobile number or password")
    return {"token": create_token(row["id"]), "user": {"id": row["id"], "name": row["name"], "mobile_no": row["mobile_no"], "preferred_language": row["preferred_language"]}}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: sqlite3.Connection = Depends(get_db)):
    verify_verification_token(payload.verification_token, payload.mobile_no, "forgot_password")
    row = db.execute("SELECT id FROM users WHERE mobile_no=?", (payload.mobile_no,)).fetchone()
    if not row:
        raise HTTPException(404, "Account not found")
    db.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(payload.new_password), row["id"])); db.commit()
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
