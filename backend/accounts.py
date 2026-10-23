"""Local account administration. Passwords are read privately, never as CLI arguments."""

import argparse
from getpass import getpass
from uuid import uuid4

from app.auth import passwords
from app.database import LoginSessionRow, ProjectRow, SessionLocal, UserRow
from sqlalchemy import delete, select, update


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["create", "reset-password", "disable", "assign-local-projects"]
    )
    parser.add_argument("username")
    args = parser.parse_args()
    username = args.username.strip().casefold()
    if not username or len(username) > 200:
        parser.error("Nome de usuário inválido.")
    with SessionLocal() as session:
        user = session.scalar(select(UserRow).where(UserRow.username == username))
        if args.command == "create" and user:
            parser.error("Conta já existe.")
        if args.command != "create" and not user:
            parser.error("Conta não encontrada.")
        if args.command in ("create", "reset-password"):
            password = getpass("Nova senha (mínimo 12 caracteres): ")
            if (
                len(password) < 12
                or len(password) > 1024
                or password != getpass("Repita a senha: ")
            ):
                parser.error("Senha curta, longa demais ou confirmação diferente.")
            if not user:
                user = UserRow(id=str(uuid4()), username=username, active=True, password_hash="")
                session.add(user)
            user.password_hash = passwords.hash(password)
            session.execute(delete(LoginSessionRow).where(LoginSessionRow.user_id == user.id))
        elif args.command == "disable":
            user.active = False
            session.execute(delete(LoginSessionRow).where(LoginSessionRow.user_id == user.id))
        else:
            count = session.query(ProjectRow).filter(ProjectRow.owner_id.is_(None)).count()
            if (
                input(f"Atribuir os {count} projetos locais à conta {username}? Digite ATRIBUIR: ")
                != "ATRIBUIR"
            ):
                parser.error("Atribuição cancelada.")
            session.execute(
                update(ProjectRow).where(ProjectRow.owner_id.is_(None)).values(owner_id=user.id)
            )
        session.commit()
    print("Operação concluída. Nenhuma senha ou token foi exibido.")


if __name__ == "__main__":
    main()
