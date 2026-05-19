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
# CONFIGURATION (Settings)
# =========================================
BOT_TOKEN = "8892483341:AAHExQb-NuUs1OuqiaaCAgCuDFJZGPH6m0o"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHANNEL_USERNAME = "@nobitaosint"
REQUIRED_REFERRALS = 5
DB_FILE = "bot_database.db"

# Ek acchi tech banner image
WELCOME_BANNER = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop"

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
# PROGRESS BAR (Simple & Neat)
# =========================================
def make_progress_bar(count, max_val=5):
    if count > max_val: count = max_val
    filled = "🟩" * count
    empty = "⬜" * (max_val - count)
    return f"{filled}{empty} ({count}/{max_val} Friends Joined)"

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
# EASY & PROFESSIONAL INLINE KEYBOARDS
# =========================================
def get_join_keyboard():
    join_link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
    return {
        "inline_keyboard": [
            [{"text": "📢 Join Our Telegram Channel", "url": join_link}],
            [{"text": "✅ Join Kar Liya - Check Karein", "callback_data": "check_join"}]
        ]
    }

def get_premium_menu():
    return {
        "inline_keyboard": [
            [{"text": "🔍 Number Details Nikalein", "callback_data": "phone_lookup"}],
            [{"text": "👥 My Referrals & Invite Link", "callback_data": "my_referrals"}]
        ]
    }

def get_back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔙 Back To Main Menu", "callback_data": "back_to_menu"}]
        ]
    }

# =========================================
# CLEAN & FANCY DATA OUTPUT
# =========================================
def phone_lookup(phone_number):
    if not phone_number.startswith('+'): 
        phone_number = "+91" + phone_number if len(phone_number) == 10 else "+" + phone_number
    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        if not phonenumbers.is_valid_number(parsed_number):
            return "❌ <b>[Galat Number]</b> Kripya sahi 10-digit ka number bhejiye."
        
        location = geocoder.description_for_number(parsed_number, "en") or "Unknown State"
        operator = carrier.name_for_number(parsed_number, "en") or "Unknown Operator"
        
        # Clean and Professional Layout
        output = (
            f"🎯 <b>NOBITA OSINT SEARCH RESULT</b> 🎯\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📞 <b>Mobile Number:</b> <code>{phone_number}</code>\n"
            f"🏢 <b>SIM Company:</b> <code>{operator}</code>\n"
            f"📍 <b>State / Location:</b> <code>{location}</code>\n"
            f"🌍 <b>Country:</b> <code>India</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Full Name:</b> <code>[🔒 Server Encrypted]</code>\n"
            f"👴 <b>Father Name:</b> <code>[🔒 Govt Database Locked]</code>\n"
            f"🛰️ <b>Live GPS Location:</b> <code>[🔒 Premium Plan Only]</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>Note:</b> Operator aur State details successfully bypass ho gayi hain. Name aur Father Name secure database ke andar lock hain."
        )
        return output
    except Exception as e: 
        return f"⚠️ <b>System Error: {str(e)}</b>"

# =========================================
# CORE BOT LOGIC
# =========================================
def handle_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    user_text = message.get("text", "").strip()
    bot_username = "Nobita_infoo_bot"

    if not is_user_joined(user_id):
        send_message(chat_id, "👋 <b>Welcome to Nobita OSINT Bot!</b>\n\nBot ko use karne ke liye aapko hamare official telegram channel ko join karna zaroori hai.\n\n👇 <b>Niche diye gaye button par click karke join karein:</b>", reply_markup=get_join_keyboard(), parse_mode="HTML")
        return

    if user_text.startswith("/start"):
        parts = user_text.split(" ")
        if len(parts) > 1:
            try:
                referrer_id = int(parts[1])
                if referrer_id != user_id and not is_already_referred(user_id):
                    if add_referral(referrer_id, user_id):
                        current_refs = get_referral_count(referrer_id)
                        send_message(referrer_id, f"🎉 <b>Badhai Ho!</b>\n\nAapke link se ek naye friend ne join kiya hai.\nTotal Referrals: <b>{current_refs}/{REQUIRED_REFERRALS}</b>", parse_mode="HTML")
            except: pass

        welcome_text = (
            f"⚡ <b>WELCOME TO NOBITA OSINT BOT v3.0</b> ⚡\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Aap is bot se kisi bhi mobile number ki Company aur State details nikal sakte hain.\n\n"
            f"📢 <b>Rule:</b> Bot ko bilkul FREE use karne ke liye aapko bas **{REQUIRED_REFERRALS} dosto** ko invite karna hoga.\n\n"
            f"👇 Niche diye gaye buttons se apni progress check karein ya details nikalein!"
        )
        send_photo(chat_id, WELCOME_BANNER, welcome_text, reply_markup=get_premium_menu(), parse_mode="HTML")
        user_states[chat_id] = "idle"
        return

    if user_states.get(chat_id) == "awaiting_phone":
        if user_text.isdigit() and len(user_text) == 10:
            send_message(chat_id, phone_lookup(user_text), reply_markup=get_back_keyboard(), parse_mode="HTML")
            user_states[chat_id] = "idle"
        else:
            send_message(chat_id, "❌ <b>Galat Number!</b>\nKripya bina country code (+91) ke sirf 10 digit ka mobile number send karein.")
        return

