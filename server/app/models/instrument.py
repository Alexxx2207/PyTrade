from enum import Enum
from typing import Literal
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, Enum as SAEnum
from app.db.db import Base

class InstrumentNameEnum(str, Enum):
    ES = "ES"
    NQ = "NQ"
    YM = "YM"


class Instrument(Base):
    __tablename__ = "instruments"
    
    id:  Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[InstrumentNameEnum] = mapped_column(SAEnum(InstrumentNameEnum, name="instrument_name_enum"), unique=True, index=True)
    
    prices = relationship(
        "InstrumentPrice",
        back_populates="instrument",
        cascade="all, delete-orphan",
    )