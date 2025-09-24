import os
import hashlib
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

def hash_sha256(val):
    if isinstance(val, list):
        return [hashlib.sha256(str(v).encode('utf-8')).hexdigest() for v in val]
    if val is None:
        return None
    return hashlib.sha256(str(val).encode('utf-8')).hexdigest()

@app.route('/fb-event', methods=['POST'])
def fb_event():
    # 1. Ricevi payload
    data = request.get_json(force=True)
    user_data = data.get('user_data', {})

    # 2. Hash automatico dei dati richiesti da Meta (em, ph, fn, ln)
    for key in ['em', 'ph', 'fn', 'ln']:
        if key in user_data:
            user_data[key] = hash_sha256(user_data[key])

    # 3. Prepara il payload da inoltrare a Facebook Conversion API
    fb_payload = {
        "event_name": data.get("event_name"),
        "event_time": data.get("event_time"),
        "user_data": user_data,
        "custom_data": data.get("custom_data", {}),
        "action_source": data.get("action_source", "website")
    }

    access_token = os.environ['ACCESS_TOKEN']
    pixel_id = os.environ['PIXEL_ID']

    fb_url = f"https://graph.facebook.com/v18.0/{pixel_id}/events?access_token={access_token}"

    # 4. Inoltra l'evento a Facebook
    fb_data = {
        "data": [fb_payload]
    }
    fb_response = requests.post(fb_url, json=fb_data)
    fb_result = fb_response.json()

    # 5. Rispondi al client
    return jsonify({
        "sent_to_facebook": fb_data,
        "facebook_response": fb_result
    }), fb_response.status_code

# Optional: Home test
@app.route("/")
def home():
    return "API is running!"

# Flask launch in debug (per sviluppo locale)
if __name__ == "__main__":
    app.run(debug=True)
