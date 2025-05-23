import os

import requests
from dotenv import load_dotenv

class TelegramBot:
    # Load environment variables
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    @staticmethod
    def remove_duplicates(events):
        seen = set()
        unique_events = []

        for event in events:
            if event not in seen:
                seen.add(event)
                unique_events.append(event)

        return unique_events

    @staticmethod
    def send_message(message: str) -> bool:
        if not TelegramBot.TOKEN or not TelegramBot.CHAT_ID:
            print("Error: BOT_TOKEN or CHAT_ID not found in environment variables.")
            return False

        url = f"https://api.telegram.org/bot{TelegramBot.TOKEN}/sendMessage"
        payload = {
            "chat_id": TelegramBot.CHAT_ID,
            "text": message
        }

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return True
            else:
                print(f"Failed to send message. Status code: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    @staticmethod
    def post(events):
        print("[TELEGRAM BOT - SE ENVIARAN SIN FILTRAR]")
        print(events)
        unique_events = TelegramBot.remove_duplicates(events)
        print("[TELEGRAM BOT - FILTRADO]")
        print(unique_events)
        for (title, country, actual) in unique_events:
            text = f"Llego una novedad de {country}, {title}. Nuevo actual: {actual}"
            TelegramBot.send_message(text)
