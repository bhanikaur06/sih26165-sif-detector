# Backend — SIF Precursor Detection API

Flask API serving the classifier, life-saving-rule tagger, and dashboard summary.
See root `CLAUDE.md` for the schema and API contract, and `backend/CLAUDE.md` for
track responsibilities.

## Running the dev server

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Server binds to `0.0.0.0:5001`, reachable at `http://127.0.0.1:5001` locally and
at your machine's LAN IP from other devices on the network. Port 5000 is
avoided because macOS ControlCenter (AirPlay Receiver) binds it by default.
Override the port with the `BACKEND_PORT` environment variable:

```bash
BACKEND_PORT=8000 python app.py
```

Debug mode (auto-reload + the interactive Werkzeug debugger) is **off** by
default. Since the server listens on all interfaces, leaving it on exposes
that debugger — which can execute arbitrary code — to anyone else on the same
network, so only turn it on for local troubleshooting on a trusted network:

```bash
FLASK_DEBUG=1 python app.py
```

CORS is enabled for all origins so the frontend can call it directly during
development.

## Endpoints

- `POST /api/classify` — body `{ "narrative": "<text>" }`
- `GET /api/dashboard/summary`

Both currently return hardcoded placeholder JSON. No model or data loading is
wired up yet — that comes with `train.py` and the artifacts in `models/`.
