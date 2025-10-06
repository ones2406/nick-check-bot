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
TARGET_PRODUCT = "Nick random thông tin xấu - thông tin đẹp"

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=30)
        print("Telegram response:", r.text)
    except Exception as e:
        print("Telegram error:", e)

def fetch_target_product():
    r = requests.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    for div in soup.find_all("div", class_=lambda x: x and "rounded-lg" in x):
        name = div.find("h2")
        sold = div.find("span", class_="text-primary-500")
        remain = div.find("span", class_="text-red-500")

        if name and sold and remain:
            product_name = name.text.strip()
            if TARGET_PRODUCT.lower() in product_name.lower():
                return {
                    "name": product_name,
                    "sold": int(sold.text.strip().replace(",", "")),
                    "remain": int(remain.text.strip().replace(",", ""))
                }
    return None

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    product = fetch_target_product()
    if not product:
        send_telegram(f"⚠️ Không tìm thấy sản phẩm: {TARGET_PRODUCT}")
        return

    state = load_state()
    new_state = {product["name"]: product["remain"]}
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)
    hour = now.hour

    # 🚨 Cảnh báo hết hàng
    if product["remain"] == 0 and state.get(product["name"], 1) > 0:
        send_telegram(f"🚨 <b>{product['name']}</b> đã <u>HẾT HÀNG</u>!")

    # 📊 Báo cáo tồn kho lúc 0h, 12h hoặc khi chạy tay
    if hour in [0, 12] or os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch":
        report = (
            f"📊 <b>BÁO CÁO TỒN KHO</b>\n"
            f"🕒 {now.strftime('%H:%M %d/%m/%Y')}\n\n"
            f"🎯 <b>{product['name']}</b>\n"
            f"   ├ 🟢 Còn lại: <b>{product['remain']}</b>\n"
            f"   └ 📈 Đã bán: <b>{product['sold']}</b>"
        )
        send_telegram(report)

    save_state(new_state)

if __name__ == "__main__":
    main()
