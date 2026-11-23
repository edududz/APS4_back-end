from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from model.usuario import Usuario
from schema.usuario_schema import UsuarioCreate
from security.security import hash_password

class UsuarioService:
    @staticmethod
    def cadastrar_usuario(db: Session, usuario_in: UsuarioCreate) -> Usuario:
        """Cadastra um novo usuário com perfil 'usuario' e senha criptografada em Argon2.
        Valida e-mail duplicado (409 Conflict).
        """
        email_normalizado = usuario_in.email.strip().lower()
        existente = db.query(Usuario).filter(Usuario.email == email_normalizado).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário cadastrado com este e-mail."
            )

        senha_criptografada = hash_password(usuario_in.senha)
        novo_usuario = Usuario(
            nome=usuario_in.nome.strip(),
            email=email_normalizado,
            senha_hash=senha_criptografada,
            perfil="usuario"
        )
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario

    @staticmethod
    def consultar_por_id(db: Session, user_id: int) -> Usuario:
        """Busca usuário pelo identificador."""
        usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        return usuario
