import requests
from bs4 import BeautifulSoup
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://cypher289.shop/home"

def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )

def main():
    res = requests.get(URL)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    empty_items = []

    cards = soup.find_all("div", class_="card")  # cần chỉnh chính xác class
    for card in cards:
        text = card.get_text(" ", strip=True)
        if "Bán Hết" in text or "Còn 0 Nick" in text:
            empty_items.append(text)

    if empty_items:
        msg = "⚠️ Các mục đã hết nick:\n" + "\n".join(empty_items)
        send_message(msg)
        print("Đã gửi thông báo:", msg)
    else:
        print("✅ Chưa có mục nào hết nick.")

if __name__ == "__main__":
    main()
