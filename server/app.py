
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask("PyTrade API")
CORS(
    app, 
    resources={r"/*": {"origins": "http://localhost:5173"}}, 
    supports_credentials=True
)

@app.route("/instruments/<name>", methods=["GET"])
def getInstrumentPriceHistory(name: str):
    return jsonify({"instrument": name})


if __name__ == "__main__":
    app.run(debug=True)