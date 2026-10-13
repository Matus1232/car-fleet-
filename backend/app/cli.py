"""Príkazy na správu aplikácie z terminálu.

Prvého admina nemá kto vytvoriť cez API (POST /users vyžaduje admina), preto existuje tento
príkaz. Spúšťa ho len ten, kto má prístup k serveru:

    python -m app.cli create-admin --email admin@firma.sk
    docker compose exec api python -m app.cli create-admin --email admin@firma.sk
"""

import argparse
import getpass
import sys

from pydantic import ValidationError
from sqlalchemy import select

from app.api.users import build_user
from app.db.session import SessionLocal
from app.models.user import Role, User
from app.schemas.user import UserCreate


def create_admin(email: str) -> None:
    # Heslo sa pýta interaktívne (a nevypisuje sa). Keby bolo argumentom príkazu,
    # ostalo by uložené v histórii terminálu a videli by ho aj iné procesy.
    password = getpass.getpass("Heslo: ")
    if password != getpass.getpass("Heslo znova: "):
        sys.exit("Heslá sa nezhodujú.")
    try:
        data = UserCreate(email=email, password=password, role=Role.ADMIN)
    except ValidationError as exc:
        # Len správy, bez zadaných hodnôt: tie by v sebe mohli mať heslo.
        sys.exit("Neplatné údaje: " + "; ".join(e["msg"] for e in exc.errors()))

    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == data.email)):
            sys.exit(f"Používateľ {data.email} už existuje.")
        db.add(build_user(data))
        db.commit()
    print(f"Admin {data.email} bol vytvorený.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("create-admin", help="vytvorí používateľa s rolou admin")
    admin.add_argument("--email", required=True)

    args = parser.parse_args()
    if args.command == "create-admin":
        create_admin(args.email)


if __name__ == "__main__":
    main()
