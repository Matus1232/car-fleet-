from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from app.models.user import Role


def normalize_email(value: str) -> str:
    """' Jan@Firma.SK ' -> 'jan@firma.sk', aby sa ten istý človek nedal vytvoriť dvakrát."""
    return value.strip().lower()


class UserRegister(BaseModel):
    """Čo posiela človek pri verejnej registrácii. Rola tu zámerne nie je: keby si ju mohol
    poslať sám, spravil by zo seba admina. Polia navyše (aj "role") Pydantic jednoducho zahodí.
    """

    # Na rozdiel od VehicleBase tu nie je str_strip_whitespace: heslo meniť nesmieme,
    # medzera na začiatku hesla je jeho platná súčasť.
    email: EmailStr
    # SecretStr sa pri výpise (print, logy) zobrazí ako '**********'. Skutočnú hodnotu
    # treba vyžiadať explicitne cez .get_secret_value(), takže heslo neunikne omylom.
    # Horná hranica chráni server: hashovať megabajtové "heslo" by trvalo zbytočne dlho.
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value):
        return normalize_email(value) if isinstance(value, str) else value


class UserCreate(UserRegister):
    """Účet, ktorý zakladá admin (POST /users) alebo príkaz v termináli: navyše určí rolu.

    Dedí z UserRegister, takže email a heslo majú tie isté pravidlá a píšu sa len raz.
    """

    role: Role = Role.DRIVER


class UserRead(BaseModel):
    """Čo o používateľovi API vracia. Heslo (ani jeho hash) tu zámerne nie je."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Role
    created_at: datetime


class Token(BaseModel):
    """Tvar odpovede, ktorý očakáva OAuth2 štandard (a tlačidlo Authorize v /docs)."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105  (typ tokenu, nie heslo)
