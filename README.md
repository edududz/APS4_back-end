# Avaliação Parcial 04 (APS 4) — Autenticação e Segurança em uma API RESTful

API RESTful completa desenvolvida com **FastAPI**, **SQLite**, **SQLAlchemy ORM** e **Pydantic**, implementando autenticação segura via **Tokens JWT**, hash de senhas com algoritmo robusto **Argon2** (via biblioteca `pwdlib`), controle de acesso baseado em perfis (**RBAC - Administrador e Usuário**), proteção de rotas, injeção de dependências do FastAPI e preservação integral de todas as regras de negócio e relatórios consolidados da APS 3.

---

## 1. Descrição do Projeto

Esta aplicação é a evolução da **APS 3**, adicionando uma camada completa de segurança, identificação de usuários e controle granular de autorização:
- **Armazenamento Seguro de Senhas**: As senhas nunca são gravadas em texto plano nem retornadas em respostas da API. Utiliza-se a biblioteca oficial recomendada `pwdlib` com o algoritmo criptográfico de última geração **Argon2** (`$argon2id$`).
- **Autenticação com JWT (JSON Web Token)**: Autenticação baseada em e-mail e senha (`POST /auth/login`), gerando tokens de acesso assinados digitalmente com prazo de validade configurável e validação através do esquema `Bearer`.
- **Controle de Acesso Baseado em Perfis (RBAC)**:
  - `administrador`: Gerenciamento completo de eventos (criar, atualizar, excluir), gerenciamento de participantes e acesso exclusivo a relatórios consolidados.
  - `usuario`: Cadastro público de conta de estudante/participante, consulta de eventos disponíveis, realização de inscrições em eventos e consulta de seus próprios dados autenticados (`/auth/me`).
- **Proteção Centralizada de Rotas**: Utilização dos mecanismos de dependências (`Depends`) do FastAPI para validar credenciais, rejeitar acessos não autorizados (401 Unauthorized) ou sem permissão suficiente (403 Forbidden).
- **Tratamento Padronizado de Códigos HTTP**: 200 (OK), 201 (Created), 204 (No Content), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 409 (Conflict) e 422 (Unprocessable Entity).
- **Continuidade da APS 3**: Preservação das regras de capacidade de eventos, integridade referencial, bloqueio de inscrições duplicadas e relatórios analíticos de ocupação, por categoria e por curso.

---

## 2. Estrutura do Projeto (Padrão MVC + Security)

A arquitetura mantém rigorosa separação de responsabilidades em camadas desacopladas:

```
aps4_eventos/
│
├── main.py                     # Ponto de entrada da aplicação FastAPI e ciclo de vida (lifespan)
├── database.py                 # Configuração do SQLite, engine, SessionLocal e foreign keys
├── requirements.txt           # Dependências do projeto (FastAPI, PyJWT, pwdlib, etc.)
├── .env.example                # Exemplo das variáveis de ambiente necessárias
├── .env                        # Configurações locais (chave secreta, algoritmo, expiração)
├── .gitignore                  # Arquivos ignorados pelo controle de versão Git
├── test_aps4.py                # Suíte de testes automatizados com Pytest (12 cenários)
├── run_cenarios.py             # Script de demonstração formatada dos 12 cenários
│
├── controller/                 # Camada de Apresentação (Rotas HTTP e injeção de dependências)
│   ├── auth_controller.py      # Rotas de login (/auth/login) e consulta de perfil (/auth/me)
│   ├── usuario_controller.py   # Rota de cadastro de usuários (/usuarios)
│   ├── evento_controller.py    # Rotas de eventos (/eventos) com proteção RBAC
│   ├── participante_controller.py # Rotas de participantes (/participantes)
│   ├── inscricao_controller.py # Rotas de inscrição (/eventos/{id}/inscricoes)
│   └── relatorio_controller.py # Rotas dos relatórios consolidados (/relatorios)
│
├── model/                      # Camada de Persistência (Entidades SQLAlchemy ORM)
│   ├── __init__.py
│   ├── usuario.py              # Tabela 'usuarios' (id, nome, email, senha_hash, perfil)
│   ├── evento.py               # Tabela 'eventos'
│   ├── participante.py         # Tabela 'participantes'
│   └── inscricao.py            # Tabela 'inscricoes' com chaves estrangeiras
│
├── schema/                     # Camada de Validação e DTOs (Pydantic V2)
│   ├── __init__.py
│   ├── usuario_schema.py       # Schemas de criação, resposta segura e login
│   ├── evento_schema.py        # Validação de eventos
│   ├── participante_schema.py  # Validação de participantes
│   ├── inscricao_schema.py     # Respostas de inscrição
│   └── relatorio_schema.py     # Schemas dos relatórios consolidados
│
├── service/                    # Camada de Negócio (Regras, validações e controle de fluxo)
│   ├── __init__.py
│   ├── auth_service.py         # Regra de autenticação, verificação de hash e geração de token
│   ├── usuario_service.py      # Regra de cadastro e validação de e-mail duplicado
│   ├── evento_service.py       # CRUD de eventos e checagem de vagas
│   ├── participante_service.py # CRUD e regras de participantes
│   ├── inscricao_service.py    # Regras de concorrência de vagas e duplicidade
│   └── relatorio_service.py    # Consultas agregadas e estatísticas via SQLAlchemy
│
└── security/                   # Módulo de Segurança Centralizado
    ├── __init__.py
    └── security.py             # Hashing Argon2, PyJWT, verificação de token e RBAC
```

