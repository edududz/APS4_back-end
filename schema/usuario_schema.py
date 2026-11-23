from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional

class UsuarioCreate(BaseModel):
    """Schema para cadastro de usuário (POST /usuarios).
    Não aceita perfil, garantindo que novos cadastros comuns sejam sempre 'usuario'.
    """
    nome: str = Field(..., min_length=1, max_length=100, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="E-mail único para acesso")
    senha: str = Field(..., min_length=6, description="Senha do usuário (mínimo de 6 caracteres)")

class UsuarioResponse(BaseModel):
    """Schema de retorno do usuário.
    Nunca expõe a senha nem o hash da senha.
    """
    id: int
    nome: str
    email: str
    perfil: str

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    """Schema para requisição de login (POST /auth/login)."""
    email: EmailStr = Field(..., description="E-mail cadastrado")
    senha: str = Field(..., min_length=1, description="Senha do usuário")

class TokenResponse(BaseModel):
    """Schema de resposta após autenticação bem-sucedida."""
    access_token: str
    token_type: str = "bearer"
