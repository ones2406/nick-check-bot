import re
import json
import requests
from bs4 import BeautifulSoup
import os

# === CẤU HÌNH BOT TELEGRAM ===
BOT_TOKEN = "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = "7520535840"

# === TRANG WEB CẦN CHECK ===
URL = "https://cypher289.shop/home"
HEADERS = {"User-Agent": "Mozilla/5.0"}

STATE_FILE = "last_state.json"  # lưu trạng thái lần trước

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload, timeout=10)

def parse_number(text, keyword):
    m = re.search(rf"{keyword}\s*[:\-]?\s*([0-9]+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else None

def fetch_products():
    res = requests.get(URL, headers=HEADERS, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    products = {}
    for h2 in soup.find_all("h2"):
        name = h2.get_text(strip=True)
        h4 = h2.find_next("h4")
        info = h4.get_text(" ", strip=True) if h4 else ""
        sold = parse_number(info, "Đã Bán")
        remain = parse_number(info, "Còn")
        products[name] = {"sold": sold, "remain": remain}
    return products

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def main():
    products = fetch_products()
    state = load_state()

    # Xác định cách chạy
    event = os.getenv("GITHUB_EVENT_NAME", "")

    # Nếu chạy theo lịch cron (12h trưa / 12h đêm) => gửi báo cáo
    if event == "schedule":
        now_utc_hour = int(os.getenv("GITHUB_RUN_ATTEMPT", "0"))  # placeholder
        report_lines = ["📊 *BÁO CÁO TỒN KHO* 📊\n"]
        for name, data in products.items():
            line = f"🔹 {name}\n"
            if data["sold"] is not None:
                line += f"   • Đã bán: {data['sold']}\n"
            if data["remain"] is not None:
                line += f"   • Còn lại: {data['remain']}\n"
            report_lines.append(line)
        send_message("\n".join(report_lines))

    # Kiểm tra hết hàng mới
    alerts = []
    for name, data in products.items():
        remain = data["remain"]
        old_remain = state.get(name, {}).get("remain")
        if remain == 0 and old_remain and old_remain > 0:
            alerts.append(f"⚠️ *{name}* vừa hết nick!")

    if alerts:
        send_message("\n".join(alerts))

    # Lưu trạng thái
    save_state(products)

if __name__ == "__main__":
    main()
