"""One-time helper: fetch your Telegram chat ID by reading recent messages
sent to your bot. Run this after sending your bot any message on Telegram."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def main():
    if not BOT_TOKEN or BOT_TOKEN == "paste_your_bot_token_here":
        print("TELEGRAM_BOT_TOKEN is not set in .env yet. Paste your real token there first.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    if not data.get("result"):
        print("No messages found yet. Send your bot a message on Telegram first, then run this again.")
        return

    latest_message = data["result"][-1]["message"]
    chat_id = latest_message["chat"]["id"]
    sender_name = latest_message["chat"].get("first_name", "unknown")

    print(f"Found chat ID: {chat_id} (from a message by: {sender_name})")
    print("Add this to your .env file as: TELEGRAM_CHAT_ID=" + str(chat_id))


if __name__ == "__main__":
    main()
