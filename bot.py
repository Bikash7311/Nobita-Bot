
import requests
import json
import time
import os
import sqlite3
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
DB_FILE = "bot_database.db"

# Ek acchi si banner image ka link (Aap is URL ko apni kisi bhi image link se badal sakte hain)
WELCOME_BANNER = "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&auto=format&fit=crop"

user_states = {}

# =========================================
# DATABASE FUNCTIONS (SQLite)
# =========================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        referrer_id INTEGER,
                        referred_id INTEGER UNIQUE,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def get_referral_count(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def add_referral(referrer_id, referred_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, referred_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def is_already_referred(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM referrals WHERE referred_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

# =========================================
# PROGRESS BAR
# =========================================
def make_progress_bar(count, max_val=5):
    if count > max_val: count = max_val
    filled = "🟩" * count
    empty = "⬜" * (max_val - count)
    return f"{filled}{empty} ({count}/{max_val})"

# =========================================
# TELEGRAM API METHODS
# =========================================
def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = API_URL + "/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup: payload["reply_markup"] = json.dumps(reply_markup)
    if parse_mode: payload["parse_mode"] = parse_mode
    try: requests.post(url, data=payload, timeout=10)
    except: pass

def send_photo(chat_id, photo_url, caption, reply_markup=None, parse_mode=None):
    url = API_URL + "/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption}
    if reply_markup: payload["reply_markup"] = json.dumps(reply_markup)
    if parse_mode: payload["parse_mode"] = parse_mode
    try: requests.post(url, data=payload, timeout=10)
    except: pass

def answer_callback_query(callback_query_id, text):
    url = API_URL + "/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id, "text": text}
    try: requests.post(url, data=payload, timeout=10)
    except: pass

def is_user_joined(user_id):
    try:
        url = API_URL + "/getChatMember"
        params = {"chat_id": CHANNEL_USERNAME, "user_id": user_id}
        response = requests.get(url, params=params, timeout=10).json()
        if response.get("ok") and response["result"]["status"] in ["member", "administrator", "creator"]:
            return True
        return False
    except: return False

# =========================================
# PREMIUM INLINE KEYBOARDS
# =========================================
def get_join_keyboard():
    join_link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
    return {
        "inline_keyboard": [
            [{"text": "📢 Join Our Channel", "url": join_link}],
            [{"text": "🔄 Check Membership", "callback_data": "check_join"}]
        ]
    }

def get_premium_menu():
    return {
        "inline_keyboard": [
            [{"text": "📱 Phone Lookup Engine", "callback_data": "phone_lookup"}],
            [{"text": "👥 My Referrals & Invite Link", "callback_data": "my_referrals"}]
        ]
    }

def get_back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔙 Back To Menu", "callback_data": "back_to_menu"}]
        ]
    }

# =========================================
# CORE CORE BOT LOGIC
# =========================================
def handle_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    user_text = message.get("text", "").strip()
    bot_username = "Nobita_infoo_bot"

    if not is_user_joined(user_id):
        send_message(chat_id, "⚠️ <b>Access Denied!</b>\n\nBot ko use karne ke liye aapko hamare official channel ko join karna hoga. Niche diye gaye button par click karke join karein:", reply_markup=get_join_keyboard(), parse_mode="HTML")
        return

    if user_text.startswith("/start"):
        parts = user_text.split(" ")
        if len(parts) > 1:
            try:
                referrer_id = int(parts[1])
                if referrer_id != user_id and not is_already_referred(user_id):
                    if add_referral(referrer_id, user_id):
                        current_refs = get_referral_count(referrer_id)
                        send_message(referrer_id, f"🎉 <b>New Referral Milestone!</b>\n\nAapke link se ek user ne join kiya hai.\nTotal Referrals: {current_refs}/{REQUIRED_REFERRALS}", parse_mode="HTML")
            except: pass

        welcome_text = (
            f"⚡ <b>WELCOME TO NOBITA OSINT BOT v2.0</b> ⚡\n\n"
            f"यह एक एडवांस इंटेलिजेंस ट्रैकिंग बोट है। फीचर्स को अनलॉक करने के लिए नीचे दिए गए बटन्स का उपयोग करें।\n\n"
            f"⚠️ <b>Requirement:</b> {REQUIRED_REFERRALS} Friends Invite"
        )
        send_photo(chat_id, WELCOME_BANNER, welcome_text, reply_markup=get_premium_menu(), parse_mode="HTML")
        user_states[chat_id] = "idle"
        return

    if user_states.get(chat_id) == "awaiting_phone":
        if user_text.isdigit() and len(user_text) == 10:
            # Phone Lookup logic
            if not user_text.startswith('+'): user_text = "+91" + user_text
            try:
                parsed_number = phonenumbers.parse(user_text, None)
                location = geocoder.description_for_number(parsed_number, "en") or "Unknown State"
                operator = carrier.name_for_number(parsed_number, "en") or "Unknown Operator"
                res_text = f"🔍 <b>TARGET INFO FOUND</b>\n\n📞 <b>Number:</b> {user_text}\n🏢 <b>Operator:</b> {operator}\n📍 <b>Location:</b> {location}\n⚙️ <b>Database:</b> Local OSINT Core"
            except:
                res_text = "❌ Error processing number."
            send_message(chat_id, res_text, reply_markup=get_back_keyboard(), parse_mode="HTML")
            user_states[chat_id] = "idle"
        else:
            send_message(chat_id, "❌ Invalid number! Kripya 10-digit mobile number bhein.")
        return

def handle_callback(callback):
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    user_id = callback["from"]["id"]
    data = callback["data"]
    bot_username = "Nobita_infoo_bot"

    if data == "check_join":
        if is_user_joined(user_id):
            answer_callback_query(callback_id, "✅ Thank you for joining!")
            send_message(chat_id, "🎉 Verification Successful! Use /start to open the premium menu.", reply_markup=get_premium_menu())
        else:
            answer_callback_query(callback_id, "❌ Aapne abhi tak join nahi kiya hai!")
        return

    if not is_user_joined(user_id):
        answer_callback_query(callback_id, "❌ Please join the channel first!")
        return

    if data == "my_referrals":
        my_count = get_referral_count(user_id)
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        p_bar = make_progress_bar(my_count, REQUIRED_REFERRALS)
        
        status_text = (
            f"👥 <b>ADVANCE REFERRAL DASHBOARD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>Live Progress:</b>\n{p_bar}\n\n"
            f"🔒 <b>System Access:</b> {'🔓 GRANTED (Unlocked)' if my_count >= REQUIRED_REFERRALS else '🔒 RESTRICTED (Locked)'}\n\n"
            f"🔗 <b>Your Personal Invite Link:</b>\n<code>{ref_link}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Tip: Share this link to group/channels to complete fast!</i>"
        )
        answer_callback_query(callback_id, "📊 Data Synced")
        send_message(chat_id, status_text, reply_markup=get_back_keyboard(), parse_mode="HTML")
        return

    if data == "phone_lookup":
        my_count = get_referral_count(user_id)
        if my_count < REQUIRED_REFERRALS:
            answer_callback_query(callback_id, "🔒 Feature Locked!")
            ref_link = f"https://t.me/{bot_username}?start={user_id}"
            p_bar = make_progress_bar(my_count, REQUIRED_REFERRALS)
            lock_message = (
                f"⛔ <b>ACCESS DENIED (LOCKED)</b>\n\n"
                f"Aapke paas is feature ka access nahi hai. Pehle 5 referrals poore karein.\n"
                f"📈 <b>Current Progress:</b> {p_bar}\n\n"
                f"🔗 <b>Invite Link:</b>\n<code>{ref_link}</code>"
            )
            send_message(chat_id, lock_message, reply_markup=get_back_keyboard(), parse_mode="HTML")
            return
        
        answer_callback_query(callback_id, "📱 Engine Active")
        send_message(chat_id, "📞 <b>🎯 OSINT ENGINE ACTIVE</b>\n\nKripya jis 10-digit mobile number ki details chahiye, wo yahan send karein:", parse_mode="HTML")
        user_states[chat_id] = "awaiting_phone"
        return

    if data == "back_to_menu":
        answer_callback_query(callback_id, "🔙 Main Menu")
        welcome_text = (
            f"⚡ <b>WELCOME TO NOBITA OSINT BOT v2.0</b> ⚡\n\n"
            f"Features ko use karne ke liye neeche diye gaye buttons par click karein."
        )
        send_photo(chat_id, WELCOME_BANNER, welcome_text, reply_markup=get_premium_menu(), parse_mode="HTML")
        user_states[chat_id] = "idle"
        return

# =========================================
# DUMMY SERVER FOR RENDER
# =========================================
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Premium Bot is Online!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), WebServer)
    server.serve_forever()

# =========================================
# MAIN POLLING LOOP
# =========================================
def bot_polling():
    offset = 0
    print("✅ Premium Bot Polling Started...")
    while True:
        try:
            response = requests.get(API_URL + "/getUpdates", params={"timeout": 30, "offset": offset}, timeout=35).json()
            if response.get("ok"):
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        handle_message(update["message"])
                    elif "callback_query" in update:
                        handle_callback(update["callback_query"])
        except: time.sleep(1)

if __name__ == "__main__":
    init_db()
    Thread(target=run_server, daemon=True).start()
    bot_polling()
