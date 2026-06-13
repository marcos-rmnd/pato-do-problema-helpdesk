import os
import re
try:
    import httpx
except ImportError:
    httpx = None

API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


async def _call_claude(prompt: str, max_tokens: int = 1000) -> str:
    if not API_KEY:
        raise RuntimeError("no-api-key")
    if httpx is None:
        raise RuntimeError("no-httpx")
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(API_URL, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        return "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        )



def _normalizar_resumo(texto: str) -> str:
    texto = (texto or "").strip()
    return re.sub(r'(?<!\.)\.\.(?!\.)', '.', texto)


async def summarize(events: list) -> str:
    linhas = "\n".join(f"- [{e['kind']}] {e['author']}: {e['content']}" for e in events)
    prompt = f"""Resuma este chamado para outro técnico assumir. No máximo 3 frases, direto ao ponto.

Histórico:
{linhas}
"""
    try:
        resumo = (await _call_claude(prompt, 400)).strip()
        return _normalizar_resumo(resumo)
    except Exception:
        msgs = [e for e in events if e["kind"] in ("message", "status", "escalation")]
        resumo = f"Chamado com {len(events)} eventos registrados. Último: {msgs[-1]['content'] if msgs else 'sem mensagens'}"
        return _normalizar_resumo(resumo)


async def suggest_reply(ticket: dict, events: list) -> str:
    linhas = "\n".join(f"- {e['author']}: {e['content']}" for e in events if e["kind"] == "message")
    prompt = f"""Escreva uma resposta curta e útil para o cliente. Não invente solução técnica que não esteja no histórico.

Chamado: {ticket['title']}
Descrição: {ticket['description']}
Conversa até agora:
{linhas or '(sem mensagens ainda)'}
"""
    try:
        return (await _call_claude(prompt, 500)).strip()
    except Exception:
        return ("Olá! Recebemos seu chamado e já estamos analisando. "
                "Em breve traremos uma atualização. Se puder, envie qualquer "
                "detalhe adicional que ajude a entender o problema.")


async def humanize(status_text: str) -> str:
    prompt = f"""Reescreva em linguagem simples para cliente, em uma frase curta.

Frase técnica: "{status_text}"
"""
    try:
        return (await _call_claude(prompt, 200)).strip()
    except Exception:
        return status_text
