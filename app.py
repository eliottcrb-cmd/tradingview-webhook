import os
import time
import hmac
import hashlib
import json
import logging

import requests
from flask import Flask, request, jsonify

# -------------------------------------------------
# Basic Flask app
# -------------------------------------------------
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# -------------------------------------------------
# Environment configuration
# -------------------------------------------------
# Set these in Render dashboard → Environment
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
COINBASE_API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE")

# Sandbox by default. If you ever go live, change this carefully.
COINBASE_BASE_URL = os.getenv(
    "COINBASE_BASE_URL",
    "https://api-public.sandbox.exchange.coinbase.com"
)

if not COINBASE_API_KEY or not COINBASE_API_SECRET or not COINBASE_API_PASSPHRASE:
    logging.warning("Coinbase API credentials are not fully set in environment variables.")


# -------------------------------------------------
# Coinbase Advanced signing helper
# -------------------------------------------------
def sign_request(timestamp: str, method: str, request_path: str, body: str) -> str:
    """
    Create CB-ACCESS-SIGN header value.
    """
    message = f"{timestamp}{method.upper()}{request_path}{body}".encode("utf-8")
    secret = COINBASE_API_SECRET.encode("utf-8")
    signature = hmac.new(secret, message, hashlib.sha256).digest()
    return signature.hex()


def coinbase_headers(method: str, request_path: str, body: dict) -> dict:
    timestamp = str(int(time.time()))
    body_str = json.dumps(body) if body else ""
    signature = sign_request(timestamp, method, request_path, body_str)

    return {
        "CB-ACCESS-KEY": COINBASE_API_KEY,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "CB-ACCESS-PASSPHRASE": COINBASE_API_PASSPHRASE,
        "Content-Type": "application/json"
    }


# -------------------------------------------------
# Order creation on Coinbase Advanced
# -------------------------------------------------
def place_coinbase_order(symbol: str, side: str, qty: str, order_type: str = "market"):
    """
    Place an order on Coinbase Advanced.
    symbol: e.g. 'SOL-USD'
    side: 'buy' or 'sell'
    qty: string quantity, e.g. '1.5'
    order_type: 'market' or 'limit'
    """
    request_path = "/api/v3/brokerage/orders"
    url = COINBASE_BASE_URL + request_path

    # Basic market order payload
    body = {
        "product_id": symbol,          # e.g. 'SOL-USD'
        "side": side.lower(),          # 'buy' or 'sell'
        "order_configuration": {
            "market_market_ioc": {
                "base_size": qty       # quantity in base asset (e.g. SOL)
            }
        }
    }

    headers = coinbase_headers("POST", request_path, body)

    logging.info(f"Placing Coinbase order: {body}")
    response = requests.post(url, headers=headers, json=body, timeout=10)

    try:
        data = response.json()
    except Exception:
        data = {"raw_text": response.text}

    logging.info(f"Coinbase response status: {response.status_code}")
    logging.info(f"Coinbase response body: {data}")

    return response.status_code, data


# -------------------------------------------------
# Webhook endpoint for TradingView
# -------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    """
    TradingView → Render → Coinbase Advanced
    Expected JSON payload example (SOL):

    {
      "symbol": "SOL-USD",
      "side": "buy",
      "qty": "1.0",
      "type": "market"
    }
    """
    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        logging.error(f"Failed to parse JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    logging.info(f"Incoming webhook payload: {data}")

    # Validate required fields
    required_fields = ["symbol", "side", "qty"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        msg = f"Missing required fields: {missing}"
        logging.error(msg)
        return jsonify({"error": msg}), 400

    symbol = data["symbol"]
    side = data["side"]
    qty = data["qty"]
    order_type = data.get("type", "market")

    # Basic sanity checks
    if side.lower() not in ["buy", "sell"]:
        msg = f"Invalid side: {side}"
        logging.error(msg)
        return jsonify({"error": msg}), 400

    try:
        float(qty)
    except ValueError:
        msg = f"Invalid qty (not a number): {qty}"
        logging.error(msg)
        return jsonify({"error": msg}), 400

    logging.info(
        f"Parsed order → symbol={symbol}, side={side}, qty={qty}, type={order_type}"
    )

    # Place order on Coinbase
    status_code, cb_response = place_coinbase_order(
        symbol=symbol,
        side=side,
        qty=str(qty),
        order_type=order_type
    )

    if 200 <= status_code < 300:
        return jsonify({
            "status": "ok",
            "coinbase_status": status_code,
            "coinbase_response": cb_response
        }), 200
    else:
        return jsonify({
            "status": "error",
            "coinbase_status": status_code,
            "coinbase_response": cb_response
        }), 502


# -------------------------------------------------
# Health check
# -------------------------------------------------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "alive", "message": "SOL webhook online"}), 200


# -------------------------------------------------
# Local run (Render will use: python app.py)
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