---

## 3. Configuração da Chave Secreta e Variáveis de Ambiente

Conforme exigência do projeto (Seções 6 e 15), a chave secreta de assinatura dos tokens **nunca deve ser publicada no código-fonte**. As configurações são lidas do arquivo `.env` através da biblioteca `python-dotenv`:

Crie ou edite o arquivo `.env` na raiz do projeto (baseando-se no `.env.example`):

```env
# Chave secreta forte para assinatura HMAC-SHA256 dos tokens JWT
SECRET_KEY=chave_secreta_super_segura_aps4_evento_academico_2026

# Algoritmo de assinatura (padrão da indústria)
ALGORITHM=HS256

# Tempo de validade do token de acesso em minutos
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Credenciais do Administrador inicial (criado de forma segura no primeiro startup)
ADMIN_EMAIL=admin@universidade.edu.br
ADMIN_PASSWORD=admin123
ADMIN_NOME=Administrador do Sistema
```

> **Estratégia de Criação do Administrador Inicial (Item 3.1):**  
> Novos cadastros pela rota pública `POST /usuarios/` recebem estritamente o perfil `"usuario"`, impedindo que qualquer cliente se torne administrador por conta própria. A conta administrativa inicial é instanciada durante a inicialização (`lifespan`) de forma controlada e segura a partir das variáveis de ambiente configuradas.

---

## 4. Instalação e Execução

### Pré-requisitos
- Python 3.10 ou superior
- Pip e Git instalados

### Passo a Passo

1. **Clone ou navegue até o repositório:**
   ```bash
   cd aps4_eventos
   ```

2. **Crie e ative um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   # No Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # No Linux / macOS:
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie o servidor de desenvolvimento:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Acesse a documentação interativa Swagger UI:**
   Abra no seu navegador: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 5. Perfis de Usuário e Matriz de Permissões (RBAC)

| Rota / Endpoint | Método | Descrição | Acesso Permitido | Código de Não Autorizado |
| :--- | :---: | :--- | :---: | :---: |
| `/usuarios/` | `POST` | Cadastro público de novos usuários | **Público** | - |
| `/auth/login` | `POST` | Autenticação e emissão do JWT | **Público** | `401 Unauthorized` |
| `/auth/me` | `GET` | Consulta dados do usuário logado | **Autenticado** (Admin ou Usuário) | `401 Unauthorized` |
| `/eventos/` | `GET` | Listagem de eventos disponíveis | **Público / Autenticado** | - |
| `/eventos/{id}` | `GET` | Consulta detalhes de um evento | **Público / Autenticado** | - |
| `/eventos/` | `POST` | Criação de novo evento acadêmico | **Somente Administrador** | `401` / `403 Forbidden` |
| `/eventos/{id}` | `PUT` | Atualização cadastral de evento | **Somente Administrador** | `401` / `403 Forbidden` |
| `/eventos/{id}` | `DELETE`| Exclusão de evento existente | **Somente Administrador** | `401` / `403 Forbidden` |
| `/participantes/` | `POST` | Cadastro de participantes | **Somente Administrador** | `401` / `403 Forbidden` |
| `/participantes/` | `GET` | Listagem geral de participantes | **Autenticado** (Admin ou Usuário) | `401 Unauthorized` |
| `/participantes/{id}` | `GET` | Consulta participante por ID | **Autenticado** (Admin ou Usuário) | `401 Unauthorized` |
| `/participantes/{id}` | `PUT` | Atualização de participante | **Somente Administrador** | `401` / `403 Forbidden` |
| `/participantes/{id}` | `DELETE`| Exclusão de participante | **Somente Administrador** | `401` / `403 Forbidden` |
| `/eventos/{id}/inscricoes/{p_id}` | `POST` | Inscrição de participante em evento | **Autenticado** (Admin ou Usuário) | `401 Unauthorized` |
| `/eventos/{id}/inscricoes` | `GET` | Listagem de inscritos no evento | **Autenticado** (Admin ou Usuário) | `401 Unauthorized` |
| `/relatorios/eventos/ocupacao` | `GET` | Relatório de ocupação de eventos | **Somente Administrador** | `401` / `403 Forbidden` |
| `/relatorios/eventos/categorias`| `GET` | Relatório de eventos por categoria| **Somente Administrador** | `401` / `403 Forbidden` |
| `/relatorios/participantes/cursos`| `GET` | Relatório de adesão por curso | **Somente Administrador** | `401` / `403 Forbidden` |

