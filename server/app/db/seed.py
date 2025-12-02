from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.db import Base, engine, SessionLocal
from app.models.instrument import Instrument


INSTRUMENT_NAMES = [
    "ES",
    "NQ",
]


def seed_instruments(db: Session):
    for name in INSTRUMENT_NAMES:
        stmt = select(Instrument).where(Instrument.name == name)
        exists = db.execute(stmt).scalar_one_or_none()
        if not exists:
            db.add(Instrument(name=name))


def seed():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        seed_instruments(db)
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()
        
        
if __name__=="__main__":
    seed()
    