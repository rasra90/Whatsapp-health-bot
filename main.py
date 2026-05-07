from flask import Flask, request
import requests
import os
import google.generativeai as genai

app = Flask(__name__)

# Config
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")

# Gemini Setup
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def get_health_tip(user_message):
    prompt = f"""
    Aap ek expert health advisor hain. User ne yeh message bheja hai: "{user_message}"
    Ek helpful, practical aur safe health tip do Hindi mein.
    Response 3-4 lines se zyada na ho.
    Agar message health se related nahi hai toh politely kehna ki main sirf health tips de sakta hoon.
    """
    response = model.generate_content(prompt)
    return response.text

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, headers=headers, json=data)

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if data.get("object") == "whatsapp_business_account":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                messages = change.get("value", {}).get("messages", [])
                for message in messages:
                    if message.get("type") == "text":
                        user_number = message["from"]
                        user_text = message["text"]["body"]
                        reply = get_health_tip(user_text)
                        send_whatsapp_message(user_number, reply)
    return "OK", 200

@app.route("/")
def home():
    return "Health Bot is Running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
