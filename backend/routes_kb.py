import json
import re

from fastapi import APIRouter, Depends, HTTPException

import ai
import database as db
from helpers import clean_text, require_tech
from schemas import KBArticleIn, KBSearchIn

router = APIRouter()


@router.get("/api/kb")
def kb_list(q: str = ""):
    conn = db.get_conn()
    if q:
        rows = db.fetchall(
            conn,
            "SELECT id,title,category,tags,views,created_at FROM kb_articles "
            "WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? ORDER BY views DESC",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        )
    else:
        rows = db.fetchall(conn, "SELECT id,title,category,tags,views,created_at FROM kb_articles ORDER BY views DESC")
    conn.close()
    return rows


@router.get("/api/kb/{aid}")
def kb_get(aid: int):
    conn = db.get_conn()
    article = db.fetchone(conn, "SELECT * FROM kb_articles WHERE id=?", (aid,))
    if not article:
        conn.close()
        raise HTTPException(404, "Artigo não encontrado")
    db.execute(conn, "UPDATE kb_articles SET views=views+1 WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    return article


@router.post("/api/kb")
def kb_create(data: KBArticleIn, user=Depends(require_tech)):
    title = clean_text(data.title, "Título", 3, 180)
    content = clean_text(data.content, "Conteúdo", 10, 12000)
    category = clean_text(data.category, "Categoria", 2, 60)
    tags = (data.tags or "").strip()[:240]
    conn = db.get_conn()
    current = db.fetchone(conn, "SELECT name FROM users WHERE id=?", (user["user_id"],))
    author = current["name"] if current else "Técnico"
    aid = db.insert_returning_id(
        conn,
        "INSERT INTO kb_articles (title,content,category,tags,author,views,created_at,updated_at) VALUES (?,?,?,?,?,0,?,?)",
        (title, content, category, tags, author, db.now(), db.now()),
    )
    conn.commit()
    row = db.fetchone(conn, "SELECT * FROM kb_articles WHERE id=?", (aid,))
    conn.close()
    return row


@router.put("/api/kb/{aid}")
def kb_update(aid: int, data: KBArticleIn, user=Depends(require_tech)):
    title = clean_text(data.title, "Título", 3, 180)
    content = clean_text(data.content, "Conteúdo", 10, 12000)
    category = clean_text(data.category, "Categoria", 2, 60)
    tags = (data.tags or "").strip()[:240]
    conn = db.get_conn()
    if not db.fetchone(conn, "SELECT id FROM kb_articles WHERE id=?", (aid,)):
        conn.close()
        raise HTTPException(404, "Artigo não encontrado")
    db.execute(
        conn,
        "UPDATE kb_articles SET title=?,content=?,category=?,tags=?,updated_at=? WHERE id=?",
        (title, content, category, tags, db.now(), aid),
    )
    conn.commit()
    row = db.fetchone(conn, "SELECT * FROM kb_articles WHERE id=?", (aid,))
    conn.close()
    return row


@router.delete("/api/kb/{aid}")
def kb_delete(aid: int, user=Depends(require_tech)):
    conn = db.get_conn()
    db.execute(conn, "DELETE FROM kb_articles WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/api/kb/suggest")
async def kb_suggest(data: KBSearchIn):
    conn = db.get_conn()
    articles = db.fetchall(conn, "SELECT id,title,category,tags FROM kb_articles ORDER BY views DESC LIMIT 40")
    conn.close()
    if not articles:
        return {"suggestions": []}
    catalog = "\n".join(f"ID {a['id']}: {a['title']} [{a['category']}] tags:{a['tags']}" for a in articles)
    prompt = (
        f'O usuário descreveu: "{data.query}"\n\nArtigos disponíveis:\n{catalog}\n\n'
        'Retorne SOMENTE JSON com os IDs dos 3 mais relevantes: {"ids":[1,2,3]}'
    )
    try:
        raw = await ai._call_claude(prompt, 200)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        ids = json.loads(match.group(0)).get("ids", []) if match else []
        return {"suggestions": [a for a in articles if a["id"] in ids]}
    except Exception:
        words = data.query.lower().split()
        return {
            "suggestions": [
                a for a in articles
                if any(w in (a["title"] + a["tags"]).lower() for w in words)
            ][:3]
        }
