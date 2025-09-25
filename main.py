import os
import time
import hashlib
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ECWID_STORE_ID = '29517085'
ECWID_SECRET_TOKEN = 'secret_sCWKvQc4Ta3exmxdrBUZCYwib6TgTC9Q'
RAILWAY_FB_API = 'https://errandboy-fb-api-production.up.railway.app/fb-event'

def get_ecwid(endpoint):
    url = f"https://app.ecwid.com/api/v3/{ECWID_STORE_ID}/{endpoint}"
    headers = {"Authorization": f"Bearer {ECWID_SECRET_TOKEN}"}
    resp = requests.get(url, headers=headers)
    return resp.json().get("items", [])

def forward_to_facebook(event_data):
    resp = requests.post(RAILWAY_FB_API, json=event_data)
    try:
        return resp.json()
    except Exception:
        return {"error": "BAD RESPONSE", "body": resp.text}

@app.route("/poll-ecwid-orders", methods=["GET"])
def poll_orders():
    orders = get_ecwid("orders")
    results = []
    for order in orders:
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
        results.append({"order_id": order.get("id"), "fb_response": forward_to_facebook(event_data)})
    return jsonify(results)

@app.route("/poll-ecwid-carts", methods=["GET"])
def poll_carts():
    carts = get_ecwid("carts")
    results = []
    for cart in carts:
        person = cart.get("billingPerson", {})
        name = person.get("name", "")
        first_name = name.split()[0] if name else ""
        last_name = name.split()[-1] if name and len(name.split()) > 1 else ""
        event_data = {
            "event_name": "AddToCart",
            "event_time": int(time.time()),
            "user_data": {
                "em": [cart.get("email", "")],
                "fn": [first_name],
                "ln": [last_name],
                "ph": [person.get("phone", "")]
            },
            "custom_data": {
                "currency": cart.get("currency", "EUR"),
                "value": cart.get("items", [{}])[0].get("price", 0) if cart.get("items") else 0,
                "content_ids": [str(i.get("productId")) for i in cart.get("items", [])],
                "content_type": "product"
            },
            "action_source": "website"
        }
        results.append({"cart_id": cart.get("id"), "fb_response": forward_to_facebook(event_data)})
    return jsonify(results)

@app.route("/poll-ecwid-leads", methods=["GET"])
def poll_leads():
    customers = get_ecwid("customers")
    results = []
    for cust in customers:
        name = cust.get("name", "")
        first_name = name.split()[0] if name else ""
        last_name = name.split()[-1] if name and len(name.split()) > 1 else ""
        event_data = {
            "event_name": "Lead",
            "event_time": int(time.time()),
            "user_data": {
                "em": [cust.get("email", "")],
                "fn": [first_name],
                "ln": [last_name],
                "ph": [cust.get("phone", "")]
            },
            "custom_data": {
                "lead_type": "newsletter"
            },
            "action_source": "website"
        }
        results.append({"customer_id": cust.get("id"), "fb_response": forward_to_facebook(event_data)})
    return jsonify(results)

@app.route("/")
def home():
    return "Ecwid Conversion API integration is live! /poll-ecwid-orders /poll-ecwid-carts /poll-ecwid-leads"

if __name__ == "__main__":
    app.run(debug=True)
