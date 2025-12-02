
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from app.db.db import SessionLocal
from app.models.instrument import Instrument, InstrumentNameEnum
from app.models.instrument_price import InstrumentPrice
from app.price_generator import start_price_generation


app = Flask("PyTrade API")


CORS(
    app, 
    resources={r"/*": {"origins": "http://localhost:5173"}}, 
    supports_credentials=True
)


@app.route("/instruments/<name>", methods=["GET"])
def getInstrumentPriceHistory(name: str):
    """Return last N prices for an instrument, newest first.
        Query params: limit - number of latest prices - default 100
    """
    try:
        instrument_name = InstrumentNameEnum(name)
    except ValueError:
        return jsonify({"error": f"Unknown instrument: {name}"}), 400

    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    if limit <= 0:
        return jsonify({"error": "limit must be positive"}), 400

    with SessionLocal() as db:
        instrument = (
            db.query(Instrument)
            .filter(Instrument.name == instrument_name)
            .first()
        )

        if instrument is None:
            return (
                jsonify(
                    {"error": f"Instrument {instrument_name.value} not found in DB"}
                ),
                404,
            )

        prices = (
            db.query(InstrumentPrice)
            .filter(InstrumentPrice.instrument_id == instrument.id)
            .order_by(InstrumentPrice.created_at.desc())
            .limit(limit)
            .all()
        )

    result = {
        "instrument": instrument_name.value,
        "count": len(prices),
        "prices": [
            {
                "price": p.price,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in prices
        ],
    }
    return jsonify(result)


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_price_generation()
    app.run(debug=True)