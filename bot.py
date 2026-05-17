import requests
import json
import time
import os
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
import phonenumbers
from phonenumbers import geocoder, carrier

# =========================================
# CONFIGURATION
# =========================================
BOT_TOKEN = "8892483341:AAHJYIv5ZwwYyDZv7DM1_acO6TNm_bFtbFo"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHANNEL_USERNAME = "@nobitaosint"
REQUIRED_REFERRALS = 5

user_states = {}
referral_db = {}
referred_users = {}

# =========================================
# DUMMY SERVER FOR RENDER FREE TIER
# =========================================
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is Running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), WebServer)
    print(f"🌍 Dummy Web Server started on port {port}")
    server.serve_forever()

# =========================================
# BOT FUNCTIONS
# =========================================
def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = API_URL + "/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup: payload["reply_markup"] = json.dumps(reply_markup)
    if parse_mode: payload["parse_mode"] = parse_mode
    try: requests.post(url, data=payload, timeout=10)
    except: pass

def get_main_keyboard():
    return {"keyboard": [[{"text": "📱 Phone Lookup"}], [{"text": "👥 My Referrals & Link"}]], "resize_keyboard": True}

def is_user_joined(user_id):
    try:
        url = API_URL + "/getChatMember"
        params = {"chat_id": CHANNEL_USERNAME, "user_id": user_id}
        response = requests.get(url, params=params, timeout=10).json()
        if response.get("ok") and response["result"]["status"] in ["member", "administrator", "creator"]:
            return True
        return False
    except: return False

def phone_lookup(phone_number):
    if not phone_number.startswith('+'):
        phone_number = "+91" + phone_number if len(phone_number) == 10 else "+" + phone_number
    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        if not phonenumbers.is_valid_number(parsed_number):
            return "❌ <b>Number valid nahi hai!</b>"
        location = geocoder.description_for_number(parsed_number, "en") or "Unknown State"
        operator = carrier.name_for_number(parsed_number, "en") or "Unknown Operator"
        return f"🔍 <b>INFO FOUND</b>\n\n📞 <b>Number:</b> {phone_number}\n🏢 <b>Operator:</b> {operator}\n📍 <b>Location:</b> {location}"
    except Exception as e: return f"⚠️ <b>Error: {str(e)}</b>"

def handle_update(update):
    try:
        if "message" not in update or "text" not in update["message"]: return
        chat_id = update["message"]["chat"]["id"]
        user_id = update["message"]["from"]["id"]
        user_text = update["message"]["text"].strip()
        bot_username = "Nobita_infoo_bot"

        if user_id not in referral_db: referral_db[user_id] = []

        if not is_user_joined(user_id):
            send_message(chat_id, f"👋 <b>Welcome</b>\n\n❌ Channel join karna zaroori hai:\n🔗 https://t.me/{CHANNEL_USERNAME.replace('@', '')}\n\n✅ Join karke /start karein.", parse_mode="HTML")
            return

        if user_text.startswith("/start"):
            parts = user_text.split(" ")
            if len(parts) > 1:
                try:
                    referrer_id = int(parts[1])
                    if referrer_id != user_id and user_id not in referred_users and referrer_id in referral_db:
                        if user_id not in referral_db[referrer_id]:
                            referral_db[referrer_id].append(user_id)
                            referred_users[user_id] = True
                            send_message(referrer_id, f"🎉 New friend joined! Referrals: {len(referral_db[referrer_id])}/{REQUIRED_REFERRALS}")
                except: pass
            send_message(chat_id, f"👋 <b>Welcome To Nobita Osint Info</b>\n\nBot use karne ke liye <b>{REQUIRED_REFERRALS} referrals</b> chahiye.", reply_markup=get_main_keyboard(), parse_mode="HTML")
            return

        if user_text == "👥 My Referrals & Link":
            my_count = len(referral_db.get(user_id, []))
            ref_link = f"https://t.me/{bot_username}?start={user_id}"
            send_message(chat_id, f"👥 <b>Stats:</b> {my_count}/{REQUIRED_REFERRALS}\n🔗 <b>Link:</b>\n<code>{ref_link}</code>", parse_mode="HTML")
            return

        if user_text == "📱 Phone Lookup":
            if len(referral_db.get(user_id, [])) < REQUIRED_REFERRALS:
                ref_link = f"https://t.me/{bot_username}?start={user_id}"
                send_message(chat_id, f"⛔ <b>Access Denied!</b>\nInvite {REQUIRED_REFERRALS - len(referral_db[user_id])} more friends:\n🔗 <code>{ref_link}</code>", parse_mode="HTML")
                return
            send_message(chat_id, "📞 Send 10 digit number:")
            user_states[chat_id] = "awaiting_phone"
            return

        if user_states.get(chat_id) == "awaiting_phone":
            if user_text.isdigit() and len(user_text) == 10:
                send_message(chat_id, phone_lookup(user_text), parse_mode="HTML")
                user_states[chat_id] = "idle"
            else: send_message(chat_id, "❌ Send valid 10 digit number.")
    except Exception as e: print(e)

def bot_polling():
    offset = 0
    print("✅ Bot Polling Started...")
    while True:
        try:
            response = requests.get(API_URL + "/getUpdates", params={"timeout": 30, "offset": offset}, timeout=35).json()
            if response.get("ok"):
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    handle_update(update)
        except: time.sleep(1)

if __name__ == "__main__":
    # Start Dummy Web Server in background thread
    Thread(target=run_server, daemon=True).start()
    # Start Bot
    bot_polling()
