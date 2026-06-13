from fastapi import APIRouter, Depends, HTTPException

import ai
import database as db
from config import ALLOWED_CHANNELS, ALLOWED_FREQUENCIES, ALLOWED_STATUSES, NEXT_LEVEL, TECH_ROLES
from helpers import (
    add_event,
    clean_text,
    current_user,
    enrich_ticket,
    notify_client,
    next_code,
    require_tech,
    ticket_for_user,
    validate_choice,
)
from schemas import EscalateIn, HumanizeIn, MessageIn, StatusIn, TicketIn

router = APIRouter()


@router.post("/api/tickets")
def create_ticket(data: TicketIn, user=Depends(current_user)):
    title = clean_text(data.title, "Título", 3, 160)
    description = clean_text(data.description, "Descrição", 8, 5000)
    priority = validate_choice(data.priority, ("Baixa", "Média", "Alta", "Crítica"), "Prioridade")
    channel = validate_choice(data.channel, ALLOWED_CHANNELS, "Canal")
    frequency = validate_choice(data.frequency, ALLOWED_FREQUENCIES, "Frequência")

    level = "N1"

    conn = db.get_conn()
    code = next_code(conn)
    tid = db.insert_returning_id(
        conn,
        """INSERT INTO tickets
           (code,client_id,title,description,category,priority,ai_summary,status,level,channel,frequency,eta,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            code,
            user["user_id"],
            title,
            description,
            "Geral",
            priority,
            title[:240],
            "Aberto",
            level,
            channel,
            frequency,
            "a definir",
            db.now(),
            db.now(),
        ),
    )
    add_event(conn, tid, "status", "Sistema", "Chamado aberto")
    add_event(
        conn,
        tid,
        "system",
        "Triagem",
        f"Prioridade escolhida: {priority} · fila: {level}",
    )
    add_event(conn, tid, "status", "Sistema", "Em análise")
    conn.commit()
    row = db.fetchone(conn, "SELECT * FROM tickets WHERE id=?", (tid,))
    conn.close()
    return enrich_ticket(row)


@router.get("/api/tickets")
def my_tickets(user=Depends(current_user)):
    conn = db.get_conn()
    rows = db.fetchall(conn, "SELECT * FROM tickets WHERE client_id=? ORDER BY id DESC", (user["user_id"],))
    conn.close()
    return [enrich_ticket(r) for r in rows]


@router.get("/api/tickets/{tid}")
def get_ticket(tid: int, user=Depends(current_user)):
    conn = db.get_conn()
    row = ticket_for_user(conn, tid, user, enforce_queue=user["role"] in TECH_ROLES)
    client = db.fetchone(conn, "SELECT name,email FROM users WHERE id=?", (row["client_id"],))
    row["events"] = db.fetchall(conn, "SELECT * FROM events WHERE ticket_id=? ORDER BY id", (tid,))
    row["client"] = client or {}
    conn.close()
    return enrich_ticket(row)


@router.post("/api/tickets/{tid}/message")
def post_message(tid: int, data: MessageIn, user=Depends(current_user)):
    content = clean_text(data.content, "Mensagem", 1, 3000)
    conn = db.get_conn()
    ticket_for_user(conn, tid, user, enforce_queue=user["role"] in TECH_ROLES)
    author = "Cliente" if user["role"] == "cliente" else f"Suporte {user['role']}"
    add_event(conn, tid, "message", author, content)
    db.execute(conn, "UPDATE tickets SET updated_at=? WHERE id=?", (db.now(), tid))
    conn.commit()
    conn.close()
    return {"ok": True}



@router.get("/api/queue")
def queue(user=Depends(require_tech)):
    conn = db.get_conn()
    rows = db.fetchall(
        conn,
        "SELECT * FROM tickets WHERE level=? AND status NOT IN ('Encerrado') ORDER BY "
        "CASE priority WHEN 'Crítica' THEN 0 WHEN 'Alta' THEN 1 WHEN 'Média' THEN 2 ELSE 3 END, id DESC",
        (user["role"],),
    )
    conn.close()
    return [enrich_ticket(r) for r in rows]


@router.post("/api/tickets/{tid}/internal")
def internal_note(tid: int, data: MessageIn, user=Depends(require_tech)):
    if not data.content.strip():
        raise HTTPException(400, "Escreva uma nota interna.")
    conn = db.get_conn()
    ticket_for_user(conn, tid, user, enforce_queue=True)
    add_event(conn, tid, "internal", f"Suporte {user['role']}", data.content.strip())
    db.execute(conn, "UPDATE tickets SET updated_at=? WHERE id=?", (db.now(), tid))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/api/tickets/{tid}/status")
def set_status(tid: int, data: StatusIn, user=Depends(require_tech)):
    status = validate_choice(data.status, ALLOWED_STATUSES, "Status")
    conn = db.get_conn()
    ticket = ticket_for_user(conn, tid, user, enforce_queue=True)
    db.execute(conn, "UPDATE tickets SET status=?, updated_at=? WHERE id=?", (status, db.now(), tid))
    add_event(conn, tid, "status", f"Suporte {user['role']}", f"Status alterado para: {status}")
    ticket = db.fetchone(conn, "SELECT * FROM tickets WHERE id=?", (tid,))
    notify_client(conn, ticket, f"Seu chamado {ticket['code']} mudou para: {status}")
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/api/tickets/{tid}/escalate")
async def escalate(tid: int, data: EscalateIn, user=Depends(require_tech)):
    next_level = NEXT_LEVEL[user["role"]]
    if not next_level or data.level != next_level:
        raise HTTPException(400, "Escalonamento inválido para este nível de suporte.")

    conn = db.get_conn()
    row = ticket_for_user(conn, tid, user, enforce_queue=True)
    events = db.fetchall(conn, "SELECT * FROM events WHERE ticket_id=? ORDER BY id", (tid,))
    resumo = await ai.summarize(events)
    db.execute(conn, "UPDATE tickets SET level=?, ai_summary=?, updated_at=? WHERE id=?", (next_level, resumo, db.now(), tid))
    add_event(conn, tid, "escalation", f"Suporte {user['role']}", f"Escalado de {row['level']} para {next_level}")
    add_event(conn, tid, "system", "Triagem", f"Resumo para {next_level}: {resumo}")
    conn.commit()
    conn.close()
    return {"ok": True, "resumo": resumo}


@router.post("/api/tickets/{tid}/suggest")
async def suggest(tid: int, user=Depends(require_tech)):
    conn = db.get_conn()
    row = ticket_for_user(conn, tid, user, enforce_queue=True)
    events = db.fetchall(conn, "SELECT * FROM events WHERE ticket_id=? ORDER BY id", (tid,))
    conn.close()
    txt = await ai.suggest_reply(row, events)
    return {"suggestion": txt}


@router.post("/api/tickets/{tid}/close")
def close_ticket(tid: int, user=Depends(current_user)):
    conn = db.get_conn()
    row = db.fetchone(conn, "SELECT * FROM tickets WHERE id=?", (tid,))
    if not row:
        conn.close()
        raise HTTPException(404, "Não encontrado")
    if user["role"] == "cliente" and row["client_id"] != user["user_id"]:
        conn.close()
        raise HTTPException(403, "Sem acesso")
    if user["role"] in TECH_ROLES and row["level"] != user["role"]:
        conn.close()
        raise HTTPException(403, "Chamado fora da sua fila atual")
    db.execute(conn, "UPDATE tickets SET status='Encerrado', updated_at=? WHERE id=?", (db.now(), tid))
    autor = "Cliente" if user["role"] == "cliente" else f"Suporte {user['role']}"
    add_event(conn, tid, "status", autor, "Chamado encerrado")
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/api/humanize")
async def humanize(data: HumanizeIn, user=Depends(require_tech)):
    return {"text": await ai.humanize(data.text)}
