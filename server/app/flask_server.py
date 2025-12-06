
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from app.price_generator import start_price_generation

from app.services.instruments import load_instrument_price_history

app = Flask("PyTrade API")


CORS(
    app, 
    resources={r"/*": {"origins": "http://localhost:5173"}}, 
    supports_credentials=True
)


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


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_price_generation()
    app.run(debug=True)