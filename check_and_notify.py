#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: crawl products + gửi Telegram
- Lấy tên, đã bán, còn lại, giá (nếu có), link chi tiết (nếu có)
- Nếu remain == 0 -> ghi "ĐÃ BÁN HẾT"
- Escape HTML trước khi gửi (parse_mode=HTML)
- Dùng requests.Session, kiểm tra lỗi HTTP, safe int parsing
"""

import os
import re
import html
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from pathlib import Path
from typing import List, Dict, Optional

# --------- Cấu hình (khuyên dùng env vars, nhưng có thể gán trực tiếp) ----------
BOT_TOKEN = os.getenv("MY_BOT_TOKEN") or "8265932226:AAE8ki950o1FmQ2voDqIk7UDJaYPIolnWU0"
CHAT_ID = os.getenv("MY_CHAT_ID") or "7520535840"
URL = "https://cypher234.shop/home"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TIMEZONE = "Asia/Ho_Chi_Minh"
MAX_TELEGRAM_LEN = 3900   # giữ an toàn < 4096

# ---------- Helpers ----------
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
})

def now(tz_name: str = TIMEZONE) -> str:
    tz = pytz.timezone(tz_name)
    return datetime.now(tz).strftime("%H:%M %d/%m/%Y")

def safe_int_from_text(s: Optional[str]) -> int:
    """
    Lấy số nguyên từ chuỗi: loại bỏ ký tự không phải số.
    Trả về 0 nếu không tìm thấy chữ số.
    """
    if not s:
        return 0
    s = s.strip()
    # chuyển dạng 1.2k, 3k, 1.5k thành số (nếu cần)
    # trước tiên thử chuyển trực tiếp các chữ số
    m = re.search(r"([\d\.,]+)\s*([kKmM]?)", s)
    if not m:
        digits = re.sub(r"[^\d]", "", s)
        return int(digits) if digits else 0
    num = m.group(1).replace(",", "").replace(".", "")
    suffix = m.group(2).lower()
    try:
        # nếu có suffix 'k' hoặc 'm' thì xử lý
        if suffix == "k":
            # vd "1.2k" -> 1200 (approx). Toàn bộ m.group(1) lost decimals because removed dot,
            # better parse float from original with dot preserved:
            try:
                f = float(m.group(1).replace(",", ""))
                return int(f * 1000)
            except:
                pass
        if suffix == "m":
            try:
                f = float(m.group(1).replace(",", ""))
                return int(f * 1_000_000)
            except:
                pass
        # default: chỉ giữ digits
        digits = re.sub(r"[^\d]", "", m.group(1))
        return int(digits) if digits else 0
    except:
        return 0

def safe_text(x: Optional[str]) -> str:
    return x.strip() if x else ""

# ---------- Telegram send with basic check & retry ----------
def send_telegram(msg: str, chat_id: str = CHAT_ID, tries: int = 2, sleep_between: float = 1.0) -> bool:
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    for attempt in range(1, tries + 1):
        try:
            r = session.post(TELEGRAM_API, data=payload, timeout=15)
            if r.status_code == 200:
                j = r.json()
                if j.get("ok"):
                    return True
                else:
                    # Telegram trả ok=false, log lý do
                    print("[telegram] ok=false response:", j)
            else:
                print(f"[telegram] HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[telegram] Exception attempt {attempt}: {e}")
        if attempt < tries:
            time.sleep(sleep_between)
    return False

# ---------- Scraper: lấy tất cả sản phẩm ----------
def fetch_all_products() -> List[Dict]:
    """
    Trả về list product dict:
    {
      "name": str,
      "sold": int,
      "remain": int,
      "price": Optional[str],
      "href": Optional[str],
      "status": "CÒN" | "ĐÃ BÁN HẾT"
    }
    """
    try:
        r = session.get(URL, timeout=30)
    except Exception as e:
        print("[fetch_all_products] request error:", e)
        return []
    if r.status_code != 200:
        print("[fetch_all_products] http status:", r.status_code)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    products = []

    # tìm tất cả block có class chứa 'rounded-lg' (giữ nguyên logic cũ)
    for div in soup.find_all("div", class_=lambda x: x and "rounded-lg" in x):
        # tên: h2 hoặc element có class tương ứng
        name_tag = div.find("h2") or div.find(attrs={"class": lambda v: v and "product-name" in v})
        sold_tag = div.find("span", class_=lambda x: x and "text-primary-500" in x) or div.find(attrs={"class": lambda v: v and "sold" in v})
        remain_tag = div.find("span", class_=lambda x: x and "text-red-500" in x) or div.find(attrs={"class": lambda v: v and "remain" in v})
        price_tag = div.find(attrs={"class": lambda v: v and ("price" in v or "text-green" in v)}) or div.find("p", class_=lambda x: x and "price" in x)
        link_tag = div.find("a", href=True)

        name = safe_text(name_tag.text) if name_tag else None
        sold_raw = safe_text(sold_tag.text) if sold_tag else None
        remain_raw = safe_text(remain_tag.text) if remain_tag else None
        price = safe_text(price_tag.text) if price_tag else None
        href = link_tag["href"].strip() if link_tag else None

        sold = safe_int_from_text(sold_raw)
        remain = safe_int_from_text(remain_raw)

        status = "ĐÃ BÁN HẾT" if remain == 0 else "CÒN"

        products.append({
            "name": name or "(Không có tên)",
            "sold": sold,
            "remain": remain,
            "price": price,
            "href": href,
            "status": status,
            "raw_sold": sold_raw,
            "raw_remain": remain_raw
        })
    return products

# ---------- Build message (HTML) và chia nhỏ nếu cần ----------
def build_messages(products: List[Dict]) -> List[str]:
    header = (
        f"🚀 <b>DANH SÁCH TOÀN BỘ SẢN PHẨM</b>\n"
        f"🕒 {now()}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    msgs = []
    current = header
    total_sold = 0
    total_remain = 0

    def safe_item_line(i: int, p: Dict) -> str:
        # escape HTML
        name = html.escape(p.get("name", ""))
        sold = p.get("sold", 0)
        remain = p.get("remain", 0)
        price = html.escape(p["price"]) if p.get("price") else None
        href = p.get("href")
        status = p.get("status", "")
        extra = ""
        if price:
            extra += f"   💰 Giá: <code>{price}</code>\n"
        if href:
            # ensure absolute url if needed
            link_display = html.escape(href)
            extra += f"   🔗 <a href=\"{link_display}\">Chi tiết</a>\n"
        # If sold out, show marker
        soldout_line = ""
        if status == "ĐÃ BÁN HẾT":
            soldout_line = "   ❌ <b>ĐÃ BÁN HẾT</b>\n"

        return (
            f"#{i} 🔥 <b>{name}</b>\n"
            f"   🟢 Còn lại: <code>{remain}</code>\n"
            f"   📈 Đã bán: <code>{sold}</code>\n"
            f"{extra}"
            f"{soldout_line}"
            "━━━━━━━━━━━━━━\n"
        )

    for i, p in enumerate(products, 1):
        line = safe_item_line(i, p)
        # nếu thêm line làm dài > MAX_TELEGRAM_LEN thì push current and start new
        if len(current) + len(line) > MAX_TELEGRAM_LEN:
            msgs.append(current)
            current = line
        else:
            current += line
        total_sold += p.get("sold", 0)
        total_remain += p.get("remain", 0)

    # append summary
    summary = (
        "\n📦 <b>TỔNG KẾT</b>\n"
        f"   🟢 Tổng còn lại: <b>{total_remain}</b>\n"
        f"   🔥 Tổng đã bán: <b>{total_sold}</b>\n"
    )
    if len(current) + len(summary) > MAX_TELEGRAM_LEN:
        msgs.append(current)
        msgs.append(summary)
    else:
        current += summary
        msgs.append(current)

    return msgs

# ---------- Main ----------
def main():
    products = fetch_all_products()
    if not products:
        send_text = f"⚠️ Không tìm thấy sản phẩm trên trang {URL} — {now()}"
        send_telegram(send_text)
        return

    msgs = build_messages(products)
    for m in msgs:
        ok = send_telegram(m)
        if not ok:
            print("[main] Gửi Telegram thất bại cho 1 message")
        time.sleep(0.6)  # nhẹ nhàng giữa các message gửi

if __name__ == "__main__":
    main()
