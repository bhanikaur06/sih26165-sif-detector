import os

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def index():
    return jsonify(
        {
            "service": "sif-precursor-detection-api",
            "status": "ok",
            "endpoints": [
                "POST /api/classify",
                "GET /api/dashboard/summary",
            ],
        }
    )


@app.route("/api/classify", methods=["POST"])
def classify():
    payload = request.get_json(silent=True) or {}
    narrative = payload.get("narrative", "")
    return jsonify(
        {
            "sif_probability": 0.0,
            "sif_label": 0,
            "life_saving_rule": None,
        }
    )


@app.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    return jsonify(
        {
            "precursor_density_by_group": [
                {
                    "group": "Drilling",
                    "group_type": "activity",
                    "total_reports": 120,
                    "sif_count": 18,
                    "density": 0.15,
                },
                {
                    "group": "Well Servicing",
                    "group_type": "activity",
                    "total_reports": 80,
                    "sif_count": 6,
                    "density": 0.075,
                },
            ],
            "summary_stats": {
                "total_reports": 200,
                "sif_count": 24,
                "density": 0.12,
            },
            "rule_breakdown": [
                {"life_saving_rule": "Energy Isolation", "count": 9},
                {"life_saving_rule": "Line of Fire", "count": 7},
                {"life_saving_rule": "Work Authorisation", "count": 8},
            ],
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("BACKEND_PORT", "5001"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
