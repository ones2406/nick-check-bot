import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import pytz

BOT_TOKEN = "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = "7520535840"
URL = "https://cypher289.shop/home"

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=30)
        print("Telegram response:", r.text)
    except Exception as e:
        print("Telegram error:", e)

def fetch_all_products():
    r = requests.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    products = []

    for div in soup.find_all("div", class_=lambda x: x and "rounded-lg" in x):
        name = div.find("h2")
        sold = div.find("span", class_="text-primary-500")
        remain = div.find("span", class_="text-red-500")

        if name and sold and remain:
            products.append({
                "name": name.text.strip(),
                "sold": int(sold.text.strip().replace(",", "")),
                "remain": int(remain.text.strip().replace(",", ""))
            })

    return products

def main():
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)

    products = fetch_all_products()

    if not products:
        send_telegram("⚠️ Không tìm thấy sản phẩm nào trên trang!")
        return

    # Gửi toàn bộ danh sách sản phẩm về Telegram
    msg = (
        f"📋 <b>DANH SÁCH SẢN PHẨM</b>\n"
        f"🕒 {now.strftime('%H:%M %d/%m/%Y')}\n\n"
    )
    for p in products:
        msg += f"🎯 {p['name']}\n   ├ 🟢 Còn lại: <b>{p['remain']}</b>\n   └ 📈 Đã bán: <b>{p['sold']}</b>\n\n"

    send_telegram(msg.strip())

if __name__ == "__main__":
    main()
