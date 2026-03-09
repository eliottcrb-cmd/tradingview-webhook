from flask import Flask, request, jsonify

app = Flask(__name__)

@app.post("/webhook")
def webhook():
    data = request.json

    # Heartbeat
    if data.get("heartbeat"):
        print("Heartbeat received")
        return jsonify({"status": "alive"})

    print("Trading signal received:", data)

    # TODO: Add Coinbase logic here

    return jsonify({"status": "ok"})

@app.get("/")
def home():
    return "Webhook is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
