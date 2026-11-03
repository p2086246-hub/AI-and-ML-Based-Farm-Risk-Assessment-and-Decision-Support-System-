import httpx
from app.core.config import settings


async def send_otp_sms(mobile_no: str, otp: str, purpose: str) -> str:
    purpose_text = "account verification" if purpose == "register" else "password reset"
    message = f"AgriTech OTP for {purpose_text}: {otp}. Valid for {settings.otp_expire_minutes} minutes. Do not share it."

    if settings.sms_mode.lower() == "twilio":
        if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_from_number):
            raise RuntimeError("Twilio SMS mode is enabled but credentials are missing")
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                url,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                data={"From": settings.twilio_from_number, "To": mobile_no, "Body": message},
            )
            response.raise_for_status()
        return "sms"

    # Safe local-development mode: never expose the OTP in the browser/UI.
    print("\n" + "=" * 68)
    print(f"AGRITECH DEVELOPMENT OTP -> {mobile_no}: {otp}")
    print("This appears only in the backend terminal because SMS_MODE=console.")
    print("=" * 68 + "\n")
    return "console"
