import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# ==== Config ====
BOT_TOKEN = "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = "7520535840"
STATE_FILE = "last_state.json"
URL = "https://cypher289.shop/home"

# ==== Gửi tin nhắn Telegram ====
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print("Lỗi gửi Telegram:", e)

# ==== Lấy danh sách sản phẩm từ web ====
def fetch_products():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    products = []
    # Lấy toàn bộ div, rồi lọc class có chứa "rounded-lg"
    for div in soup.find_all("div"):
        classes = div.get("class", [])
        if "rounded-lg" not in classes:
            continue

        name_tag = div.find("h2")
        h4_tags = div.find_all("h4")
        if not name_tag or len(h4_tags) < 2:
            continue

        sold_tag = h4_tags[0].find("span")
        remain_tag = h4_tags[1].find("span")

        try:
            name = name_tag.get_text(strip=True)
            sold = int(sold_tag.get_text(strip=True).replace(".", "").replace(",", ""))
            remain = int(remain_tag.get_text(strip=True).replace(".", "").replace(",", ""))
            products.append({"name": name, "sold": sold, "remain": remain})
        except:
            continue

    return products

# ==== Load/Save trạng thái cũ ====
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ==== Main ====
def main():
    try:
        products = fetch_products()
    except Exception as e:
        send_telegram(f"⚠️ Không lấy được dữ liệu sản phẩm!\n{e}")
        return

    if not products:
        send_telegram("⚠️ Không tìm thấy sản phẩm nào! (parser không match HTML)")
        return

    state = load_state()
    new_state = {}
    alerts = []

    for p in products:
        name, remain = p["name"], p["remain"]
        new_state[name] = remain
        old_remain = state.get(name)

        if old_remain is not None and old_remain > 0 and remain == 0:
            alerts.append(f"🚨 <b>{name}</b> đã <u>hết hàng</u>!")
        if old_remain is None and remain == 0:
            alerts.append(f"🚨 <b>{name}</b> hiện đang <u>hết hàng</u>!")

    if alerts:
        send_telegram("\n".join(alerts))

    now = datetime.now()
    if now.hour in (0, 12) or os.environ.get("MANUAL_RUN") == "1":
        report_lines = [f"📊 <b>Báo cáo tồn kho ({len(products)} sản phẩm)</b>"]
        for p in products:
            report_lines.append(f"- {p['name']}: còn {p['remain']} (đã bán {p['sold']})")
        send_telegram("\n".join(report_lines))

    save_state(new_state)


if __name__ == "__main__":
    main()
