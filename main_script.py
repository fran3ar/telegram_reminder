import os
import requests
from datetime import datetime

def send_telegram_message(token, chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print("⚠️ Error enviando mensaje a Telegram:", e)
        return None

BOT_TOKEN = os.getenv("SECRET_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MESSAGE = os.getenv("MESSAGE")

send_telegram_message(BOT_TOKEN, CHAT_ID, MESSAGE)
