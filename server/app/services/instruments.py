import time
from app.db.db import SessionLocal
from app.models.instrument import Instrument, InstrumentNameEnum
from app.models.instrument_price import InstrumentPrice

def load_instrument_price_history(name: str, ticks: int) -> dict:
    
    # for showing multithreading
    # time.sleep(ticks)
    
    try:
        instrument_name = InstrumentNameEnum(name)
    except ValueError:
        return {"error": f"Unknown instrument: {name}"}

    if ticks <= 0:
        return {"error": "ticks must be positive"}

    with SessionLocal() as db:
        instrument = (
            db.query(Instrument)
            .filter(Instrument.name == instrument_name)
            .first()
        )

        if instrument is None:
            return {"error": f"Instrument {name} not found in DB"}

        prices = (
            db.query(InstrumentPrice)
            .filter(InstrumentPrice.instrument_id == instrument.id)
            .order_by(InstrumentPrice.created_at.desc())
            .limit(ticks)
            .all()
        )

    return {
        "instrument": instrument_name.value,
        "count": len(prices),
        "prices": [
            {
                "price": float(p.price),
                "timestamp": int(p.created_at.timestamp()),
            }
            for p in prices
        ],
    }