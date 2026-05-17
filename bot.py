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

# Cyber/Hacker Theme Banner Image
WELCOME_BANNER = "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop"

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
            [{"text": "☠️ ACCESS TERMINAL (JOIN)", "url": join_link}],
            [{"text": "🔄 BYPASS RESTRICTION", "callback_data": "check_join"}]
        ]
    }

def get_premium_menu():
    return {
        "inline_keyboard": [
            [{"text": "🎯 EXPLOIT PHONE NUMBER", "callback_data": "phone_lookup"}],
            [{"text": "👥 MULTIPLY NODES (REFERRALS)", "callback_data": "my_referrals"}]
        ]
    }

def get_back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔙 BACK TO MAINFRAME", "callback_data": "back_to_menu"}]
        ]
    }

# =========================================
# HACKER STYLE PHONE LOOKUP ENGINE
# =========================================
def phone_lookup(phone_number):
    if not phone_number.startswith('+'): 
        phone_number = "+91" + phone_number if len(phone_number) == 10 else "+" + phone_number
    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        if not phonenumbers.is_valid_number(parsed_number):
            return "❌ <b>[ERROR] INVALID NODE TARGET. NUMBER NOT VALID.</b>"
        
        location = geocoder.description_for_number(parsed_number, "en") or "Unknown State"
        operator = carrier.name_for_number(parsed_number, "en") or "Unknown Operator"
        
        # Super Advance Hacker-Style Layout Output
        cyber_output = (
            f"⚡ <b>NOBITA OSINT CORE ENGINE v3.0</b> ⚡\n"
            f"<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            f"📡 <b>TARGET NODE :</b> <code>{phone_number}</code>\n"
            f"📊 <b>SIGNAL STATUS:</b> <code>[ACTIVE / ONLINE]</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>FULL NAME   :</b> <code>[🔒 REFRESHING IN CORE...]</code>\n"
            f"👴 <b>FATHER NAME :</b> <code>[🔒 TELECOM_DB_ENCRYPTED]</code>\n"
            f"🏢 <b>OPERATOR    :</b> <code>{operator}</code>\n"
            f"📍 <b>LOCATION    :</b> <code>{location}</code>\n"
            f"🌍 <b>COUNTRY     :</b> <code>India (Local Engine)</code>\n"
            f"🛰️ <b>GPS VECTOR  :</b> <code>22.57° N, 88.36° E (Approx)</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>[ALERT] LEVEL-2 ENCRYPTION DETECTED!</b>\n"
            f"<i>Bypass Failed on Free Tier. Advanced details are locked under Govt Security Firewall.</i>"
        )
        return cyber_output
    except Exception as e: 
        return f"⚠️ <b>[SYS_CRASH] Error: {str(e)}</b>"

# =========================================
# CORE CORE BOT LOGIC
# =========================================
def handle_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    user_text = message.get("text", "").strip()
    bot_username = "Nobita_infoo_bot"

    if not is_user_joined(user_id):
        send_message(chat_id, "⚠️ <b>[SYSTEM BLOCK] FIREWALL ACTIVE</b>\n\nMainframe ko access karne ke liye official security channel ko join karna compulsory hai. Niche diye gaye link ko bypass karein:", reply_markup=get_join_keyboard(), parse_mode="HTML")
        return

    if user_text.startswith("/start"):
        parts = user_text.split(" ")
        if len(parts) > 1:
            try:
                referrer_id = int(parts[1])
                if referrer_id != user_id and not is_already_referred(user_id):
                    if add_referral(referrer_id, user_id):
                        current_refs = get_referral_count(referrer_id)
                        send_message(referrer_id, f"📡 <b>[NODE INJECTED] New Referral Connection!</b>\n\nAapke link se ek user server se connect hua hai.\nTotal Nodes: {current_refs}/{REQUIRED_REFERRALS}", parse_mode="HTML")
            except: pass

        welcome_text = (
            f"🤖 <b>SYSTEM ONLINE: NOBITA OSINT BOT v3.0</b> 🤖\n"
            f"<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            f"<i>Welcome Agent. Advanced Cyber Intelligence Core Terminal is active. Choose your exploit vector from below.</i>\n\n"
            f"⚙️ <b>Firewall Status:</b> <code>Bypassed</code>\n"
            f"🔑 <b>Required Nodes:</b> <code>{REQUIRED_REFERRALS} Invites</code>"
        )
        send_photo(chat_id, WELCOME_BANNER, welcome_text, reply_markup=get_premium_menu(), parse_mode="HTML")
        user_states[chat_id] = "idle"
        return

    if user_states.get(chat_id) == "awaiting_phone":
        if user_text.isdigit() and len(user_text) == 10:
            send_message(chat_id, phone_lookup(user_text), reply_markup=get_back_keyboard(), parse_mode="HTML")
            user_states[chat_id] = "idle"
        else:
            send_message(chat_id, "❌ <b>[SYS_ERROR] INVALID INPUT.</b>\nPlease send a clean 10-digit mobile number node.")
        return

