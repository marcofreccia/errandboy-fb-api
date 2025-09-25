import os
import time
import hashlib
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configura questi valori con il tuo store
ECWID_STORE_ID = '29517085'
ECWID_SECRET_TOKEN = 'secret_sCWKvQc4Ta3exmxdrBUZCYwib6TgTC9Q'
RAILWAY_FB_API = 'https://errandboy-fb-api-production.up.railway.app/fb-event'

def hash_sha256(val):
    if isinstance(val, list):
        return [hashlib.sha256(str(v).encode('utf-8')).hexdigest() for v in val]
    if val is None:
        return None
    return hashlib.sha256(str(val).encode('utf-8')).hexdigest()

def get_ecwid_orders():
    url = f"https://app.ecwid.com/api/v3/{ECWID_STORE_ID}/orders"
    headers = {"Authorization": f"Bearer {ECWID_SECRET_TOKEN}"}
    resp = requests.get(url, headers=headers)
    return resp.json().get("items", [])

def forward_order_to_facebook(order):
    name = order.get("billingPerson", {}).get("name", "")
    first_name = name.split()[0] if name else ""
    last_name = name.split()[-1] if name and len(name.split()) > 1 else ""

    event_data = {
        "event_name": "Purchase",
        "event_time": int(time.time()),
        "user_data": {
            "em": [order.get("email", "")],
            "fn": [first_name],
            "ln": [last_name],
            "ph": [order.get("billingPerson", {}).get("phone", "")]
        },
        "custom_data": {
            "currency": order.get("totalCurrency", "EUR"),
            "value": order.get("total", 0),
            "content_ids": [str(p.get("productId")) for p in order.get("items", [])],
            "content_type": "product"
        },
        "action_source": "website"
    }
    resp = requests.post(RAILWAY_FB_API, json=event_data)
    try:
        return resp.json()
    except Exception:
        return {"error": "BAD RESPONSE", "body": resp.text}

@app.route("/poll-ecwid-orders", methods=["GET"])
def poll_and_forward():
    orders = get_ecwid_orders()
    results = []
    for order in orders:
        fb_resp = forward_order_to_facebook(order)
        results.append({
            "order_id": order.get("id"),
            "fb_response": fb_resp
        })
    return jsonify(results)

@app.route("/")
def home():
    return "Ecwid Conversion API integration live!"

if __name__ == "__main__":
    app.run(debug=True)