def handle_callback(callback):
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    user_id = callback["from"]["id"]
    data = callback["data"]
    bot_username = "Nobita_infoo_bot"

    if data == "check_join":
        if is_user_joined(user_id):
            answer_callback_query(callback_id, "✅ Verification Successful!")
            send_message(chat_id, "🎉 <b>Aapka swagat hai!</b> Channel join ho gaya hai. Ab niche diye gaye menu se bot use karein:", reply_markup=get_premium_menu(), parse_mode="HTML")
        else:
            answer_callback_query(callback_id, "❌ Aapne abhi tak join nahi kiya hai!")
        return

    if not is_user_joined(user_id):
        answer_callback_query(callback_id, "❌ Please channel join karein!")
        return

    if data == "my_referrals":
        my_count = get_referral_count(user_id)
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        p_bar = make_progress_bar(my_count, REQUIRED_REFERRALS)
        
        status_text = (
            f"👥 <b>YOUR REFERRAL DASHBOARD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>Aapki Live Progress:</b>\n{p_bar}\n\n"
            f"🔒 <b>Status:</b> <b>{'🔓 UNLOCKED (Aap use kar sakte hain)' if my_count >= REQUIRED_REFERRALS else '🔒 LOCKED (5 invites chahiye)'}</b>\n\n"
            f"🔗 <b>Aapka Invite Link:</b>\n<code>{ref_link}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>💡 Tip: Is link ko copy karke apne dosto ya WhatsApp groups mein share karein!</i>"
        )
        answer_callback_query(callback_id, "📊 Data Updated")
        send_message(chat_id, status_text, reply_markup=get_back_keyboard(), parse_mode="HTML")
        return

    if data == "phone_lookup":
        my_count = get_referral_count(user_id)
        if my_count < REQUIRED_REFERRALS:
            answer_callback_query(callback_id, "🔒 Feature Locked!")
            ref_link = f"https://t.me/{bot_username}?start={user_id}"
            p_bar = make_progress_bar(my_count, REQUIRED_REFERRALS)
            lock_message = (
                f"⛔ <b>ACCESS DENIED! (Feature Lock Hai)</b>\n\n"
                f"Number details nikalne ke liye pehle 5 referrals poore karein.\n"
                f"📈 <b>Aapke Invites:</b> {p_bar}\n\n"
                f"🔗 <b>Aapka Invite Link:</b>\n<code>{ref_link}</code>"
            )
            send_message(chat_id, lock_message, reply_markup=get_back_keyboard(), parse_mode="HTML")
            return
        
        answer_callback_query(callback_id, "📱 Engine Active")
        send_message(chat_id, "🎯 <b>NUMBER LOOKUP ENGINE ACTIVE</b>\n\nKripya jis mobile number ki details chahiye, wo 10 digit ka number yahan type karke send karein:", parse_mode="HTML")
        user_states[chat_id] = "awaiting_phone"
        return

    if data == "back_to_menu":
        answer_callback_query(callback_id, "🔙 Main Menu")
        welcome_text = (
            f"⚡ <b>WELCOME TO NOBITA OSINT BOT v3.0</b> ⚡\n"
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
        self.wfile.write(b"Easy Professional Bot is Online!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), WebServer)
    server.serve_forever()

# =========================================
# MAIN LOOP
# =========================================
def bot_polling():
    offset = 0
    print("✅ Easy UI Bot Polling Started...")
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
