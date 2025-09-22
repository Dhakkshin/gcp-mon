import os, time, requests, logging
from flask import Flask, jsonify
from google.cloud import bigquery
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
app = Flask(__name__)

# AGENTS env format: "region1=https://url1,region2=https://url2"
AGENTS_RAW = os.environ.get("AGENTS", "")
AGENTS = {}
if AGENTS_RAW:
    for pair in AGENTS_RAW.split(","):
        if not pair.strip(): continue
        try:
            region, url = pair.split("=", 1)
            AGENTS[region.strip()] = url.strip().rstrip("/") + "/ping"
        except Exception as e:
            logging.warning("Bad AGENTS entry: %s -> %s", pair, e)

BQ_TABLE = os.environ.get("BQ_TABLE", "photogrammetry-pipeline.latency.latencies")
bq = bigquery.Client()

@app.route("/run")
def run_test():
    logging.info("Starting ping round to %d targets", len(AGENTS))
    rows = []
    for region, url in AGENTS.items():
        start = time.time()
        latency = None
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                latency = (time.time() - start) * 1000.0
            else:
                logging.warning("Non-200 from %s: %s", region, r.status_code)
        except Exception as e:
            logging.warning("Ping to %s failed: %s", region, e)
        rows.append({
            "timestamp": datetime.utcnow().isoformat(),
            "source_region": "asia-south1",
            "target_region": region,
            "latency_ms": latency
        })
    logging.info("Inserting %d rows into BigQuery %s", len(rows), BQ_TABLE)
    errors = bq.insert_rows_json(BQ_TABLE, rows)
    if errors:
        logging.error("BigQuery insert errors: %s", errors)
    return jsonify({"insert_errors": errors, "results": rows})
