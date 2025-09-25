import os
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ECWID_STORE_ID = '29517085'
ECWID_SECRET_TOKEN = 'secret_sCWKvQc4Ta3exmxdrBUZCYwib6TgTC9Q'
RAILWAY_FB_API = 'https://errandboy-fb-api-production.up.railway.app/fb-event'

def get_ecwid(endpoint):
    url = f"https://app.ecwid.com/api/v3/{ECWID_STORE_ID}/{endpoint}"
    headers = {"Authorization": f"Bearer {ECWID_SECRET_TOKEN}"}
    r = requests.get(url, headers=headers)
    return r.json().get("items", [])

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
        billing = order.get("billingPerson", {})
        name = billing.get("name", "")
        first_name = name.split()[0] if name else ""
        last_name = name.split()[-1] if name and len(name.split()) > 1 else ""
        data = {
            "event_name": "Purchase",
            "event_time": int(time.time()),
            "user_data": {
                "em": [order.get("email", "")],
                "fn": [first_name],
                "ln": [last_name],
                "ph": [billing.get("phone", "")]
            },
            "custom_data": {
                "currency": order.get("totalCurrency", "EUR"),
                "value": order.get("total", 0),
                "content_ids": [str(i.get("productId")) for i in order.get("items", [])],
                "content_type": "product"
            },
            "action_source": "website"
        }
        results.append({"order_id": order.get("id"), "fb_response": forward_to_facebook(data)})
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
        data = {
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
        results.append({"cart_id": cart.get("id"), "fb_response": forward_to_facebook(data)})
    return jsonify(results)

@app.route("/poll-ecwid-leads", methods=["GET"])
def poll_leads():
    customers = get_ecwid("customers")
    results = []
    for cust in customers:
        name = cust.get("name", "")
        first_name = name.split()[0] if name else ""
        last_name = name.split()[-1] if name and len(name.split()) > 1 else ""
        data = {
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
        results.append({"customer_id": cust.get("id"), "fb_response": forward_to_facebook(data)})
    return jsonify(results)

@app.route("/poll-ecwid-viewcontent", methods=["GET"])
def poll_viewcontent():
    products = get_ecwid("products")
    results = []
    for prod in products:
        data = {
            "event_name": "ViewContent",
            "event_time": int(time.time()),
            "user_data": {
                # Qui puoi migliorare se hai dati cliente/sessione!
                "em": [prod.get("createdBy") or ""]
            },
            "custom_data": {
                "currency": prod.get("defaultDisplayedPriceFormatted", "EUR"),
                "content_ids": [str(prod.get("id"))],
                "content_type": "product"
            },
            "action_source": "website"
        }
        results.append({"product_id": prod.get("id"), "fb_response": forward_to_facebook(data)})
    return jsonify(results)

@app.route("/poll-ecwid-search", methods=["GET"])
def poll_search():
    # Ecwid non salva tutte le ricerche degli utenti lato API pubbliche!
    # Ma se hai logs/search custom, puoi adattare così:
    # Qui mostro un esempio statico che puoi adattare ai tuoi dati reali:
    search_events = [{"email": "ricerca@email.com", "search_string": "fertilizzante"}]
    results = []
    for evt in search_events:
        data = {
            "event_name": "Search",
            "event_time": int(time.time()),
            "user_data": {
                "em": [evt.get("email", "")]
            },
            "custom_data": {
                "search_string": evt.get("search_string", "")
            },
            "action_source": "website"
        }
        results.append({"search": evt.get("search_string"), "fb_response": forward_to_facebook(data)})
    return jsonify(results)

@app.route("/")
def home():
    return "Ecwid <-> Facebook Conversion API Bridge: /poll-ecwid-orders /poll-ecwid-carts /poll-ecwid-leads /poll-ecwid-viewcontent /poll-ecwid-search /fb-event"

if __name__ == "__main__":
    app.run(debug=True)
