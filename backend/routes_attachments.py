import base64

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

import database as db
from config import ALLOWED_ATTACHMENT_TYPES, MAX_FILE, TECH_ROLES
from helpers import add_event, current_user, safe_filename, ticket_for_user

router = APIRouter()


@router.post("/api/tickets/{tid}/attachments")
async def upload_attachment(tid: int, file: UploadFile = File(...), user=Depends(current_user)):
    filename = safe_filename(file.filename)
    mimetype = file.content_type or "application/octet-stream"
    if mimetype not in ALLOWED_ATTACHMENT_TYPES:
        raise HTTPException(400, "Tipo de arquivo não permitido. Envie imagem, PDF, TXT, DOCX ou XLSX.")

    raw = await file.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise HTTPException(400, f"Arquivo excede {MAX_FILE // (1024 * 1024)} MB")

    conn = db.get_conn()
    ticket_for_user(conn, tid, user, enforce_queue=user["role"] in TECH_ROLES)
    b64 = base64.b64encode(raw).decode()
    autor = "Cliente" if user["role"] == "cliente" else f"Suporte {user['role']}"
    db.execute(
        conn,
        "INSERT INTO attachments (ticket_id,filename,mimetype,size,data,uploaded_by,created_at) VALUES (?,?,?,?,?,?,?)",
        (tid, filename, mimetype, len(raw), b64, autor, db.now()),
    )
    add_event(conn, tid, "attachment", autor, f"Anexou: {filename}")
    conn.commit()
    conn.close()
    return {"ok": True, "filename": filename}


@router.get("/api/tickets/{tid}/attachments")
def list_attachments(tid: int, user=Depends(current_user)):
    conn = db.get_conn()
    ticket_for_user(conn, tid, user, enforce_queue=user["role"] in TECH_ROLES)
    rows = db.fetchall(
        conn,
        "SELECT id,filename,mimetype,size,uploaded_by,created_at FROM attachments WHERE ticket_id=? ORDER BY id",
        (tid,),
    )
    conn.close()
    return rows


@router.get("/api/attachments/{aid}")
def download_attachment(aid: int, user=Depends(current_user)):
    conn = db.get_conn()
    attachment = db.fetchone(conn, "SELECT * FROM attachments WHERE id=?", (aid,))
    if attachment:
        ticket_for_user(conn, attachment["ticket_id"], user, enforce_queue=user["role"] in TECH_ROLES)
    conn.close()
    if not attachment:
        raise HTTPException(404, "Anexo não encontrado")
    data = base64.b64decode(attachment["data"])
    filename = safe_filename(attachment["filename"])
    return Response(
        content=data,
        media_type=attachment["mimetype"] or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
