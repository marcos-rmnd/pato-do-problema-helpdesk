from fastapi import APIRouter, Depends, HTTPException

import auth
import database as db
from helpers import current_user, clean_text, normalize_email, validate_password, validate_role
from schemas import LoginIn, ProfileIn, RegisterIn

router = APIRouter()


@router.post("/api/register")
def register(data: RegisterIn):
    name = clean_text(data.name, "Nome", 2, 120)
    email = normalize_email(data.email)
    password = validate_password(data.password)
    role = validate_role(data.role, public_signup=True)

    conn = db.get_conn()
    try:
        uid = db.insert_returning_id(
            conn,
            "INSERT INTO users (name,email,password_hash,role,created_at) VALUES (?,?,?,?,?)",
            (name, email, auth.hash_password(password), role, db.now()),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(400, "E-mail já cadastrado")
    finally:
        conn.close()
    return {"token": auth.create_token(uid, role), "role": role, "name": name}


@router.post("/api/login")
def login(data: LoginIn):
    email = normalize_email(data.email)
    conn = db.get_conn()
    row = db.fetchone(conn, "SELECT * FROM users WHERE email=?", (email,))
    conn.close()
    if not row or not auth.verify_password(data.password, row["password_hash"]):
        raise HTTPException(401, "Credenciais inválidas")
    return {"token": auth.create_token(row["id"], row["role"]), "role": row["role"], "name": row["name"]}


@router.get("/api/me")
def me(user=Depends(current_user)):
    conn = db.get_conn()
    row = db.fetchone(conn, "SELECT id,name,email,role FROM users WHERE id=?", (user["user_id"],))
    conn.close()
    return row or {}


@router.put("/api/me")
def update_me(data: ProfileIn, user=Depends(current_user)):
    name = clean_text(data.name, "Nome", 2, 120)
    conn = db.get_conn()
    db.execute(conn, "UPDATE users SET name=? WHERE id=?", (name, user["user_id"]))
    conn.commit()
    row = db.fetchone(conn, "SELECT id,name,email,role FROM users WHERE id=?", (user["user_id"],))
    conn.close()
    return row or {}
