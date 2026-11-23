from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from database import init_db, SessionLocal
from security.security import create_initial_admin
from controller.auth_controller import router as auth_router
from controller.usuario_controller import router as usuario_router
from controller.evento_controller import router as evento_router
from controller.participante_controller import router as participante_router
from controller.inscricao_controller import router as inscricao_router
from controller.relatorio_controller import router as relatorio_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa as tabelas do banco de dados na inicialização
    init_db()
    # Inicializa o usuário administrador padrão caso não exista
    db = SessionLocal()
    try:
        create_initial_admin(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="API de Gerenciamento de Eventos Acadêmicos - APS 4",
    description="API RESTful com autenticação JWT, controle de acesso baseado em perfis (RBAC), hash seguro de senhas com Argon2 e continuidade de eventos, participantes, inscrições e relatórios.",
    version="3.0.0",
    lifespan=lifespan
)

# Inclusão dos roteadores por domínio/responsabilidade
app.include_router(auth_router)
app.include_router(usuario_router)
app.include_router(evento_router)
app.include_router(participante_router)
app.include_router(inscricao_router)
app.include_router(relatorio_router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
