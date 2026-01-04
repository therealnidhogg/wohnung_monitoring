import os
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
URL = "https://bauverein-haidhausen.de/wohnungsangebote"
STATE_FILE = "known_ads.txt"

# Telegram Secrets from GitHub
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram secrets missing.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        # 'Markdown' allows bolding, but can break if the site has weird characters. 
        # We'll use safe text only.
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✔ Telegram message sent!")
    except Exception as e:
        print(f"❌ Failed to send Telegram: {e}")

def check_website():
    print(f"--- Checking {URL} ---")
    
    try:
        response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        response.encoding = 'utf-8'
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    full_text = soup.get_text(separator="\n")

    # --- CLEANING LOGIC ---
    start_marker = "Eine Bewerbung ist nur online möglich."
    end_marker = "Bauverein München Haidhausen eG"

    if start_marker in full_text:
        content_after_header = full_text.split(start_marker, 1)[1]
        
        if end_marker in content_after_header:
            clean_content = content_after_header.split(end_marker, 1)[0]
        else:
            clean_content = content_after_header

        lines = [line.strip() for line in clean_content.splitlines() if line.strip()]
        final_text = "\n".join(lines)
        
        # --- STATE MANAGEMENT ---
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                old_text = f.read()
        else:
            old_text = ""
            
        if final_text != old_text:
            print("🔄 Changes detected!")
            
            msg = f"🏠 **New Apartment Update!**\n\n{final_text}\n\nCheck here: {URL}"
            send_telegram(msg)
            
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                f.write(final_text)
        else:
            print("✔ No changes found.")
            
    else:
        error_msg = "❌ Could not find the listing section. Website structure might have changed."
        print(error_msg)
        send_telegram(f"⚠ Bot Error: {error_msg}")

if __name__ == "__main__":
    check_website()
