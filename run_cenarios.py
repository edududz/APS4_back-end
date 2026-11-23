"""
Script de demonstração e execução dos 12 cenários de teste da APS 4.
Demonstração completa de autenticação JWT, perfis RBAC, proteção de rotas,
hash Argon2 e continuidade de todas as regras da APS 3.
"""

import json
from datetime import timedelta
from fastapi.testclient import TestClient
from main import app
from database import init_db, SessionLocal
from model.usuario import Usuario
from model.evento import Evento
from model.participante import Participante
from model.inscricao import Inscricao
from security.security import create_initial_admin, create_access_token

client = TestClient(app)

def reset_db():
    init_db()
    db = SessionLocal()
    db.query(Inscricao).delete()
    db.query(Participante).delete()
    db.query(Evento).delete()
    db.query(Usuario).delete()
    db.commit()
    create_initial_admin(db)
    db.close()

def print_section(titulo):
    print("\n" + "=" * 80)
    print(f" {titulo} ")
    print("=" * 80)

def main():
    print_section("INICIALIZANDO TESTES DOS 12 CENÁRIOS DA APS 4")
    reset_db()

    # Cenário 1
    print_section("CENÁRIO 1: Cadastro de um usuário comum (POST /usuarios)")
    u_payload = {
        "nome": "Aluno Exemplo",
        "email": "aluno@exemplo.com",
        "senha": "senha_segura_123"
    }
    r = client.post("/usuarios/", json=u_payload)
    print(f"[POST /usuarios/] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 2
    print_section("CENÁRIO 2: Verificação de que a senha foi armazenada como hash no SQLite")
    db = SessionLocal()
    u_db = db.query(Usuario).filter(Usuario.email == "aluno@exemplo.com").first()
    print(f"E-mail: {u_db.email}")
    print(f"Perfil: {u_db.perfil}")
    print(f"Hash armazenado no banco: {u_db.senha_hash}")
    print(f"A senha pura 'senha_segura_123' está presente no banco? {'NÃO' if 'senha_segura_123' not in u_db.senha_hash else 'SIM'}")
    print(f"O algoritmo utilizado é Argon2? {'SIM ($argon2id$)' if u_db.senha_hash.startswith('$argon2id$') else 'NÃO'}")
    db.close()

    # Cenário 3
    print_section("CENÁRIO 3: Tentativa de cadastro com e-mail duplicado (Esperado: 409 Conflict)")
    r = client.post("/usuarios/", json=u_payload)
    print(f"[POST /usuarios/] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 4
    print_section("CENÁRIO 4: Autenticação com credenciais válidas (POST /auth/login)")
    login_payload = {
        "email": "aluno@exemplo.com",
        "senha": "senha_segura_123"
    }
    r = client.post("/auth/login", json=login_payload)
    print(f"[POST /auth/login] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))
    user_token = r.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Autenticação do Administrador
    r_adm = client.post("/auth/login", json={"email": "admin@universidade.edu.br", "senha": "admin123"})
    admin_token = r_adm.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Cenário 5
    print_section("CENÁRIO 5: Tentativa de autenticação com credenciais inválidas (Esperado: 401)")
    r = client.post("/auth/login", json={"email": "aluno@exemplo.com", "senha": "senha_errada"})
    print("[Tentativa 1 - Senha incorreta]")
    print(f"[POST /auth/login] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    r = client.post("/auth/login", json={"email": "naoexiste@exemplo.com", "senha": "qualquer_senha"})
    print("\n[Tentativa 2 - E-mail inexistente]")
    print(f"[POST /auth/login] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 6
    print_section("CENÁRIO 6: Acesso a uma rota protegida sem token (Esperado: 401 Unauthorized)")
    r = client.post("/eventos/", json={
        "titulo": "Evento Sem Token",
        "descricao": "Teste de proteção",
        "data": "2026-12-10",
        "horario": "10:00",
        "local": "Auditório",
        "capacidade": 50,
        "categoria": "Palestra"
    })
    print(f"[POST /eventos/ sem token] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))

    # Cenário 7
    print_section("CENÁRIO 7: Acesso a uma rota protegida com token válido")
    ev_payload = {
        "titulo": "Seminário Avançado de IA",
        "descricao": "Grandes modelos de linguagem e segurança",
        "data": "2026-12-12",
        "horario": "19:00",
        "local": "Auditório Central",
        "capacidade": 100,
        "categoria": "Seminário"
    }
    r = client.post("/eventos/", json=ev_payload, headers=admin_headers)
    print(f"[POST /eventos/ com token admin] Status: {r.status_code}")
    print("Resposta:", json.dumps(r.json(), indent=2, ensure_ascii=False))
    ev_id = r.json()["id"]

    # Cenário 8
    print_section("CENÁRIO 8: Acesso com token inválido ou expirado (Esperado: 401 Unauthorized)")
    r_inv = client.get("/auth/me", headers={"Authorization": "Bearer token_falsificado_abc_123"})
    print("[Tentativa 1 - Token Adulterado/Inválido]")
    print(f"[GET /auth/me] Status: {r_inv.status_code}")
    print("Resposta:", json.dumps(r_inv.json(), indent=2, ensure_ascii=False))

    exp_token = create_access_token(
        data={"sub": "1", "email": "admin@universidade.edu.br", "perfil": "administrador"},
        expires_delta=timedelta(minutes=-5)
    )
    r_exp = client.get("/auth/me", headers={"Authorization": f"Bearer {exp_token}"})
    print("\n[Tentativa 2 - Token Expirado]")
    print(f"[GET /auth/me] Status: {r_exp.status_code}")
    print("Resposta:", json.dumps(r_exp.json(), indent=2, ensure_ascii=False))

    # Cenário 9
    print_section("CENÁRIO 9: Tentativa de operação administrativa por usuário comum (Esperado: 403 Forbidden)")
    r_bloq = client.post("/eventos/", json={
        "titulo": "Evento Proibido",
        "descricao": "Tentativa por usuario comum",
        "data": "2026-12-20",
        "horario": "08:00",
        "local": "Sala 10",
        "capacidade": 30,
        "categoria": "Teste"
    }, headers=user_headers)
    print(f"[POST /eventos/ com token de perfil 'usuario'] Status: {r_bloq.status_code}")
    print("Resposta:", json.dumps(r_bloq.json(), indent=2, ensure_ascii=False))

    # Cenário 10
    print_section("CENÁRIO 10: Execução de operação administrativa por um administrador")
    r_edit = client.put(f"/eventos/{ev_id}", json={
        "titulo": "Seminário Avançado de IA e Engenharia de Software",
        "capacidade": 120
    }, headers=admin_headers)
    print(f"[PUT /eventos/{ev_id} com token admin] Status: {r_edit.status_code}")
    print("Resposta:", json.dumps(r_edit.json(), indent=2, ensure_ascii=False))

    # Cenário 11
    print_section("CENÁRIO 11: Consulta dos dados do usuário autenticado utilizando /auth/me")
    r_me = client.get("/auth/me", headers=user_headers)
    print("[GET /auth/me - Usuário Comum]")
    print(f"Status: {r_me.status_code}")
    print("Resposta:", json.dumps(r_me.json(), indent=2, ensure_ascii=False))

    r_me_admin = client.get("/auth/me", headers=admin_headers)
    print("\n[GET /auth/me - Administrador]")
    print(f"Status: {r_me_admin.status_code}")
    print("Resposta:", json.dumps(r_me_admin.json(), indent=2, ensure_ascii=False))

    # Cenário 12
    print_section("CENÁRIO 12: Preservação das funcionalidades e relatórios consolidados da APS 3")
    # Cadastro de participante
    part = client.post("/participantes/", json={
        "nome": "Juliana Santos",
        "email": "juliana@faculdade.edu.br",
        "curso": "Engenharia de Software"
    }, headers=admin_headers).json()
    print(f"Participante cadastrado: ID {part['id']}, Nome: {part['nome']}")

    # Inscrição realizada por usuário autenticado
    insc = client.post(f"/eventos/{ev_id}/inscricoes/{part['id']}", headers=user_headers)
    print(f"[POST /eventos/{ev_id}/inscricoes/{part['id']}] Status: {insc.status_code}")
    print("Resposta da inscrição:", json.dumps(insc.json(), indent=2, ensure_ascii=False))

    # Tentativa de inscrição duplicada
    insc_dup = client.post(f"/eventos/{ev_id}/inscricoes/{part['id']}", headers=user_headers)
    print(f"Tentativa duplicada - Status: {insc_dup.status_code} - Detail: {insc_dup.json().get('detail')}")

    # Consulta de relatórios pelo Admin
    rel_ocup = client.get("/relatorios/eventos/ocupacao", headers=admin_headers).json()
    print("\nRelatório de Ocupação consolidado:")
    print(json.dumps(rel_ocup, indent=2, ensure_ascii=False))

    print_section("TODOS OS 12 CENÁRIOS DA APS 4 FORAM DEMONSTRADOS COM SUCESSO!")

if __name__ == "__main__":
    main()
