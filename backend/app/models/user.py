from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Predvolený názov, ktorý PostgreSQL dáva unique constraintu na stĺpci email.
EMAIL_UNIQUE = "users_email_key"


class Role(StrEnum):
    ADMIN = "admin"  # môže všetko: spravovať autá aj používateľov
    DRIVER = "driver"  # autá len číta


class User(Base):
    __tablename__ = "users"
    # Poistka priamo v databáze: iná rola sa neuloží, ani keby ju niekto zapísal mimo API.
    __table_args__ = (CheckConstraint("role IN ('admin', 'driver')", name="users_role_check"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    # Nikdy samotné heslo, len jeho Argon2 hash (obsahuje aj soľ a nastavenia algoritmu).
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
