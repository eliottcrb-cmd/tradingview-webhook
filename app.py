from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True) or {}

if data.get("type") == "heartbeat":
    return jsonify({"status": "alive"}), 200

required_fields = ["symbol", "side", "entry", "stop", "take_profit", "risk_percent"]
missing = [f for f in required_fields if f not in data]
if missing:
    return jsonify({
        "status": "error",
        "error": "missing_fields",
        "details": missing
    }), 400

symbol = data["symbol"]
side = data["side"].lower()
entry = float(data["entry"])
stop = float(data["stop"])
take_profit = float(data["take_profit"])
risk_percent = float(data["risk_percent"])

if side not in ["buy", "sell"]:
    return jsonify({"status": "error", "error": "invalid_side"}), 400

if entry == stop:
    return jsonify({"status": "error", "error": "entry_equals_stop"}), 400

account_balance = 10000.0
risk_amount = account_balance * (risk_percent / 100.0)
stop_distance = abs(entry - stop)

if stop_distance <= 0:
    return jsonify({"status": "error", "error": "invalid_stop_distance"}), 400

position_size = risk_amount / stop_distance

print("=== INCOMING TRADE SIGNAL ===")
print({
    "symbol": symbol,
    "side": side,
    "entry": entry,
    "stop": stop,
    "take_profit": take_profit,
    "risk_percent": risk_percent,
    "account_balance": account_balance,
    "risk_amount": risk_amount,
    "stop_distance": stop_distance,
    "position_size": position_size
})
print("=== END SIGNAL ===")

return jsonify({
    "status": "ok",
    "mode": "dry_run",
    "symbol": symbol,
    "side": side,
    "position_size": position_size
}), 200

    symbol = data["symbol"]
    side = data["side"].lower()
    entry = float(data["entry"])
    stop = float(data["stop"])
    take_profit = float(data["take_profit"])
    risk_percent = float(data["risk_percent"])

    if side not in ["buy", "sell"]:
        return jsonify({"status": "error", "error": "invalid_side"}), 400

    if entry == stop:
        return jsonify({"status": "error", "error": "entry_equals_stop"}), 400

    account_balance = 10000.0
    risk_amount = account_balance * (risk_percent / 100.0)
    stop_distance = abs(entry - stop)

    if stop_distance <= 0:
        return jsonify({"status": "error", "error": "invalid_stop_distance"}), 400

    position_size = risk_amount / stop_distance

    print("=== INCOMING TRADE SIGNAL ===")
    print({
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "stop": stop,
        "take_profit": take_profit,
        "risk_percent": risk_percent,
        "account_balance": account_balance,
        "risk_amount": risk_amount,
        "stop_distance": stop_distance,
        "position_size": position_size
    })
    print("=== END SIGNAL ===")

    return jsonify({
        "status": "ok",
        "mode": "dry_run",
        "symbol": symbol,
        "side": side,
        "position_size": position_size
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
