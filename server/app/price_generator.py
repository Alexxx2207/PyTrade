from decimal import Decimal
from threading import Lock, Thread
import time
import random
from typing import Callable, Final, Optional

from sqlalchemy import select
from app.db.db import SessionLocal
from app.models.instrument import Instrument, InstrumentNameEnum
from app.models.instrument_price import InstrumentPrice


PriceUpdateCallback = Callable[[InstrumentNameEnum, InstrumentPrice], None]
_price_update_callback: Optional[PriceUpdateCallback] = None


STARTING_PRICE: Final[dict[InstrumentNameEnum, Decimal]] = {
    InstrumentNameEnum.ES: Decimal(100),
    InstrumentNameEnum.NQ: Decimal(100) 
}

TICK_SIZE: Final[dict[InstrumentNameEnum, Decimal]] = {
    InstrumentNameEnum.ES: Decimal(0.25), 
    InstrumentNameEnum.NQ: Decimal(0.25) 
}

NEXT_TICK_SLEEP_TIME: Final[int] = 10
NEXT_AUTOREGRESSIVE_COEFFICIENT_MIN_SLEEP_TIME: Final[int] = 100
NEXT_AUTOREGRESSIVE_COEFFICIENT_MAX_SLEEP_TIME: Final[int] = 10000

AUTOREGRESSIVE_COEFFICIENT_LOWER_BOUND: Final[float] = -0.8
AUTOREGRESSIVE_COEFFICIENT_UPPER_BOUND: Final[float] = 0.8

autoregressive_coefficient = 0
_autoregressive_coefficient_lock = Lock()


def start_price_generation():
    start_autoregressive_coefficient_change(
            NEXT_AUTOREGRESSIVE_COEFFICIENT_MIN_SLEEP_TIME, 
            NEXT_AUTOREGRESSIVE_COEFFICIENT_MAX_SLEEP_TIME)
    start_price_generation_for_instrument(InstrumentNameEnum.ES)
    start_price_generation_for_instrument(InstrumentNameEnum.NQ)


def change_autoregressive_coefficient(min_seconds: int, max_seconds: int):
    global autoregressive_coefficient

    while True:
        new_phi = random.uniform(AUTOREGRESSIVE_COEFFICIENT_LOWER_BOUND, AUTOREGRESSIVE_COEFFICIENT_UPPER_BOUND)
        with _autoregressive_coefficient_lock:
            autoregressive_coefficient = new_phi
        
        time.sleep(random.uniform(min_seconds, max_seconds))


def start_autoregressive_coefficient_change(min_seconds: int, max_seconds: int):
    update_thread = Thread(target=change_autoregressive_coefficient, args=(min_seconds, max_seconds), daemon=True)
    update_thread.start()


def generate_autoregressive_tick(previous_tick_change: int) -> int:
    with _autoregressive_coefficient_lock:
        phi = autoregressive_coefficient

    probability_for_uptick = (1.0 + phi * previous_tick_change) * 0.5

    probability_for_uptick = max(0.0, min(1.0, probability_for_uptick))

    return 1 if random.random() < probability_for_uptick else -1


def calculate_new_price(
        current_price: Decimal,
        instrument_name: InstrumentNameEnum,
        previous_tick_change: int) -> tuple[Decimal, int]:
    ticks = int(current_price / TICK_SIZE[instrument_name])
    
    delta_ticks = generate_autoregressive_tick(previous_tick_change)

    new_ticks = ticks + delta_ticks
    
    return (new_ticks * TICK_SIZE[instrument_name], delta_ticks)


def generate_price(instrument_id: int, instrument_name: InstrumentNameEnum, current_price: Decimal) -> None:
    previous_tick_change: int = 1 if random.random() < 0.5 else -1
    
    while True:
        with SessionLocal() as db:
            try:
                current_price, previous_tick_change = (
                    calculate_new_price(current_price, instrument_name, previous_tick_change))
                
                new_price = InstrumentPrice(instrument_id=instrument_id, price=current_price)
                
                db.add(new_price)
                db.commit()
                
                if _price_update_callback is not None:
                    _price_update_callback(instrument_name, new_price)
            except Exception as e:
                print(e)
                db.rollback()
                
        time.sleep(NEXT_TICK_SLEEP_TIME)


def start_price_generation_for_instrument(instrument_name: InstrumentNameEnum) -> None:
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


def register_price_update_callback(cb: PriceUpdateCallback) -> None:
    global _price_update_callback
    _price_update_callback = cb