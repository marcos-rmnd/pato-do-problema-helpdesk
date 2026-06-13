import os
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException

import auth
import database as db
import notify
from config import (
    ALLOWED_ROLES,
    PUBLIC_TECH_REGISTRATION,
    TECH_ROLES,
)


def clean_text(value: str, field: str, min_len: int = 1, max_len: int = 5000) -> str:
    text = (value or "").strip()
    if len(text) < min_len:
        raise HTTPException(400, f"{field} precisa ter ao menos {min_len} caracteres.")
    if len(text) > max_len:
        raise HTTPException(400, f"{field} excede {max_len} caracteres.")
    return text


def normalize_email(value: str) -> str:
    email = (value or "").strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Informe um e-mail válido.")
    return email


def validate_password(password: str) -> str:
    password = password or ""
    if len(password) < 8:
        raise HTTPException(400, "A senha precisa ter pelo menos 8 caracteres.")
    return password


def validate_role(role: str, public_signup: bool = False) -> str:
    role = (role or "cliente").strip()
    if role not in ALLOWED_ROLES:
        raise HTTPException(400, "Tipo de conta inválido.")
    if public_signup and role in TECH_ROLES and not PUBLIC_TECH_REGISTRATION:
        return "cliente"
    return role


def validate_choice(value: str, allowed: tuple[str, ...], field: str) -> str:
    value = (value or "").strip()
    if value not in allowed:
        raise HTTPException(400, f"{field} inválido.")
    return value


def safe_filename(name: str) -> str:
    base = os.path.basename(name or "arquivo")
    safe = "".join(ch for ch in base if ch.isalnum() or ch in (".", "-", "_", " ")).strip()
    return safe[:120] or "arquivo"


def current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token ausente")
    data = auth.decode_token(authorization.split(" ", 1)[1])
    if not data:
        raise HTTPException(401, "Token inválido")
    return data


def require_tech(user=Depends(current_user)):
    if user["role"] not in TECH_ROLES:
        raise HTTPException(403, "Acesso restrito a técnicos")
    return user


def assert_tech_can_handle(ticket: dict, user: dict):
    if user["role"] in TECH_ROLES and ticket.get("level") != user["role"]:
        raise HTTPException(403, "Chamado fora da sua fila atual")


def add_event(conn, ticket_id, kind, author, content):
    db.execute(
        conn,
        "INSERT INTO events (ticket_id,kind,author,content,created_at) VALUES (?,?,?,?,?)",
        (ticket_id, kind, author, content, db.now()),
    )


def ticket_for_user(conn, tid, user, *, enforce_queue: bool = False):
    row = db.fetchone(conn, "SELECT * FROM tickets WHERE id=?", (tid,))
    if not row:
        raise HTTPException(404, "Chamado não encontrado")
    if user["role"] == "cliente" and row["client_id"] != user["user_id"]:
        raise HTTPException(403, "Sem acesso")
    if enforce_queue:
        assert_tech_can_handle(row, user)
    return row


def status_bucket(status):
    if status in ("Resolvido", "Encerrado"):
        return "resolvido"
    if status in ("Aguardando cliente", "Aguardando terceiro"):
        return "aguardando"
    if status in ("Em atendimento", "Em análise"):
        return "andamento"
    return "aberto"


def sla_state(ticket):
    priority_hours = {"Crítica": 4, "Alta": 8, "Média": 24, "Baixa": 72}
    if ticket.get("status") in ("Resolvido", "Encerrado"):
        return {"label": "Encerrado", "state": "ok", "hours_left": 0}
    hours = priority_hours.get(ticket.get("priority"), 24)
    try:
        created = datetime.fromisoformat(ticket["created_at"])
        elapsed = (datetime.now(timezone.utc).replace(tzinfo=None) - created).total_seconds() / 3600
        left = round(hours - elapsed, 1)
    except Exception:
        left = hours
    if left < 0:
        return {"label": "Atrasado", "state": "late", "hours_left": left}
    if left <= max(2, hours * 0.25):
        return {"label": "Atenção", "state": "warn", "hours_left": left}
    return {"label": "No prazo", "state": "ok", "hours_left": left}


def enrich_ticket(ticket):
    ticket["status_bucket"] = status_bucket(ticket.get("status"))
    ticket["sla"] = sla_state(ticket)
    return ticket


def notify_client(conn, ticket, message):
    cli = db.fetchone(conn, "SELECT name,email FROM users WHERE id=?", (ticket["client_id"],))
    email = cli["email"] if cli else ""
    status = notify.notify(
        channel=ticket.get("channel", "Chat"),
        frequency=ticket.get("frequency", ""),
        to_email=email,
        to_phone="",
        ticket_code=ticket["code"],
        message=message,
    )
    add_event(conn, ticket["id"], "system", "Sistema", status)


def next_code(conn):
    row = db.fetchone(conn, "SELECT COUNT(*) AS n FROM tickets")
    return f"#{row['n']+1:04d}"
