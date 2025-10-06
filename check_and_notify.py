import requests
from bs4 import BeautifulSoup

# === Thay bằng token/chat_id của bạn ===
BOT_TOKEN = "82659xxxxxx:AAEJXXXXXX"   # token bạn gửi mình
CHAT_ID = "7520535840"                 # chat id của bạn

URL = "https://cypher289.shop/home"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Lỗi gửi tin:", e)

def check_stock():
    try:
        res = requests.get(URL, timeout=15)
        res.raise_for_status()
    except Exception as e:
        send_message(f"❌ Không lấy được dữ liệu: {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    products = soup.find_all("div", class_="card-body")

    sold_out = []
    for product in products:
        name_tag = product.find("h2")
        count_tag = product.find("span", class_="text-red-500")

        if not name_tag or not count_tag:
            continue

        name = name_tag.get_text(strip=True)
        try:
            remain = int(count_tag.get_text(strip=True))
        except ValueError:
            continue

        if remain == 0:
            sold_out.append(name)

    if sold_out:
        for item in sold_out:
            send_message(f"⚠️ {item} đã HẾT NICK!")
    else:
        print("Chưa có sản phẩm nào hết nick.")

if __name__ == "__main__":
    check_stock()
