import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-troque-isso")
JWT_ALGO = "HS256"
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "12"))

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd.verify(password, password_hash)


def create_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return {"user_id": int(data["sub"]), "role": data["role"]}
    except (JWTError, KeyError, ValueError):
        return None
