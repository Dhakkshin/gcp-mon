import os
from flask import Flask, jsonify
from google.cloud import firestore

app = Flask(__name__)
db = firestore.Client()

# Env vars set by Cloud Build deployment
REGION = os.environ.get("REGION", "unknown")
SERVICE_URL = os.environ.get("K_SERVICE_URL")

def register_agent():
    """Register this agent in Firestore."""
    if SERVICE_URL:
        db.collection("agents").document(REGION).set({"url": SERVICE_URL})
        print(f"✅ Registered agent for {REGION}: {SERVICE_URL}")
    else:
        print("⚠️ SERVICE_URL not set, cannot register.")

@app.route("/ping")
def ping():
    return jsonify({"status": "alive", "region": REGION})

# Register once at startup
register_agent()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