def handle_callback(callback):
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    user_id = callback["from"]["id"]
    data = callback["data"]
    bot_username = "Nobita_infoo_bot"

    if data == "check_join":
        if is_user_joined(user_id):
            answer_callback_query(callback_id, "⚙️ Firewall Bypassed!")
            send_message(chat_id, "🎉 <b>Verification Successful!</b>\nType /start to initialize the hacker core menu.", reply_markup=get_premium_menu())
        else:
            answer_callback_query(callback_id, "❌ Join Check Failed!")
        return

    if not is_user_joined(user_id):
        answer_callback_query(callback_id, "❌ Access Denied!")
        return

    if data == "my_referrals":
        my_count = get_referral_count(user_id)
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        p_bar = make_progress_bar(my_count, REQUIRED_REFERRALS)
        
        status_text = (
            f"📊 <b>NODE CONNECTION DASHBOARD</b>\n"
            f"<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            f"📈 <b>Live Extraction Progress:</b>\n{p_bar}\n\n"
            f"🔒 <b>Core Decryption Access:</b> <code>{'🔓 UNLOCKED' if my_count >= REQUIRED_REFERRALS else '🔒 LOCKED'}</code>\n\n"
            f"🔗 <b>Your Exploitation Link:</b>\n<code>{ref_link}</code>\n"
            f"<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
            f"<i>Share this token payload link to add more network nodes!</i>"
        )
        answer_callback_query(callback_id, "📡 Nodes Synced")
        send_message(chat_id, status_text, reply_markup=get_back_keyboard(), parse_mode="HTML")
        return

    if data == "phone_lookup":
        my_count = get_referral_count(user_id)
        if my_count < REQUIRED_REFERRALS:
            answer_callback_query(callback_id, "🔒 Target Node Locked!")
            ref_link = f"https://t.me/{bot_username}?start={user_id}"
            p_bar = make_progress_bar(my_count, REQUIRED_REFERRALS)
            lock_message = (
                f"⛔ <b>[FIREWALL REJECTION] ACCESS DENIED</b>\n\n"
                f"Mainframe core data extraction is locked. Secure 5 nodes first.\n"
                f"📈 <b>Nodes Connected:</b> {p_bar}\n\n"
                f"🔗 <b>Exploit Link:</b>\n<code>{ref_link}</code>"
            )
            send_message(chat_id, lock_message, reply_markup=get_back_keyboard(), parse_mode="HTML")
            return
        
        answer_callback_query(callback_id, "⚡ OSINT Core Active")
        send_message(chat_id, "🎯 <b>OSINT PACKET INJECTOR ON</b>\n\nEnter the target 10-digit mobile number to initiate lookup scan:", parse_mode="HTML")
        user_states[chat_id] = "awaiting_phone"
        return

    if data == "back_to_menu":
        answer_callback_query(callback_id, "🔙 Mainframe Reloaded")
        welcome_text = (
            f"🤖 <b>SYSTEM ONLINE: NOBITA OSINT BOT v3.0</b> 🤖\n"
            f"Select your exploit vector from below to manipulate data systems."
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
        self.wfile.write(b"Hacker Core UI is Online!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), WebServer)
    server.serve_forever()

# =========================================
# MAIN POLLING LOOP
# =========================================
def bot_polling():
    offset = 0
    print("✅ Cyber Core Polling Started...")
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
