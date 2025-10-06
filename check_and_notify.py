import requests
from bs4 import BeautifulSoup
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

def fetch_random_products():
    r = requests.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    products = []

    for div in soup.find_all("div", class_=lambda x: x and "rounded-lg" in x):
        name = div.find("h2")
        sold = div.find("span", class_="text-primary-500")
        remain = div.find("span", class_="text-red-500")

        if name and sold and remain:
            pname = name.text.strip()
            if pname.startswith("Nick random thông tin xấu - thông tin đẹp"):
                products.append({
                    "name": pname,
                    "sold": int(sold.text.strip().replace(",", "")),
                    "remain": int(remain.text.strip().replace(",", ""))
                })
    return products

def main():
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)

    products = fetch_random_products()

    if not products:
        send_telegram("⚠️ Không tìm thấy chuyên mục <b>Nick random thông tin xấu - thông tin đẹp</b>")
        return

    # Sắp xếp để nhìn gọn gàng (nếu có 6 mục)
    products = sorted(products, key=lambda x: x["name"])

    # Báo cáo
    msg = (
        f"📊 <b>BÁO CÁO CHUYÊN MỤC</b>\n"
        f"🕒 {now.strftime('%H:%M %d/%m/%Y')}\n"
        f"📂 Nick random thông tin xấu - thông tin đẹp\n\n"
    )
    for i, p in enumerate(products, 1):
        msg += (
            f"#{i} 🎯 <b>{p['name']}</b>\n"
            f"   ├ 🟢 Còn lại: <b>{p['remain']}</b>\n"
            f"   └ 📈 Đã bán: <b>{p['sold']}</b>\n\n"
        )

    send_telegram(msg.strip())

if __name__ == "__main__":
    main()
