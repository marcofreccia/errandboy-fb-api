from flask import Flask, request, jsonify
import requests
import time
import os

app = Flask(__name__)

# Route di test home - utile per verifica deploy
@app.route('/', methods=['GET'])
def home():
    return "API online - Custom Railway Deploy", 200

# Route Facebook event POST
@app.route('/fb-event', methods=['POST'])
def fb_event():
    data = request.json
    event_name = data.get('event_name', 'Purchase')
    event_time = int(time.time())
    user_data = data.get('user_data', {})  # es. { "em": "email_hash_sha256" }
    custom_data = data.get('custom_data', {})  # es. { "currency": "EUR", "value": 49.90 }
    payload = {
        "data": [{
            "event_name": event_name,
            "event_time": event_time,
            "user_data": user_data,
            "custom_data": custom_data,
            "action_source": "website"
        }],
        "access_token": os.getenv("ACCESS_TOKEN")
    }
    pixel_id = os.getenv("PIXEL_ID")
    url = f'https://graph.facebook.com/v19.0/{pixel_id}/events'
    res = requests.post(url, json=payload)
    return jsonify(res.json())

# Codice per debug locale, da commentare/rimuovere su Railway
if __name__ == '__main__':
    app.run(port=8080, debug=True)
