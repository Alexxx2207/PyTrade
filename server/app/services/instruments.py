from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import time
from typing import List
from app.db.db import SessionLocal
from app.models.instrument import Instrument, InstrumentNameEnum
from app.models.instrument_price import InstrumentPrice

@dataclass
class ReturnType:
    price: float
    timestamp: int
    
    def __iter__(self):
        return iter((self.price, self.timestamp))
    
    def to_dict(self):
        return {
            "price": self.price,
            "timestamp": self.timestamp
        }


def load_instrument_price_history(name: str, minutes: int) -> List[ReturnType]:
    
    # uncomment to show multithreading - selector
    # time.sleep(minutes)
    
    if minutes <= 0:
        raise ValueError(f"minutes must be positive")

    try:
        instrument_name = InstrumentNameEnum(name)
    except ValueError:
        raise ValueError(f"Unknown instrument: {name}")

    with SessionLocal() as db:
        instrument = (
            db.query(Instrument)
            .filter(Instrument.name == instrument_name)
            .first()
        )

        if instrument is None:
            raise ValueError(f"Instrument {name} not found in DB")

        lookback_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        prices = (
            db.query(InstrumentPrice)
            .filter(
                InstrumentPrice.instrument_id == instrument.id,
                InstrumentPrice.created_at >= lookback_time
            )
            .order_by(InstrumentPrice.created_at.desc())
            .all()
        )

    return [
        ReturnType(float(p.price), int(p.created_at.timestamp()))
        for p in prices
    ]