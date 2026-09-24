from datetime import datetime, timedelta, timezone
import hashlib, hmac, secrets
from jose import JWTError, jwt
from fastapi import Request
from .config import settings

ALGORITHM = 'HS256'
COOKIE_NAME = 'pocketsmart_token'

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 210_000)
    return f'{salt.hex()}${digest.hex()}'

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split('$', 1)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), 210_000)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False

def create_token(username: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({'sub': username, 'exp': exp}, settings.secret_key, algorithm=ALGORITHM)

def get_username(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get('sub')
    except JWTError:
        return None
