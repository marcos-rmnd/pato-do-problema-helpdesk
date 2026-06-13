from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import Response

import database as db
from helpers import require_tech, sla_state

router = APIRouter()


def csv_cell(value) -> str:
    text = str(value or "")
    if text.startswith(("=", "+", "-", "@")):
        text = "'" + text
    return '"' + text.replace('"', '""') + '"'


@router.get("/api/metrics")
def metrics(user=Depends(require_tech)):
    lvl = user["role"]
    conn = db.get_conn()

    # tudo da fila desse nível de uma vez
    tickets = db.fetchall(conn, "SELECT * FROM tickets WHERE level=?", (lvl,))

    por_status = {}
    por_prio = {}
    hoje = datetime.now(timezone.utc).date().isoformat()
    criados_hoje = 0
    atrasados = 0
    tempos = []

    for t in tickets:
        st = t["status"]
        por_status[st] = por_status.get(st, 0) + 1
        por_prio[t["priority"]] = por_prio.get(t["priority"], 0) + 1
        if t["created_at"].startswith(hoje):
            criados_hoje += 1
        resolvido = st in ("Resolvido", "Encerrado")
        if not resolvido and sla_state(t)["state"] == "late":
            atrasados += 1
        if resolvido:
            ev = db.fetchone(
                conn,
                "SELECT created_at FROM events WHERE ticket_id=? AND kind='status' ORDER BY id DESC LIMIT 1",
                (t["id"],),
            )
            if ev:
                try:
                    t0 = datetime.fromisoformat(t["created_at"])
                    t1 = datetime.fromisoformat(ev["created_at"])
                    tempos.append((t1 - t0).total_seconds() / 3600.0)
                except Exception:
                    pass

    # contagem global por nível (visão geral)
    por_nivel = {}
    for lv in ("N1", "N2", "N3"):
        por_nivel[lv] = db.fetchone(conn, "SELECT COUNT(*) AS n FROM tickets WHERE level=?", (lv,))["n"]
    conn.close()

    total = len(tickets)
    resolvidos = por_status.get("Resolvido", 0) + por_status.get("Encerrado", 0)
    abertos = total - resolvidos

    return {
        "total": total,
        "abertos": abertos,
        "resolvidos": resolvidos,
        "taxa_resolucao": round(resolvidos / total * 100) if total else 0,
        "por_nivel": por_nivel,
        "por_prioridade": {p: por_prio.get(p, 0) for p in ("Crítica", "Alta", "Média", "Baixa")},
        "por_status": {s: por_status.get(s, 0) for s in ("Aberto", "Em análise", "Em atendimento", "Aguardando cliente", "Aguardando terceiro", "Resolvido", "Encerrado")},
        "criados_hoje": criados_hoje,
        "aguardando_cliente": por_status.get("Aguardando cliente", 0),
        "criticos": por_prio.get("Crítica", 0),
        "atrasados": atrasados,
        "tempo_medio_resolucao_h": round(sum(tempos) / len(tempos), 1) if tempos else 0,
    }


@router.get("/api/export/tickets.csv")
def export_tickets(user=Depends(require_tech)):
    conn = db.get_conn()
    rows = db.fetchall(
        conn,
        """SELECT t.code,t.title,t.category,t.priority,t.status,t.level,t.channel,t.created_at,t.updated_at,u.name AS cliente
           FROM tickets t LEFT JOIN users u ON u.id=t.client_id ORDER BY t.id DESC""",
    )
    conn.close()
    header = ["codigo", "titulo", "cliente", "categoria", "prioridade", "status", "nivel", "canal", "criado_em", "atualizado_em"]
    lines = [";".join(header)]
    for r in rows:
        vals = [
            r["code"],
            r["title"],
            r.get("cliente") or "",
            r.get("category") or "",
            r.get("priority") or "",
            r.get("status") or "",
            r.get("level") or "",
            r.get("channel") or "",
            r.get("created_at") or "",
            r.get("updated_at") or "",
        ]
        lines.append(";".join(csv_cell(v) for v in vals))
    return Response(
        "\n".join(lines),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="chamados.csv"'},
    )
