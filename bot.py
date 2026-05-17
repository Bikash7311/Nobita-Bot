# =========================================
# Telegram Bot With Force Join & 5 Referral System
# Bot Name: Nobita Osint Info
# Bot Username: @Nobita_infoo_bot
# Educational Purpose Only
# =========================================

import requests
import json
import time
import phonenumbers
from phonenumbers import geocoder, carrier

# =========================================
# CONFIGURATION
# =========================================

BOT_TOKEN = "8892483341:AAHJYIv5ZwwYyDZv7DM1_acO6TNm_bFtbFo"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHANNEL_USERNAME = "@nobitaosint"
REQUIRED_REFERRALS = 5

# =========================================
# DATABASES (In-Memory)
# =========================================

user_states = {}
referral_db = {}
referred_users = {}

# =========================================
# SEND MESSAGE FUNCTION
# =========================================

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = API_URL + "/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Send Message Error:", e)

# =========================================
# MAIN KEYBOARD
# =========================================

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "📱 Phone Lookup"}],
            [{"text": "👥 My Referrals & Link"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# =========================================
# CHECK CHANNEL JOIN
# =========================================

def is_user_joined(user_id):
    try:
        url = API_URL + "/getChatMember"
        params = {"chat_id": CHANNEL_USERNAME, "user_id": user_id}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("ok"):
            if data["result"]["status"] in ["member", "administrator", "creator"]:
                return True
        return False
    except Exception as e:
        print("Join Check Error:", e)
        return False

# =========================================
# PHONE LOOKUP FUNCTION
# =========================================

def phone_lookup(phone_number):
    if not phone_number.startswith('+'):
        if len(phone_number) == 10:
            phone_number = "+91" + phone_number
        else:
            phone_number = "+" + phone_number

    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        if not phonenumbers.is_valid_number(parsed_number):
            return "❌ <b>Number valid nahi hai! Sahi number daalein.</b>"

        location_data = geocoder.description_for_number(parsed_number, "en")
        carrier_data = carrier.name_for_number(parsed_number, "en")
        
        location = location_data if location_data else "Unknown State"
        operator = carrier_data if carrier_data else "Unknown Operator"
        country = "India" if phone_number.startswith("+91") else "International"

        return (
            f"🔍 <b>NUMBER INFO FOUND (LOCAL ENGINE)</b>\n\n"
            f"📞 <b>Number:</b> {phone_number}\n"
            f"🏢 <b>Operator:</b> {operator}\n"
            f"📍 <b>Location/State:</b> {location}\n"
            f"🌍 <b>Country:</b> {country}\n"
            f"⚙️ <b>Status:</b> Valid Number"
        )
    except Exception as e:
        return f"⚠️ <b>Error: {str(e)}</b>"

# =========================================
# HANDLE USER UPDATE
# =========================================

def handle_update(update):
    try:
        if "message" not in update: return
        message = update["message"]
        if "text" not in message: return

        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        user_text = message["text"].strip()
        bot_username = "Nobita_infoo_bot" 

        if user_id not in referral_db:
            referral_db[user_id] = []

        # 1. FORCE JOIN CHECK 
        if not is_user_joined(user_id):
            join_link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
            join_message = (
                "👋 <b>Welcome To Nobita Osint Info</b>\n\n"
                "❌ <b>You must join our channel first to use this bot.</b>\n\n"
                f"🔗 <b>Join Here:</b> {join_link}\n\n"
                "✅ After joining, click /start again."
            )
            send_message(chat_id, join_message, parse_mode="HTML")
            return

        # 2. START COMMAND WITH REFERRAL
        if user_text.startswith("/start"):
            parts = user_text.split(" ")
            if len(parts) > 1:
                referrer_id = parts[1]
                try:
                    referrer_id = int(referrer_id)
                    if referrer_id != user_id and user_id not in referred_users:
                        if referrer_id in referral_db:
                            if user_id not in referral_db[referrer_id]:
                                referral_db[referrer_id].append(user_id)
                                referred_users[user_id] = True
                                send_message(referrer_id, f"🎉 A new friend joined via your link! Total referrals: {len(referral_db[referrer_id])}/{REQUIRED_REFERRALS}")
                except ValueError:
                    pass

            welcome_text = (
                "👋 <b>Welcome To Nobita Osint Info</b>\n\n"
                f"⚠️ Note: This bot requires <b>{REQUIRED_REFERRALS} friend referrals</b> to unlock the Phone Lookup feature.\n\n"
                "Use the buttons below to check your stats or invite friends."
            )
            send_message(chat_id, welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")
            user_states[chat_id] = "idle"
            return

        # 3. REFERRAL STATUS BUTTON
        if user_text == "👥 My Referrals & Link":
            my_count = len(referral_db.get(user_id, []))
            ref_link = f"https://t.me/{bot_username}?start={user_id}"
            
            status_text = (
                f"👥 <b>Your Referral Stats:</b>\n\n"
                f"✅ <b>Invited Friends:</b> {my_count} / {REQUIRED_REFERRALS}\n"
                f"🔒 <b>Status:</b> {'🔓 Unlocked' if my_count >= REQUIRED_REFERRALS else '🔒 Locked'}\n\n"
                f"🔗 <b>Your Invite Link:</b>\n<code>{ref_link}</code>\n\n"
                f"Share this link with {REQUIRED_REFERRALS} friends to unlock the Phone Lookup feature!"
            )
            send_message(chat_id, status_text, parse_mode="HTML")
            return

        # 4. PHONE LOOKUP BUTTON 
        if user_text == "📱 Phone Lookup":
            my_count = len(referral_db.get(user_id, []))
            
            if my_count < REQUIRED_REFERRALS:
                ref_link = f"https://t.me/{bot_username}?start={user_id}"
                lock_message = (
                    f"⛔ <b>Access Denied!</b>\n\n"
                    f"You have only invited <b>{my_count}/{REQUIRED_REFERRALS}</b> friends.\n"
                    f"Please invite {REQUIRED_REFERRALS - my_count} more friends using your link to unlock this feature:\n\n"
                    f"🔗 <code>{ref_link}</code>"
                )
                send_message(chat_id, lock_message, parse_mode="HTML")
                return

            send_message(chat_id, "📞 Send 10 digit mobile number:")
            user_states[chat_id] = "awaiting_phone"
            return

        # 5. PHONE NUMBER INPUT
        if user_states.get(chat_id) == "awaiting_phone":
            if user_text.isdigit() and len(user_text) == 10:
                formatted_message = phone_lookup(user_text)
                send_message(chat_id, formatted_message, parse_mode="HTML")
                user_states[chat_id] = "idle"
            else:
                send_message(chat_id, "❌ Invalid mobile number.\nPlease send a valid 10 digit number.")
            return

        send_message(chat_id, "⚠️ Unknown command.\nUse /start to begin.")
    except Exception as e:
        print("Handle Update Error:", e)

# =========================================
# MAIN LOOP
# =========================================

def main():
    offset = 0
    print("✅ Bot Started with Force Join & 5 Referral System...")
    while True:
        try:
            url = API_URL + "/getUpdates"
            params = {"timeout": 30, "offset": offset}
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            if data.get("ok"):
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    handle_update(update)
        except Exception as e:
            print("Polling Error:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()
