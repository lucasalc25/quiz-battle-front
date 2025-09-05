import os
from fastapi import HTTPException, Header

DEV_MODE = os.getenv("DEV_MODE", "true").lower() in {"1", "true", "yes"}

# Lazy import to avoid firebase dependency in dev bypass
_firebase_ready = False
def _ensure_firebase():
    global _firebase_ready
    if _firebase_ready:
        return
    import firebase_admin
    from firebase_admin import credentials
    if not firebase_admin._apps:
        cred_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if cred_json:
            # Expect a JSON string
            import json
            cred = credentials.Certificate(json.loads(cred_json))
        else:
            # Try ADC if set in the environment
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    _firebase_ready = True

def require_user(authorization: str | None = Header(default=None)):
    """Return (uid, email, name). In DEV_MODE, returns a fake user."""
    if DEV_MODE:
        return ("dev-uid", "dev@example.com", "Dev User")
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    try:
        _ensure_firebase()
        from firebase_admin import auth
        decoded = auth.verify_id_token(token)
        return (decoded.get("uid"), decoded.get("email"), decoded.get("name") or "Player")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
