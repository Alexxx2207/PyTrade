
from decimal import Decimal
from flask_socketio import SocketIO, emit, join_room
from flask import Flask, jsonify, request
from flask_cors import CORS

from app.price_generator import register_price_update_callback, start_price_generation

from app.services.instruments import load_instrument_price_history
from app.models.instrument import InstrumentNameEnum
from app.models.instrument_price import InstrumentPrice

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
        ticks = int(request.args.get("ticks", 100))
    except ValueError:
        return jsonify({"error": "ticks must be an integer"}), 400

    result = load_instrument_price_history(name, ticks)
    
    if "error" in result:
        status = 400 if "Unknown instrument" in result["error"] else 404
        return jsonify(result), status
    
    return jsonify(result)


@socketio.on("subscribe")
def handle_subscribe(data):
    symbol = data.get("symbol", "ES")
    join_room(symbol)

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