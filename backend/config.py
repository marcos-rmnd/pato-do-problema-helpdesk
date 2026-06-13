import os

BASE_DIR = os.path.dirname(__file__)
_envp = os.path.join(BASE_DIR, ".env")
if os.path.exists(_envp):
    with open(_envp, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

import ai
import auth
import notify

APP_ENV = os.getenv("APP_ENV", "development").lower()
PUBLIC_TECH_REGISTRATION = os.getenv("ENABLE_PUBLIC_TECH_REGISTRATION", "false").lower() == "true"
ALLOW_DEV_RESET_TOKEN = os.getenv("ALLOW_DEV_RESET_TOKEN", "true").lower() == "true" and APP_ENV != "production"
SEED_DEMO = os.getenv("SEED_DEMO", "true" if APP_ENV != "production" else "false").lower() == "true"
MAX_FILE = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

TECH_ROLES = ("N1", "N2", "N3")
ALLOWED_ROLES = ("cliente",) + TECH_ROLES
ALLOWED_CHANNELS = ("Chat",)
ALLOWED_FREQUENCIES = (
    "Apenas atualizações importantes",
    "Atualizações automáticas",
    "Acompanhamento prioritário",
)
ALLOWED_STATUSES = (
    "Aberto",
    "Em análise",
    "Em atendimento",
    "Aguardando cliente",
    "Aguardando terceiro",
    "Resolvido",
    "Encerrado",
)
NEXT_LEVEL = {"N1": "N2", "N2": "N3", "N3": None}
ALLOWED_ATTACHMENT_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "application/pdf", "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

ai.API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ai.MODEL = os.getenv("ANTHROPIC_MODEL", ai.MODEL)
auth.JWT_SECRET = os.getenv("JWT_SECRET", auth.JWT_SECRET)
auth.TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", str(auth.TOKEN_HOURS)))
notify.SMTP_HOST = os.getenv("SMTP_HOST", "")
notify.SMTP_PORT = int(os.getenv("SMTP_PORT", str(notify.SMTP_PORT)))
notify.SMTP_USER = os.getenv("SMTP_USER", "")
notify.SMTP_PASS = os.getenv("SMTP_PASS", "")
notify.SMTP_FROM = os.getenv("SMTP_FROM", notify.SMTP_USER or "no-reply@pato.local")

if APP_ENV == "production" and auth.JWT_SECRET == "dev-secret-troque-isso":
    raise RuntimeError("Configure JWT_SECRET antes de iniciar em produção.")

if APP_ENV == "production" and ALLOWED_ORIGINS.strip() == "*":
    raise RuntimeError("Configure ALLOWED_ORIGINS antes de iniciar em produção.")


def cors_origins() -> list[str]:
    if ALLOWED_ORIGINS.strip() == "*":
        return ["*"]
    return [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
