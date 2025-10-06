import os
import json
import requests
from bs4 import BeautifulSoup

# ==== Config Telegram (đã gắn trực tiếp) ====
TELEGRAM_BOT_TOKEN = "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = "7520535840"   # chat id của bạn (lấy từ JSON)

# ==== Config trang web ====
URL = "https://shopnick.vnroblox.com/shop/roblox"   # thay link đúng của bạn
STATE_FILE = "last_state.json"


def send_message(text: str):
    """Gửi tin nhắn Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            print("❌ Telegram error:", r.text)
        else:
            print("✅ Sent to Telegram")
    except Exception as e:
        print("❌ Send message failed:", e)


def fetch_products():
    """Lấy danh sách sản phẩm từ trang web"""
    products = {}
    try:
        res = requests.get(URL, timeout=20)
        res.raise_for_status()
    except Exception as e:
        print("❌ Fetch error:", e)
        return products

    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.find_all("div", class_="p-4")  # chỉnh selector theo web thực tế

    for item in items:
        name_tag = item.find("h2")
        sold_tag = item.find("span", class_="text-gray-500")
        remain_tag = item.find("span", class_="text-red-500")

        name = name_tag.text.strip() if name_tag else "Unknown"
        sold = None
        remain = None

        if sold_tag:
            try:
                sold = int("".join(filter(str.isdigit, sold_tag.text)))
            except:
                pass
        if remain_tag:
            try:
                remain = int("".join(filter(str.isdigit, remain_tag.text)))
            except:
                pass

        products[name] = {"sold": sold, "remain": remain}
    return products


def load_state():
    """Đọc trạng thái cũ từ file"""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_state(state):
    """Lưu trạng thái mới"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    products = fetch_products()
    if not products:
        send_message("⚠️ Không lấy được dữ liệu sản phẩm!")
        return

    state = load_state()
    event = os.getenv("GITHUB_EVENT_NAME", "")

    # === 1. Luôn gửi báo cáo khi chạy tay hoặc theo lịch ===
    if event in ["schedule", "workflow_dispatch"]:
        report_lines = ["📊 *BÁO CÁO TỒN KHO* 📊\n"]
        for name, data in products.items():
            line = f"🔹 {name}\n"
            if data["sold"] is not None:
                line += f"   • Đã bán: {data['sold']}\n"
            if data["remain"] is not None:
                line += f"   • Còn lại: {data['remain']}\n"
            report_lines.append(line)
        send_message("\n".join(report_lines))

    # === 2. Báo hết hàng mới hoặc hết ngay lần đầu ===
    alerts = []
    for name, data in products.items():
        remain = data["remain"]
        old_remain = state.get(name, {}).get("remain")

        if remain == 0 and (old_remain is None or old_remain > 0):
            alerts.append(f"⚠️ *{name}* đã hết nick!")

    if alerts:
        send_message("\n".join(alerts))

    # === 3. Lưu trạng thái mới ===
    save_state(products)


if __name__ == "__main__":
    main()
