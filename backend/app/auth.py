import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import ADMIN_EMAIL, ADMIN_PASSWORD, SECRET_KEY, TOKEN_EXPIRE_MINUTES

bearer = HTTPBearer()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: str) -> str:
    digest = hmac.new(SECRET_KEY.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return _b64(digest)


def create_token(email: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": email, "exp": int(time.time()) + TOKEN_EXPIRE_MINUTES * 60}
    body = f"{_b64(json.dumps(header, separators=(',', ':')).encode())}.{_b64(json.dumps(payload, separators=(',', ':')).encode())}"
    return f"{body}.{_sign(body)}"


def verify_credentials(email: str, password: str) -> bool:
    return hmac.compare_digest(email, ADMIN_EMAIL) and hmac.compare_digest(password, ADMIN_PASSWORD)


def decode_token(token: str) -> dict[str, Any]:
    try:
        head, payload, signature = token.split(".")
        body = f"{head}.{payload}"
        if not hmac.compare_digest(signature, _sign(body)):
            raise ValueError("bad signature")
        data = json.loads(_unb64(payload))
        if int(data.get("exp", 0)) < int(time.time()):
            raise ValueError("expired")
        return data
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict[str, Any]:
    return decode_token(credentials.credentials)
