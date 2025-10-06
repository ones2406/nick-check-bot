import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import pytz

BOT_TOKEN = "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = "7520535840"
URL = "https://cypher289.shop/home"
STATE_FILE = "last_state.json"

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=30)
        print("Telegram response:", r.text)   # DEBUG
    except Exception as e:
        print("Telegram error:", e)

def fetch_products():
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

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    products = fetch_products()
    if not products:
        send_telegram("⚠️ Không tìm thấy sản phẩm nào! (parser không match HTML)")
        return

    state = load_state()
    new_state = {}
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)
    hour = now.hour

    report_lines = [f"📦 Báo cáo tồn kho ({now.strftime('%H:%M %d/%m/%Y')})"]

    for p in products:
        new_state[p["name"]] = p["remain"]
        report_lines.append(f"- {p['name']}: còn {p['remain']} | đã bán {p['sold']}")

        # cảnh báo hết hàng
        if p["remain"] == 0 and state.get(p["name"], 1) > 0:
            send_telegram(f"🚨 {p['name']} đã hết hàng!")

    # gửi báo cáo vào 0h và 12h
    if hour in [0, 12] or os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch":
        send_telegram("\n".join(report_lines))

    save_state(new_state)

if __name__ == "__main__":
    main()
