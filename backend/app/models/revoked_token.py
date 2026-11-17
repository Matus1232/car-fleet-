from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RevokedToken(Base):
    """Token, ktorý sa odhlásil. Hoci jeho podpis aj čas platnosti sú v poriadku, neprijmeme ho.

    JWT je "bezstavový": server si nepamätá, komu ho vydal, len overí podpis. Preto sa nedá
    jednoducho zrušiť. Riešením je zoznam zrušených tokenov (denylist). Pamätáme si len tie
    odhlásené a len kým by aj tak nevypršali, takže tabuľka ostáva malá.
    """

    __tablename__ = "revoked_tokens"

    # jti = jedinečné ID tokenu (pozri create_access_token). Primárny kľúč = rýchle hľadanie.
    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    # Po tomto čase by token neplatil ani tak, riadok sa potom môže zmazať.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
