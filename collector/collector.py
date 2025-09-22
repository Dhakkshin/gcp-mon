from flask import Flask, jsonify
import requests
import time
from google.cloud import firestore

app = Flask(__name__)
db = firestore.Client()

def get_agent_urls():
    docs = db.collection("agents").stream()
    return [(doc.id, doc.to_dict()["url"]) for doc in docs]

def collect():
    urls = get_agent_urls()
    results = []

    for region, url in urls:
        try:
            start = time.time()
            resp = requests.get(f"{url}/ping", timeout=5)
            latency = round((time.time() - start) * 1000, 2)

            result = {
                "timestamp": firestore.SERVER_TIMESTAMP,
                "region": region,
                "url": url,
                "status": "success",
                "response": resp.json(),
                "latency_ms": latency,
            }

            db.collection("results").add(result)
            results.append(result)
        except Exception as e:
            result = {
                "timestamp": firestore.SERVER_TIMESTAMP,
                "region": region,
                "url": url,
                "status": "error",
                "error": str(e),
            }
            db.collection("results").add(result)
            results.append(result)

    return results

@app.route("/run", methods=["GET"])
def run_collection():
    results = collect()
    return jsonify({"status": "done", "results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
