import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

import auth
import database as db
import notify
from config import ALLOW_DEV_RESET_TOKEN
from helpers import validate_password
from schemas import ForgotIn, ResetIn

router = APIRouter()


@router.post("/api/forgot")
def forgot(data: ForgotIn):
    conn = db.get_conn()
    user = db.fetchone(conn, "SELECT id,email FROM users WHERE email=?", (data.email.lower(),))
    if user:
        token = secrets.token_urlsafe(24)
        expires_at = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)).isoformat()
        db.execute(
            conn,
            "INSERT INTO reset_tokens (user_id,token,expires_at,used) VALUES (?,?,?,0)",
            (user["id"], token, expires_at),
        )
        conn.commit()
        link = f"redefinir.html?token={token}"
        sent = notify._send_email(
            user["email"],
            "Redefinicao de senha - pato.do.problema",
            f"Para redefinir sua senha, acesse: {link}",
        )
        conn.close()
        if not sent and ALLOW_DEV_RESET_TOKEN:
            return {"ok": True, "dev_token": token, "msg": "SMTP não configurado · use o dev_token para testar a redefinição."}
    else:
        conn.close()
    return {"ok": True, "msg": "Se o e-mail existir, enviaremos instruções."}


@router.post("/api/reset")
def reset(data: ResetIn):
    password = validate_password(data.password)
    conn = db.get_conn()
    token = db.fetchone(conn, "SELECT * FROM reset_tokens WHERE token=? AND used=0", (data.token,))
    if not token or token["expires_at"] < datetime.now(timezone.utc).replace(tzinfo=None).isoformat():
        conn.close()
        raise HTTPException(400, "Token inválido ou expirado")
    db.execute(conn, "UPDATE users SET password_hash=? WHERE id=?", (auth.hash_password(password), token["user_id"]))
    db.execute(conn, "UPDATE reset_tokens SET used=1 WHERE id=?", (token["id"],))
    conn.commit()
    conn.close()
    return {"ok": True}
