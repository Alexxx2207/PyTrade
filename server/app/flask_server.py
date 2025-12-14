
from datetime import datetime
from decimal import Decimal
from typing import Iterable
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask import Flask, jsonify, request
from flask_cors import CORS

from app.price_generator import register_price_update_callback, start_price_generation

from app.services.instruments import load_instrument_price_history
from app.models.instrument import InstrumentNameEnum
from app.models.instrument_price import InstrumentPrice
from app.utils.tick_time_converter import Tick, minute_bars_from_ticks
from app.services.hurst_exponent import hurst_exponent_minutes_rs_multiprocessed
from app.services.permutation_entropy import permutation_entropy_minutes_multiprocessed

app = Flask("PyTrade API")


CORS(
    app, 
    resources={r"/*": {"origins": "http://localhost:5173"}}, 
    supports_credentials=True,
)

socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    logger=True,
                    async_mode="threading",
                    engineio_logger=True)

connected_clients: set[str] = set()


@app.route("/instruments/<name>", methods=["GET"])
def getInstrumentPriceHistory(name: str):
    try:
        minutes = int(request.args.get("minutes", 100))
    except ValueError:
        return jsonify({"error": "minutes must be an integer"}), 400

    try:
        result = load_instrument_price_history(name, minutes)
    
    except ValueError as e:
        status = 404 if "Unknown instrument" in str(e) else 400
        return jsonify(e), status
    
    return jsonify(result)


@app.route("/instruments/<name>/hurst", methods=["GET"])
def getHurstExponent(name:str):
    try:
        minutes = int(request.args.get("minutes", 100))
        workers = int(request.args.get("workers", 100))
    except ValueError:
        return jsonify({"error": "minutes must be an integer"}), 400

    result = load_instrument_price_history(name, minutes)
    
    ticksIterable: Iterable[Tick] = sorted([
        (datetime.fromtimestamp(tick.timestamp), tick.price) for tick in result
    ])
    
    try:
        minutesClosePrice = [bar.close for bar in minute_bars_from_ticks(ticksIterable, fill_missing_minutes=False)]
        hurst_coefficient = hurst_exponent_minutes_rs_multiprocessed(minutesClosePrice, num_workers=workers)
    except Exception as e:
        return jsonify(str(e)), 400

    return jsonify(hurst_coefficient)


@app.route("/instruments/<name>/permutation-entropy", methods=["GET"])
def getPermutationEntropy(name: str):
    try:
        minutes = int(request.args.get("minutes", 100))
        workers = int(request.args.get("workers", 100))
    except ValueError:
        return jsonify({"error": "minutes must be an integer"}), 400

    result = load_instrument_price_history(name, minutes)
    
    ticksIterable: Iterable[Tick] = sorted([
        (datetime.fromtimestamp(tick.timestamp), tick.price) for tick in result
    ])
    
    try:
        minutesClosePrice = [bar.close for bar in minute_bars_from_ticks(ticksIterable, fill_missing_minutes=False)]
        hurst_coefficient = permutation_entropy_minutes_multiprocessed(minutesClosePrice, workers=workers)
    except Exception as e:
        return jsonify(str(e)), 400

    return jsonify(hurst_coefficient)


@socketio.on("subscribe")
def handle_subscribe(data):
    instrument = data.get("instrument", "ES")
    print(instrument)
    join_room(instrument)
    
    print("rooms:", rooms())


@socketio.on("unsubscribe")
def handle_unsubscribe(data):
    instrument = data.get("instrument", "a")
    leave_room(instrument)


def emit_price_update(symbol: InstrumentNameEnum, p: InstrumentPrice):
    socketio.emit(
        "price",
        {
            "price": float(p.price),
            "timestamp": int(p.created_at.timestamp()),
        },
        namespace="/",
        to=str(symbol.value)
    )


if __name__ == "__main__":
    register_price_update_callback(emit_price_update)
    
    start_price_generation()
    
    socketio.run(app, host="127.0.0.1", port=5000, debug=True, use_reloader=False)