---

## 6. Exemplos de Utilização da API

### 6.1. Cadastro de Usuário Comum
**Requisição:**
`POST /usuarios/`
```json
{
  "nome": "Mariana Santos",
  "email": "mariana@faculdade.edu.br",
  "senha": "minha_senha_segura"
}
```
**Resposta (HTTP 201 Created):**
```json
{
  "id": 2,
  "nome": "Mariana Santos",
  "email": "mariana@faculdade.edu.br",
  "perfil": "usuario"
}
```
*(Note que nem a senha nem o hash são expostos na resposta).*

### 6.2. Autenticação e Obtenção do Token JWT
**Requisição:**
`POST /auth/login`
```json
{
  "email": "mariana@faculdade.edu.br",
  "senha": "minha_senha_segura"
}
```
**Resposta (HTTP 200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 6.3. Utilizando o Token em Rotas Protegidas
Para acessar qualquer rota protegida, envie o token no cabeçalho HTTP:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

No **Swagger (/docs)**:
1. Clique no botão **Authorize** (com ícone de cadeado) no canto superior direito.
2. No campo **Value**, cole apenas o token JWT gerado.
3. Clique em **Authorize** e feche a janela modal. Agora todas as requisições enviarão o cabeçalho Bearer automaticamente.

### 6.4. Consultar Dados do Usuário Autenticado
**Requisição:**
`GET /auth/me`
*Header:* `Authorization: Bearer <seu_token_jwt>`

**Resposta (HTTP 200 OK):**
```json
{
  "id": 2,
  "nome": "Mariana Santos",
  "email": "mariana@faculdade.edu.br",
  "perfil": "usuario"
}
```

---

## 7. Tratamento de Erros Padronizado

A API responde com mensagens claras e seguras nos formatos especificados:

- **Credenciais Inválidas (Login):**
  - **Status:** `401 Unauthorized`
  - **JSON:** `{"detail": "E-mail ou senha inválidos."}`
  - *(Não revela se o erro foi no e-mail ou na senha, prevenindo enumeração de contas).*

- **Token Ausente, Inválido, Adulterado ou Expirado:**
  - **Status:** `401 Unauthorized`
  - **JSON:** `{"detail": "Não foi possível validar as credenciais."}`

- **Usuário Sem Permissão Suficiente (RBAC):**
  - **Status:** `403 Forbidden`
  - **JSON:** `{"detail": "Você não possui permissão para executar esta operação."}`

- **E-mail Já Cadastrado:**
  - **Status:** `409 Conflict`
  - **JSON:** `{"detail": "Já existe um usuário cadastrado com este e-mail."}`

- **Inscrição Duplicada:**
  - **Status:** `409 Conflict`
  - **JSON:** `{"detail": "Participante já está inscrito neste evento."}`

- **Evento Lotado (Sem Vagas):**
  - **Status:** `409 Conflict`
  - **JSON:** `{"detail": "Não existem vagas disponíveis para este evento."}`

---

## 8. Demonstração e Execução dos 12 Cenários de Teste

A aplicação inclui suíte automatizada cobrindo rigorosamente todos os 12 cenários exigidos pela avaliação:

1. **Cadastro de um usuário** (`POST /usuarios/`)
2. **Verificação de que a senha foi armazenada como hash** (consulta direta ao SQLite confirmando hash Argon2)
3. **Tentativa de cadastro com e-mail duplicado** (HTTP 409 Conflict)
4. **Autenticação com credenciais válidas** (HTTP 200 OK + JWT)
5. **Tentativa de autenticação com credenciais inválidas** (HTTP 401 Unauthorized)
6. **Acesso a uma rota protegida sem token** (HTTP 401 Unauthorized)
7. **Acesso a uma rota protegida com token válido** (HTTP 201 Created)
8. **Acesso com token inválido ou expirado** (HTTP 401 Unauthorized)
9. **Tentativa de operação administrativa por usuário comum** (HTTP 403 Forbidden)
10. **Execução de operação administrativa por administrador** (HTTP 200/201/204)
11. **Consulta dos dados do usuário autenticado** (`GET /auth/me`)
12. **Verificação da continuidade de regras e relatórios da APS 3** (vagas, duplicidade e relatórios consolidados)

### Como Executar os Testes

#### Opção A — Executar o Script Visual dos 12 Cenários:
Mostra em tempo real as requisições, payloads, status HTTP e respostas JSON:
```bash
python run_cenarios.py
```

#### Opção B — Executar a Suíte Oficial com Pytest:
```bash
pytest -v
```

---

## 9. Repositório no GitHub

O código-fonte completo deste projeto encontra-se versionado e atualizado no seguinte repositório público:
- **Link do Repositório:** [https://github.com/edududz/APS4_back-end.git](https://github.com/edududz/APS4_back-end.git)
