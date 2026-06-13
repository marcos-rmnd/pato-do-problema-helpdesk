from pydantic import BaseModel


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str
    role: str = "cliente"


class LoginIn(BaseModel):
    email: str
    password: str


class TicketIn(BaseModel):
    title: str
    description: str
    priority: str
    channel: str = "Chat"
    frequency: str = "Apenas atualizações importantes"


class MessageIn(BaseModel):
    content: str


class ChannelIn(BaseModel):
    channel: str


class StatusIn(BaseModel):
    status: str


class EscalateIn(BaseModel):
    level: str


class ForgotIn(BaseModel):
    email: str


class ResetIn(BaseModel):
    token: str
    password: str


class HumanizeIn(BaseModel):
    text: str


class KBArticleIn(BaseModel):
    title: str
    content: str
    category: str = "Geral"
    tags: str = ""


class KBSearchIn(BaseModel):
    query: str


class ProfileIn(BaseModel):
    name: str
