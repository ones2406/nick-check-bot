import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import pytz

# ==============================
# Config
# ==============================
BOT_TOKEN = "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = "7520535840"
URL = "https://cypher289.shop/home"
STATE_FILE = "last_state.json"
TZ = pytz.timezone("Asia/Ho_Chi_Minh")

# ==============================
# Helpers
# ==============================
def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=30)
    except Exception as e:
        print("Telegram error:", e)

def fetch_products():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    products = []
    # Tìm tất cả div có class chứa "rounded-lg"
    for div in soup.find_all("div", class_=lambda x: x and "rounded-lg" in x):
        name_tag = div.find("h2")
        sold_tag = div.find("span", class_="text-primary-500")
        remain_tag = div.find("span", class_="text-red-500")

        if not name_tag or not sold_tag or not remain_tag:
            continue

        try:
            name = name_tag.get_text(strip=True)
            sold = int(sold_tag.get_text(strip=True).replace(".", "").replace(",", ""))
            remain = int(remain_tag.get_text(strip=True).replace(".", "").replace(",", ""))
            products.append({"name": name, "sold": sold, "remain": remain})
        except Exception:
            continue

    return products

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ==============================
# Main logic
# ==============================
def main():
    products = fetch_products()
    if not products:
        send_telegram("⚠️ Không tìm thấy sản phẩm nào! (parser không match HTML)")
        return

    state = load_state()
    new_state = {}
    alerts = []

    for p in products:
        name = p["name"]
        remain = p["remain"]
        new_state[name] = remain

        old_remain = state.get(name, None)

        # Nếu từ >0 chuyển sang =0 thì báo
        if old_remain is not None and old_remain > 0 and remain == 0:
            alerts.append(f"❌ <b>{name}</b> đã <u>hết hàng</u>!")

    # Gửi cảnh báo ngay
    for msg in alerts:
        send_telegram(msg)

    # Check giờ để gửi báo cáo tổng
    now = datetime.now(TZ)
    if now.hour in [0, 12] and now.minute < 10:  # chạy trong 10p đầu
        report = ["📊 <b>Báo cáo tồn kho</b>"]
        for p in products:
            report.append(f"{p['name']}: Đã bán {p['sold']} | Còn {p['remain']}")
        send_telegram("\n".join(report))

    save_state(new_state)


if __name__ == "__main__":
    main()
