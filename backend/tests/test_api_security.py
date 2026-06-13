def test_public_registration_cannot_create_tech_account(client):
    response = client.post(
        "/api/register",
        json={
            "name": "Pessoa Cliente",
            "email": "pessoa@example.com",
            "password": "senha-segura",
            "role": "N3",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["role"] == "cliente"


def test_ticket_visibility_respects_support_queue_level(client, login_as):
    client_headers = {"Authorization": f"Bearer {login_as('cliente@demo.com')}"}
    ticket = client.post(
        "/api/tickets",
        headers=client_headers,
        json={
            "title": "Impressora não imprime",
            "description": "A impressora do setor financeiro parou de imprimir documentos.",
            "priority": "Média",
            "channel": "Chat",
            "frequency": "Apenas atualizações importantes",
        },
    ).json()

    n1_headers = {"Authorization": f"Bearer {login_as('n1@demo.com')}"}
    n2_headers = {"Authorization": f"Bearer {login_as('n2@demo.com')}"}
    n3_headers = {"Authorization": f"Bearer {login_as('n3@demo.com')}"}

    assert client.get(f"/api/tickets/{ticket['id']}", headers=n1_headers).status_code == 200
    assert client.get(f"/api/tickets/{ticket['id']}", headers=n2_headers).status_code == 403
    assert client.get(f"/api/tickets/{ticket['id']}", headers=n3_headers).status_code == 403

    blocked_direct_to_n3 = client.post(
        f"/api/tickets/{ticket['id']}/escalate",
        headers=n1_headers,
        json={"level": "N3"},
    )
    assert blocked_direct_to_n3.status_code == 400

    to_n2 = client.post(
        f"/api/tickets/{ticket['id']}/escalate",
        headers=n1_headers,
        json={"level": "N2"},
    )
    assert to_n2.status_code == 200, to_n2.text
    assert client.get(f"/api/tickets/{ticket['id']}", headers=n1_headers).status_code == 403
    assert client.get(f"/api/tickets/{ticket['id']}", headers=n2_headers).status_code == 200
    assert client.get(f"/api/tickets/{ticket['id']}", headers=n3_headers).status_code == 403

    to_n3 = client.post(
        f"/api/tickets/{ticket['id']}/escalate",
        headers=n2_headers,
        json={"level": "N3"},
    )
    assert to_n3.status_code == 200, to_n3.text
    assert client.get(f"/api/tickets/{ticket['id']}", headers=n2_headers).status_code == 403
    assert client.get(f"/api/tickets/{ticket['id']}", headers=n3_headers).status_code == 200


def test_cliente_cannot_read_another_client_ticket(client, login_as):
    first_headers = {"Authorization": f"Bearer {login_as('cliente@demo.com')}"}
    ticket = client.post(
        "/api/tickets",
        headers=first_headers,
        json={
            "title": "Erro no sistema",
            "description": "A tela inicial mostra erro ao carregar as informações.",
            "priority": "Alta",
            "channel": "Chat",
            "frequency": "Apenas atualizações importantes",
        },
    ).json()

    created = client.post(
        "/api/register",
        json={"name": "Outra Pessoa", "email": "outra@example.com", "password": "senha-segura"},
    )
    other_headers = {"Authorization": f"Bearer {created.json()['token']}"}

    assert client.get(f"/api/tickets/{ticket['id']}", headers=other_headers).status_code == 403


def test_attachment_upload_validates_type_and_sanitizes_filename(client, login_as):
    client_headers = {"Authorization": f"Bearer {login_as('cliente@demo.com')}"}
    ticket = client.post(
        "/api/tickets",
        headers=client_headers,
        json={
            "title": "Erro ao acessar sistema",
            "description": "O sistema apresenta erro ao abrir a tela inicial.",
            "priority": "Alta",
            "channel": "Chat",
            "frequency": "Apenas atualizações importantes",
        },
    ).json()

    blocked = client.post(
        f"/api/tickets/{ticket['id']}/attachments",
        headers=client_headers,
        files={"file": ("script.exe", b"fake", "application/x-msdownload")},
    )
    assert blocked.status_code == 400

    allowed = client.post(
        f"/api/tickets/{ticket['id']}/attachments",
        headers=client_headers,
        files={"file": ("../erro tela.txt", b"log do erro", "text/plain")},
    )
    assert allowed.status_code == 200, allowed.text
    assert ".." not in allowed.json()["filename"]


def test_attachment_download_requires_ticket_access(client, login_as):
    client_headers = {"Authorization": f"Bearer {login_as('cliente@demo.com')}"}
    ticket = client.post(
        "/api/tickets",
        headers=client_headers,
        json={
            "title": "Erro ao abrir relatório",
            "description": "O relatório financeiro não abre e mostra erro na tela.",
            "priority": "Média",
            "channel": "Chat",
            "frequency": "Apenas atualizações importantes",
        },
    ).json()

    upload = client.post(
        f"/api/tickets/{ticket['id']}/attachments",
        headers=client_headers,
        files={"file": ("erro.txt", b"conteudo do erro", "text/plain")},
    )
    assert upload.status_code == 200, upload.text

    attachments = client.get(f"/api/tickets/{ticket['id']}/attachments", headers=client_headers).json()
    attachment_id = attachments[0]["id"]

    no_token = client.get(f"/api/attachments/{attachment_id}")
    assert no_token.status_code == 401

    downloaded = client.get(f"/api/attachments/{attachment_id}", headers=client_headers)
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.content == b"conteudo do erro"


def test_ticket_csv_export_neutralizes_formula_values(client, login_as):
    client_headers = {"Authorization": f"Bearer {login_as('cliente@demo.com')}"}
    created = client.post(
        "/api/tickets",
        headers=client_headers,
        json={
            "title": "=IMPORTDATA exemplo",
            "description": "O titulo simula um valor perigoso ao abrir CSV em planilhas.",
            "priority": "Baixa",
            "channel": "Chat",
            "frequency": "Apenas atualizações importantes",
        },
    )
    assert created.status_code == 200, created.text

    tech_headers = {"Authorization": f"Bearer {login_as('n1@demo.com')}"}
    exported = client.get("/api/export/tickets.csv", headers=tech_headers)
    assert exported.status_code == 200, exported.text
    assert "\"'=IMPORTDATA exemplo\"" in exported.text
