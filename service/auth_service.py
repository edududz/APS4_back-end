from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from model.usuario import Usuario
from schema.usuario_schema import LoginRequest, TokenResponse
from security.security import verify_password, create_access_token

class AuthService:
    @staticmethod
    def autenticar(db: Session, login_in: LoginRequest) -> TokenResponse:
        """Autentica o usuário com e-mail e senha.
        Se credenciais inválidas, retorna 401 sem revelar se o erro foi no e-mail ou na senha.
        Gera token JWT contendo ID e perfil do usuário.
        """
        email_normalizado = login_in.email.strip().lower()
        usuario = db.query(Usuario).filter(Usuario.email == email_normalizado).first()

        if not usuario or not verify_password(login_in.senha, usuario.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos."
            )

        # Informações mínimas e necessárias para identificação e autorização
        token_data = {
            "sub": str(usuario.id),
            "email": usuario.email,
            "perfil": usuario.perfil
        }
        access_token = create_access_token(data=token_data)
        return TokenResponse(access_token=access_token, token_type="bearer")
