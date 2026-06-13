def test_authentication_and_profile_update(client, login_as):
    token = login_as("cliente@demo.com")
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "cliente@demo.com"

    updated = client.put("/api/me", headers=headers, json={"name": "Cliente Teste"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Cliente Teste"


def test_cliente_opens_ticket_and_n1_updates_it(client, login_as):
    client_headers = {"Authorization": f"Bearer {login_as('cliente@demo.com')}"}
    ticket_response = client.post(
        "/api/tickets",
        headers=client_headers,
        json={
            "title": "Impressora não imprime",
            "description": "A impressora do financeiro parou de imprimir documentos pela manhã.",
            "priority": "Crítica",
            "channel": "Chat",
            "frequency": "Apenas atualizações importantes",
        },
    )
    assert ticket_response.status_code == 200, ticket_response.text
    ticket = ticket_response.json()
    assert ticket["level"] == "N1"
    assert ticket["priority"] == "Crítica"

    message = client.post(
        f"/api/tickets/{ticket['id']}/message",
        headers=client_headers,
        json={"content": "O erro aparece depois de enviar o arquivo para a fila."},
    )
    assert message.status_code == 200, message.text

    n1_headers = {"Authorization": f"Bearer {login_as('n1@demo.com')}"}
    queue = client.get("/api/queue", headers=n1_headers)
    assert queue.status_code == 200
    assert any(row["id"] == ticket["id"] for row in queue.json())

    status = client.post(
        f"/api/tickets/{ticket['id']}/status",
        headers=n1_headers,
        json={"status": "Em atendimento"},
    )
    assert status.status_code == 200, status.text

    detail = client.get(f"/api/tickets/{ticket['id']}", headers=client_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["status"] == "Em atendimento"
    assert any(e["kind"] == "message" for e in detail.json()["events"])


def test_missing_required_ticket_data_returns_clear_error(client, login_as):
    headers = {"Authorization": f"Bearer {login_as('cliente@demo.com')}"}
    response = client.post(
        "/api/tickets",
        headers=headers,
        json={
            "title": "Oi",
            "description": "curto",
            "priority": "Média",
            "channel": "Chat",
            "frequency": "Apenas atualizações importantes",
        },
    )

    assert response.status_code == 400
    assert "Título" in response.json()["detail"]


def test_password_reset_uses_dev_token_when_email_is_not_configured(client):
    forgot = client.post("/api/forgot", json={"email": "cliente@demo.com"})
    assert forgot.status_code == 200, forgot.text
    assert "dev_token" in forgot.json()

    reset = client.post("/api/reset", json={"token": forgot.json()["dev_token"], "password": "nova-senha"})
    assert reset.status_code == 200, reset.text

    login = client.post("/api/login", json={"email": "cliente@demo.com", "password": "nova-senha"})
    assert login.status_code == 200, login.text


def test_knowledge_base_can_be_managed_by_tech(client, login_as):
    n1_headers = {"Authorization": f"Bearer {login_as('n1@demo.com')}"}
    created = client.post(
        "/api/kb",
        headers=n1_headers,
        json={
            "title": "Limpar fila de impressão",
            "content": "Abra a fila de impressão, remova documentos presos e tente imprimir novamente.",
            "category": "Impressora",
            "tags": "impressora,fila",
        },
    )
    assert created.status_code == 200, created.text

    public_list = client.get("/api/kb?q=impressão")
    assert public_list.status_code == 200
    assert any(row["title"] == "Limpar fila de impressão" for row in public_list.json())


def test_tech_can_export_tickets_csv_but_client_cannot(client, login_as):
    client_headers = {"Authorization": f"Bearer {login_as('cliente@demo.com')}"}
    client.post(
        "/api/tickets",
        headers=client_headers,
        json={
            "title": "VPN não conecta",
            "description": "A VPN não conecta desde o começo do expediente.",
            "priority": "Alta",
            "channel": "Chat",
            "frequency": "Apenas atualizações importantes",
        },
    )

    blocked = client.get("/api/export/tickets.csv", headers=client_headers)
    assert blocked.status_code == 403

    tech_headers = {"Authorization": f"Bearer {login_as('n1@demo.com')}"}
    exported = client.get("/api/export/tickets.csv", headers=tech_headers)
    assert exported.status_code == 200, exported.text
    assert "codigo;titulo;cliente" in exported.text
    assert "VPN não conecta" in exported.text
