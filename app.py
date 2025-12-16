from flask import Flask, request, jsonify, render_template
from models import db, Sensor
import config

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(config)

db.init_app(app)

# membuat tabel otomatis
with app.app_context():
    db.create_all()

# ==========================
# 🔹 API ENDPOINT (JSON)
# ==========================

@app.route("/api/sensor", methods=["GET"])
def api_get_sensor():
    sensor = Sensor.query.all()
    data = [{"id": s.id, "organik": s.organik, "anorganik": s.anorganik, "created_at" : s.created_at} for s in sensor]
    return jsonify(data)

# ...existing code...
@app.route("/api/kirim", methods=["POST"])
def api_add_sensor():
    # accept JSON like {"value":"organik"} or {"value":"anorganik"},
    # or legacy {"organik":1} / {"anorganik":1}, or raw body "organik"
    payload = request.get_json(silent=True)
    raw_text = request.get_data(as_text=True).strip() or None

    kind = None
    if isinstance(payload, dict):
        if payload.get("value") in ("organik", "anorganik"):
            kind = payload.get("value")
        elif payload.get("organik") == 1:
            kind = "organik"
        elif payload.get("anorganik") == 1:
            kind = "anorganik"
    elif isinstance(payload, str):
        if payload in ("organik", "anorganik"):
            kind = payload

    if not kind and raw_text in ("organik", "anorganik"):
        kind = raw_text

    if kind not in ("organik", "anorganik"):
        return jsonify({"error": "invalid payload, expected 'organik' or 'anorganik'"}), 400

    # get latest counts (start from 0 if none)
    last = Sensor.query.order_by(Sensor.id.desc()).first()
    base_org = last.organik if last and last.organik is not None else 0
    base_anorg = last.anorganik if last and last.anorganik is not None else 0

    # apply increments: only the reported sensor increases by 1
    inc_org = 1 if kind == "organik" else 0
    inc_anorg = 1 if kind == "anorganik" else 0

    new_org = base_org + inc_org
    new_anorg = base_anorg + inc_anorg

    new_sensor = Sensor(organik=new_org, anorganik=new_anorg)
    db.session.add(new_sensor)
    db.session.commit()
    return jsonify({"message": "Sensor added", "received": kind, "organik": new_org, "anorganik": new_anorg})
# ...existing code...



# ==========================
# 🔹 FRONTEND HTML (TEMPLATES)
# ==========================

@app.route("/")
def home_page():
    return render_template("index.html")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
