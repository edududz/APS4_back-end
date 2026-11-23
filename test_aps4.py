import os
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from database import Base, engine, SessionLocal, init_db
from main import app
from model.usuario import Usuario
from model.evento import Evento
from model.participante import Participante
from model.inscricao import Inscricao
from security.security import create_initial_admin, create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Garante isolamento limpando as tabelas e recriando o admin padrão antes de cada teste."""
    init_db()
    db = SessionLocal()
    try:
        db.query(Inscricao).delete()
        db.query(Participante).delete()
        db.query(Evento).delete()
        db.query(Usuario).delete()
        db.commit()
        # Inicializa o admin padrão da aplicação
        create_initial_admin(db)
    finally:
        db.close()
    yield

def get_admin_headers():
    """Helper para obter cabeçalho de autorização do administrador padrão."""
    login_res = client.post("/auth/login", json={
        "email": "admin@universidade.edu.br",
        "senha": "admin123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def get_user_headers(email="aluno@exemplo.com", senha="senha_segura"):
    """Helper para cadastrar (se necessário) e autenticar um usuário comum."""
    client.post("/usuarios/", json={
        "nome": "Aluno Teste",
        "email": email,
        "senha": senha
    })
    login_res = client.post("/auth/login", json={
        "email": email,
        "senha": senha
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ==============================================================================
# OS 12 CENÁRIOS OBRIGATÓRIOS DA APS 4
# ==============================================================================

def test_cenario_01_cadastro_usuario():
    """Cenário 1: Cadastro de um usuário comum (POST /usuarios).
    Deve retornar 201 Created com dados do usuário e sem expor a senha.
    """
    payload = {
        "nome": "Carlos Oliveira",
        "email": "carlos.oliveira@faculdade.edu.br",
        "senha": "senha_forte_123"
    }
    response = client.post("/usuarios/", json=payload)
    assert response.status_code == 201
    dados = response.json()
    assert dados["id"] is not None
    assert dados["nome"] == payload["nome"]
    assert dados["email"] == payload["email"]
    assert dados["perfil"] == "usuario"
    assert "senha" not in dados
    assert "senha_hash" not in dados

def test_cenario_02_verificacao_senha_armazenada_como_hash():
    """Cenário 2: Verificação de que a senha foi armazenada como hash criptográfico no SQLite."""
    payload = {
        "nome": "Mariana Ramos",
        "email": "mariana.ramos@faculdade.edu.br",
        "senha": "senha_secreta_999"
    }
    res = client.post("/usuarios/", json=payload)
    assert res.status_code == 201

    db = SessionLocal()
    try:
        user_db = db.query(Usuario).filter(Usuario.email == payload["email"]).first()
        assert user_db is not None
        # O hash não pode ser a senha pura
        assert user_db.senha_hash != payload["senha"]
        # Deve ser um hash Argon2 seguro
        assert user_db.senha_hash.startswith("$argon2id$")
    finally:
        db.close()

def test_cenario_03_tentativa_cadastro_email_duplicado():
    """Cenário 3: Tentativa de cadastro com e-mail duplicado (deve retornar 409 Conflict)."""
    payload = {
        "nome": "Primeiro Usuario",
        "email": "duplicado@faculdade.edu.br",
        "senha": "senha_original"
    }
    res1 = client.post("/usuarios/", json=payload)
    assert res1.status_code == 201

    # Segunda tentativa com o mesmo e-mail
    payload2 = {
        "nome": "Segundo Usuario",
        "email": "duplicado@faculdade.edu.br",
        "senha": "outra_senha"
    }
    res2 = client.post("/usuarios/", json=payload2)
    assert res2.status_code == 409
    assert res2.json()["detail"] == "Já existe um usuário cadastrado com este e-mail."

def test_cenario_04_autenticacao_credenciais_validas():
    """Cenário 4: Autenticação com credenciais válidas (deve retornar 200 OK e token JWT)."""
    # Cadastra usuário
    client.post("/usuarios/", json={
        "nome": "Fernanda Lima",
        "email": "fernanda@faculdade.edu.br",
        "senha": "senha_correta"
    })

    # Autentica
    res = client.post("/auth/login", json={
        "email": "fernanda@faculdade.edu.br",
        "senha": "senha_correta"
    })
    assert res.status_code == 200
    dados = res.json()
    assert "access_token" in dados
    assert dados["token_type"] == "bearer"
    assert len(dados["access_token"]) > 20

def test_cenario_05_tentativa_autenticacao_credenciais_invalidas():
    """Cenário 5: Tentativa de autenticação com credenciais inválidas (deve retornar 401)."""
    # 1. E-mail existente com senha incorreta
    client.post("/usuarios/", json={
        "nome": "Beatriz Silva",
        "email": "beatriz@faculdade.edu.br",
        "senha": "senha_certa"
    })
    res_senha_errada = client.post("/auth/login", json={
        "email": "beatriz@faculdade.edu.br",
        "senha": "senha_errada"
    })
    assert res_senha_errada.status_code == 401
    assert res_senha_errada.json()["detail"] == "E-mail ou senha inválidos."

    # 2. E-mail inexistente
    res_email_inexistente = client.post("/auth/login", json={
        "email": "inexistente@faculdade.edu.br",
        "senha": "qualquer_senha"
    })
    assert res_email_inexistente.status_code == 401
    assert res_email_inexistente.json()["detail"] == "E-mail ou senha inválidos."

def test_cenario_06_acesso_rota_protegida_sem_token():
    """Cenário 6: Acesso a uma rota protegida sem token (deve retornar 401 Unauthorized)."""
    # Tenta cadastrar evento sem fornecer o cabeçalho Authorization
    evento_payload = {
        "titulo": "Workshop de Segurança",
        "descricao": "Práticas de autenticação",
        "data": "2026-12-15",
        "horario": "14:00",
        "local": "Lab 10",
        "capacidade": 30,
        "categoria": "Workshop"
    }
    res = client.post("/eventos/", json=evento_payload)
    assert res.status_code == 401
    assert res.json()["detail"] == "Não foi possível validar as credenciais."

    # Tenta acessar /auth/me sem token
    res_me = client.get("/auth/me")
    assert res_me.status_code == 401
    assert res_me.json()["detail"] == "Não foi possível validar as credenciais."

def test_cenario_07_acesso_rota_protegida_com_token_valido():
    """Cenário 7: Acesso a uma rota protegida com token válido."""
    headers_admin = get_admin_headers()
    evento_payload = {
        "titulo": "Congresso de Tecnologia 2026",
        "descricao": "Inovações em Engenharia de Software",
        "data": "2026-12-20",
        "horario": "09:00",
        "local": "Auditório Magna",
        "capacidade": 200,
        "categoria": "Congresso"
    }
    res = client.post("/eventos/", json=evento_payload, headers=headers_admin)
    assert res.status_code == 201
    assert res.json()["id"] is not None
    assert res.json()["titulo"] == evento_payload["titulo"]

def test_cenario_08_acesso_token_invalido_ou_expirado():
    """Cenário 8: Acesso com token inválido ou expirado (deve retornar 401 Unauthorized)."""
    # 1. Token inválido/adulterado
    headers_invalido = {"Authorization": "Bearer token_falso_adulterado_xyz"}
    res_invalido = client.get("/auth/me", headers=headers_invalido)
    assert res_invalido.status_code == 401
    assert res_invalido.json()["detail"] == "Não foi possível validar as credenciais."

    # 2. Token expirado
    token_expirado = create_access_token(
        data={"sub": "1", "email": "admin@universidade.edu.br", "perfil": "administrador"},
        expires_delta=timedelta(minutes=-10)  # Expirado há 10 minutos
    )
    headers_expirado = {"Authorization": f"Bearer {token_expirado}"}
    res_expirado = client.get("/auth/me", headers=headers_expirado)
    assert res_expirado.status_code == 401
    assert res_expirado.json()["detail"] == "Não foi possível validar as credenciais."

def test_cenario_09_tentativa_operacao_administrativa_por_usuario_comum():
    """Cenário 9: Tentativa de execução de operação administrativa por usuário comum (deve retornar 403 Forbidden)."""
    headers_usuario = get_user_headers("aluno_comum@exemplo.com", "senha12345")

    evento_payload = {
        "titulo": "Tentativa Não Autorizada",
        "descricao": "Tentando criar evento sem ser admin",
        "data": "2026-12-18",
        "horario": "10:00",
        "local": "Sala 1",
        "capacidade": 10,
        "categoria": "Teste"
    }
    # Usuário comum tentando POST /eventos/
    res_evento = client.post("/eventos/", json=evento_payload, headers=headers_usuario)
    assert res_evento.status_code == 403
    assert res_evento.json()["detail"] == "Você não possui permissão para executar esta operação."

    # Usuário comum tentando acessar relatório consolidado
    res_relatorio = client.get("/relatorios/eventos/ocupacao", headers=headers_usuario)
    assert res_relatorio.status_code == 403
    assert res_relatorio.json()["detail"] == "Você não possui permissão para executar esta operação."

def test_cenario_10_execucao_operacao_administrativa_por_administrador():
    """Cenário 10: Execução de uma operação administrativa por um administrador."""
    headers_admin = get_admin_headers()

    # 1. Administrador cadastra evento
    res_criar = client.post("/eventos/", json={
        "titulo": "Simpósio de Cibersegurança",
        "descricao": "Defesas e Auditoria",
        "data": "2026-12-22",
        "horario": "15:00",
        "local": "Teatro Universitário",
        "capacidade": 150,
        "categoria": "Simpósio"
    }, headers=headers_admin)
    assert res_criar.status_code == 201
    ev_id = res_criar.json()["id"]

    # 2. Administrador atualiza evento
    res_update = client.put(f"/eventos/{ev_id}", json={
        "titulo": "Simpósio Internacional de Cibersegurança",
        "capacidade": 180
    }, headers=headers_admin)
    assert res_update.status_code == 200
    assert res_update.json()["titulo"] == "Simpósio Internacional de Cibersegurança"
    assert res_update.json()["capacidade"] == 180

    # 3. Administrador consulta relatórios
    res_rel = client.get("/relatorios/eventos/ocupacao", headers=headers_admin)
    assert res_rel.status_code == 200

    # 4. Administrador exclui evento
    res_del = client.delete(f"/eventos/{ev_id}", headers=headers_admin)
    assert res_del.status_code == 204

def test_cenario_11_consulta_dados_usuario_autenticado_auth_me():
    """Cenário 11: Consulta dos dados do usuário autenticado utilizando /auth/me."""
    # Autentica como usuário comum
    headers_usuario = get_user_headers("mariana.silva@exemplo.com", "senha_da_mariana")
    res = client.get("/auth/me", headers=headers_usuario)
    assert res.status_code == 200
    dados = res.json()
    assert dados["email"] == "mariana.silva@exemplo.com"
    assert dados["perfil"] == "usuario"
    assert "senha" not in dados
    assert "senha_hash" not in dados

    # Autentica como administrador
    headers_admin = get_admin_headers()
    res_admin = client.get("/auth/me", headers=headers_admin)
    assert res_admin.status_code == 200
    dados_admin = res_admin.json()
    assert dados_admin["email"] == "admin@universidade.edu.br"
    assert dados_admin["perfil"] == "administrador"

def test_cenario_12_continuidade_funcionalidades_e_relatorios_aps3():
    """Cenário 12: Verificação de que as funcionalidades e relatórios da APS 3 continuam funcionando."""
    headers_admin = get_admin_headers()
    headers_user = get_user_headers("participante_teste@exemplo.com", "senha123456")

    # 1. Admin cria evento
    ev = client.post("/eventos/", json={
        "titulo": "Mini Curso de FastAPI e SQLAlchemy",
        "descricao": "Construindo APIs robustas",
        "data": "2026-12-25",
        "horario": "14:00",
        "local": "Lab 01",
        "capacidade": 2,
        "categoria": "Minicurso"
    }, headers=headers_admin).json()

    # 2. Admin cadastra participantes
    p1 = client.post("/participantes/", json={
        "nome": "Lucas Martins",
        "email": "lucas@exemplo.com",
        "curso": "Engenharia de Software"
    }, headers=headers_admin).json()

    p2 = client.post("/participantes/", json={
        "nome": "Aline Costa",
        "email": "aline@exemplo.com",
        "curso": "Ciência da Computação"
    }, headers=headers_admin).json()

    p3 = client.post("/participantes/", json={
        "nome": "Renato Souza",
        "email": "renato@exemplo.com",
        "curso": "Engenharia de Software"
    }, headers=headers_admin).json()

    # 3. Usuário autenticado inscreve p1 e p2 no evento
    insc1 = client.post(f"/eventos/{ev['id']}/inscricoes/{p1['id']}", headers=headers_user)
    assert insc1.status_code == 201
    assert insc1.json()["detail"] == "Inscrição realizada com sucesso."

    insc2 = client.post(f"/eventos/{ev['id']}/inscricoes/{p2['id']}", headers=headers_user)
    assert insc2.status_code == 201

    # 4. Inscrição duplicada (409)
    insc_dup = client.post(f"/eventos/{ev['id']}/inscricoes/{p1['id']}", headers=headers_user)
    assert insc_dup.status_code == 409
    assert insc_dup.json()["detail"] == "Participante já está inscrito neste evento."

    # 5. Tentativa de inscrição sem vagas (evento lotado, capacidade=2) -> 409
    insc_lotado = client.post(f"/eventos/{ev['id']}/inscricoes/{p3['id']}", headers=headers_user)
    assert insc_lotado.status_code == 409
    assert insc_lotado.json()["detail"] == "Não existem vagas disponíveis para este evento."

    # 6. Tentativa de inscrição em evento inexistente -> 404
    insc_404 = client.post(f"/eventos/99999/inscricoes/{p3['id']}", headers=headers_user)
    assert insc_404.status_code == 404

    # 7. Relatórios consolidados acessados pelo Administrador
    rel_ocupacao = client.get("/relatorios/eventos/ocupacao", headers=headers_admin)
    assert rel_ocupacao.status_code == 200
    assert any(r["evento_id"] == ev["id"] and r["total_inscritos"] == 2 and r["percentual_ocupacao"] == 100.0 for r in rel_ocupacao.json())

    rel_categoria = client.get("/relatorios/eventos/categorias", headers=headers_admin)
    assert rel_categoria.status_code == 200
    assert any(c["categoria"] == "Minicurso" and c["total_inscricoes"] == 2 for c in rel_categoria.json())

    rel_curso = client.get("/relatorios/participantes/cursos", headers=headers_admin)
    assert rel_curso.status_code == 200
    assert any(cur["curso"] == "Engenharia de Software" and cur["total_inscricoes"] == 1 for cur in rel_curso.json())
