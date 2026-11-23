from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from schema.usuario_schema import UsuarioCreate, UsuarioResponse
from service.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(usuario_in: UsuarioCreate, db: Session = Depends(get_db)):
    """Rota pública para cadastro de novos usuários comuns."""
    return UsuarioService.cadastrar_usuario(db, usuario_in)
