import requests

# ====== THÔNG TIN (đã gắn sẵn) ======
BOT_TOKEN = "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = "7520535840"
# =====================================

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        response = requests.post(url, data=payload, timeout=15)
        if response.status_code != 200:
            print("Lỗi khi gửi tin nhắn:", response.status_code, response.text)
        else:
            print("Đã gửi tin nhắn thành công.")
    except Exception as e:
        print("Exception khi gọi Telegram API:", str(e))

if __name__ == "__main__":
    send_message("✅ Bot đã kết nối thành công và gửi test message!")
