from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from model.usuario import Usuario
from schema.usuario_schema import LoginRequest, TokenResponse, UsuarioResponse
from service.auth_service import AuthService
from security.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(login_in: LoginRequest, db: Session = Depends(get_db)):
    """Rota pública para autenticação de usuário e obtenção do token JWT."""
    return AuthService.autenticar(db, login_in)

@router.get("/me", response_model=UsuarioResponse, status_code=status.HTTP_200_OK)
def obter_usuario_logado(current_user: Usuario = Depends(get_current_user)):
    """Rota protegida para consultar os dados do usuário autenticado a partir do token JWT."""
    return current_user
