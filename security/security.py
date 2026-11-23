import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy.orm import Session
from database import get_db

# Carrega variáveis de ambiente a partir do .env (se existir)
load_dotenv()

# Configurações de segurança e token JWT obtidas de variáveis de ambiente
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_padrao_desenvolvimento_aps4_segura_2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Configuração da biblioteca pwdlib com Argon2
password_hash = PasswordHash((Argon2Hasher(),))

def hash_password(password: str) -> str:
    """Gera o hash seguro da senha utilizando Argon2."""
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash armazenado."""
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Gera um token JWT com dados informados e tempo de expiração."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Extração de token Bearer via cabeçalho HTTP Authorization
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """Dependência para extrair e validar o token JWT e retornar o usuário autenticado."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (jwt.PyJWTError, ValueError, TypeError):
        raise credentials_exception

    from model.usuario import Usuario
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if usuario is None:
        raise credentials_exception

    return usuario

def require_admin(current_user=Depends(get_current_user)):
    """Dependência que verifica se o usuário autenticado possui perfil de administrador."""
    if current_user.perfil != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não possui permissão para executar esta operação."
        )
    return current_user

def create_initial_admin(db: Session) -> None:
    """Cria um usuário administrador inicial se nenhum existir no banco de dados.
    Configuração documentada e segura conforme requisito 3.1.
    """
    from model.usuario import Usuario
    admin_email = os.getenv("ADMIN_EMAIL", "admin@universidade.edu.br")
    admin_existente = db.query(Usuario).filter(Usuario.email == admin_email).first()
    if not admin_existente:
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_nome = os.getenv("ADMIN_NOME", "Administrador do Sistema")
        novo_admin = Usuario(
            nome=admin_nome,
            email=admin_email,
            senha_hash=hash_password(admin_pass),
            perfil="administrador"
        )
        db.add(novo_admin)
        db.commit()
