"""Send one test message via the Telegram bot, to confirm the connection
works before building any detection/notification logic on top of it."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so telegram_notify.py (project root) is importable

from telegram_notify import BOT_TOKEN, CHAT_ID, send_message


def main():
    if not BOT_TOKEN or BOT_TOKEN == "paste_your_bot_token_here":
        print("TELEGRAM_BOT_TOKEN is not set in .env yet.")
        return
    if not CHAT_ID or CHAT_ID == "paste_your_chat_id_here":
        print("TELEGRAM_CHAT_ID is not set in .env yet. Run get_telegram_chat_id.py first.")
        return

    result = send_message("Doormat Package Detector: test message. If you see this, the connection works.")

    if result.get("ok"):
        print("Message sent successfully. Check your Telegram app.")
    else:
        print(f"Telegram reported an error: {result}")


if __name__ == "__main__":
    main()
