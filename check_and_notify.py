import re
import requests
from bs4 import BeautifulSoup

# ====== THÔNG TIN BOT (ĐÃ CHÈN SẴN) ======
BOT_TOKEN = "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = "7520535840"
# ========================================

URL = "https://cypher289.shop/home"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116 Safari/537.36"}

def send_message(text):
    """Gửi tin nhắn về Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code != 200:
            print("Lỗi khi gửi tin nhắn:", resp.status_code, resp.text)
        else:
            print("Đã gửi tin nhắn:", text)
    except Exception as e:
        print("Exception khi gọi Telegram API:", e)

def parse_remain_from_text(text):
    """Cố gắng parse số 'Còn X' từ chuỗi text."""
    if not text:
        return None
    # Tìm mẫu "Còn 37" hoặc "Còn: 37"
    m = re.search(r'[Cc]òn\s*[:\-]?\s*([0-9]+)', text)
    if m:
        try:
            return int(m.group(1))
        except:
            return None
    # Tìm span số đơn thuần
    m2 = re.search(r'\b([0-9]{1,5})\b', text)
    if m2:
        try:
            return int(m2.group(1))
        except:
            return None
    return None

def check_stock():
    """Tải trang, phân tích từng product, và gửi thông báo nếu thấy 'hết'."""
    try:
        res = requests.get(URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print("Lỗi khi tải trang:", e)
        send_message(f"❌ Lỗi khi tải trang {URL}: {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")

    sold_out_items = []
    checked_items = []

    # Strategy: duyệt tất cả thẻ <h2> làm tên SP (theo cấu trúc HTML bạn cung cấp),
    # rồi tìm thẻ h4 hoặc các span chứa số lượng bên cạnh.
    for h2 in soup.find_all("h2"):
        name = h2.get_text(strip=True)
        # tìm h4 liên quan (thường chứa "Đã Bán ... | Còn ...")
        h4 = None
        # tìm trong cha của h2 hoặc next h4
        parent = h2
        for _ in range(4):
            if parent is None:
                break
            h4 = parent.find("h4")
            if h4:
                break
            parent = parent.parent
        if not h4:
            h4 = h2.find_next("h4")

        info_text = h4.get_text(" ", strip=True) if h4 else ""
        # ưu tiên lấy span class text-red-500 (theo screenshot)
        remain = None
        if h4:
            span_rem = h4.find("span", class_="text-red-500")
            if span_rem:
                try:
                    remain = int(span_rem.get_text(strip=True))
                except:
                    remain = None

        if remain is None:
            remain = parse_remain_from_text(info_text)

        # Kiểm tra các chỉ dấu "Bán Hết" hoặc "hết"
        sold_flag = False
        if "Bán Hết" in info_text or "Bán Hết" in name or "hết" in info_text.lower():
            sold_flag = True
        if remain is not None and remain == 0:
            sold_flag = True

        checked_items.append((name, remain, info_text))
        if sold_flag:
            sold_out_items.append((name, remain, info_text))

    # Nếu có sản phẩm hết, gửi thông báo (mỗi SP 1 message)
    if sold_out_items:
        for name, remain, info in sold_out_items:
            text = f"⚠️ *HẾT NICK* — {name}\n"
            if remain is not None:
                text += f"Số còn lại: {remain}\n"
            if info:
                text += f"Chi tiết: {info}"
            send_message(text)
    else:
        # Không gửi message nếu không có gì hết để tránh spam.
        print("Chưa có sản phẩm nào hết. Tổng sản phẩm check:", len(checked_items))

if __name__ == "__main__":
    check_stock()
