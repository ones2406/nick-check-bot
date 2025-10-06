import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# Cấu hình bot
BOT_TOKEN = "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = "7520535840"
URL = "https://cypher289.shop/home"

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    })
    print("Telegram response:", r.text)

def fetch_all_products():
    r = requests.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    products = []

    for div in soup.find_all("div", class_=lambda x: x and "rounded-lg" in x):
        name = div.find("h2")
        sold = div.find("span", class_="text-primary-500")
        remain = div.find("span", class_="text-red-500")

        if name and sold and remain:
            pname = name.text.strip()
            products.append({
                "name": pname,
                "sold": int(sold.text.strip().replace(",", "")),
                "remain": int(remain.text.strip().replace(",", ""))
            })
    return products

def main():
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)
    products = fetch_all_products()

    if not products:
        send_telegram("⚠️ Không tìm thấy sản phẩm nào trên web!")
        return

    # Header ngầu
    msg = (
        "🚀 <b>DANH SÁCH TOÀN BỘ SẢN PHẨM</b>\n"
        f"🕒 {now.strftime('%H:%M %d/%m/%Y')}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    total_sold = 0
    total_remain = 0

    for i, p in enumerate(products, 1):
        msg += (
            f"#{i} 🔥 <b>{p['name']}</b>\n"
            f"   🟢 Còn lại: <code>{p['remain']}</code>\n"
            f"   📈 Đã bán: <code>{p['sold']}</code>\n"
            "━━━━━━━━━━━━━━\n"
        )
        total_sold += p["sold"]
        total_remain += p["remain"]

        # Chia nhỏ message nếu quá dài
        if len(msg) > 3500:
            send_telegram(msg)
            msg = ""

    # Tổng kết
    msg += (
        "\n📦 <b>TỔNG KẾT</b>\n"
        f"   🟢 Tổng còn lại: <b>{total_remain}</b>\n"
        f"   🔥 Tổng đã bán: <b>{total_sold}</b>\n"
    )

    send_telegram(msg)

if __name__ == "__main__":
    main()
