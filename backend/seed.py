import auth
import database as db


def seed_demo():
    conn = db.get_conn()
    n = db.fetchone(conn, "SELECT COUNT(*) AS n FROM users")["n"]
    if n == 0:
        users = [
            ("Cliente Demo", "cliente@demo.com", "1234", "cliente"),
            ("Suporte N1", "n1@demo.com", "1234", "N1"),
            ("Suporte N2", "n2@demo.com", "1234", "N2"),
            ("Suporte N3", "n3@demo.com", "1234", "N3"),
        ]
        for name, email, pw, role in users:
            db.execute(
                conn,
                "INSERT INTO users (name,email,password_hash,role,created_at) VALUES (?,?,?,?,?)",
                (name, email, auth.hash_password(pw), role, db.now()),
            )
        conn.commit()

    nk = db.fetchone(conn, "SELECT COUNT(*) AS n FROM kb_articles")["n"]
    if nk == 0:
        articles = [
            (
                "Redefinir senha",
                "Use a opção 'Esqueci minha senha' na tela de login. Se o e-mail não chegar, confira o spam e abra um chamado informando seu usuário.",
                "Acesso",
                "senha,login,acesso",
            ),
            (
                "VPN não conecta",
                "Verifique sua internet, feche o cliente VPN e tente conectar novamente. Se continuar falhando, envie um print do erro no chamado.",
                "Rede",
                "vpn,rede,conexao",
            ),
            (
                "Acesso a pasta de rede",
                "Informe o caminho da pasta e qual mensagem aparece ao tentar acessar. O suporte valida se é falha local ou permissão.",
                "Rede",
                "rede,arquivos,permissao",
            ),
            (
                "Impressora não imprime",
                "Confira se a impressora está ligada, com papel e sem documentos presos na fila. Se não resolver, envie o nome da impressora.",
                "Hardware",
                "impressora,hardware",
            ),
            (
                "E-mail no celular",
                "Informe o modelo do celular e o erro exibido na configuração. O suporte confirma os dados de acesso antes de encaminhar para N2.",
                "E-mail",
                "email,celular",
            ),
        ]
        for title, content, category, tags in articles:
            db.execute(
                conn,
                "INSERT INTO kb_articles (title,content,category,tags,author,views,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (title, content, category, tags, "Suporte N1", 0, db.now(), db.now()),
            )
        conn.commit()
    conn.close()
