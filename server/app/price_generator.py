from decimal import Decimal
from threading import Thread
import time
import random
from typing import Final

from sqlalchemy import select
from app.db.db import SessionLocal
from app.models.instrument import Instrument, InstrumentNameEnum
from app.models.instrument_price import InstrumentPrice


STARTING_PRICE: Final[dict[InstrumentNameEnum, Decimal]] = {
    InstrumentNameEnum.ES: Decimal(100),
    InstrumentNameEnum.NQ: Decimal(100) 
}

TICK_SIZE: Final[dict[InstrumentNameEnum, Decimal]] = {
    InstrumentNameEnum.ES: Decimal(0.25), 
    InstrumentNameEnum.NQ: Decimal(0.25) 
}

SLEEP_TIME: Final[int] = 5


def generate_price(instrument_id: int, instrument_name: InstrumentNameEnum, current_price: Decimal):
    while True:
        with SessionLocal() as db:
            try:
                ticks = round(current_price / TICK_SIZE[instrument_name])
                delta_ticks = int(round(random.gauss(mu=0, sigma=1)))
                new_ticks = ticks + delta_ticks
                current_price = new_ticks * TICK_SIZE[instrument_name]
                
                db.add(InstrumentPrice(instrument_id=instrument_id, price=current_price))
                db.commit()
            except Exception as e:
                print(e)
                db.rollback()
        time.sleep(SLEEP_TIME)


def start_price_generation(instrument_name: InstrumentNameEnum):
    with SessionLocal() as db:
        instrument_stmt = select(Instrument).where(Instrument.name == instrument_name)
        instrument = db.scalars(instrument_stmt).first()
        
        if instrument is None:
            raise Exception("Instrument with such name does not exist to start price generation for it")
        
        current_price_stmt = (
            select(InstrumentPrice.price)
            .where(InstrumentPrice.instrument_id == instrument.id)
            .order_by(InstrumentPrice.created_at.desc())
        )
        current_price = db.scalars(current_price_stmt).first()
        
        if current_price is None:
            current_price = STARTING_PRICE[instrument_name]
        
    thread = Thread(target=generate_price, args=(instrument.id, instrument.name, current_price), daemon=True)
    thread.start()