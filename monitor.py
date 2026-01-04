import os
import smtplib
from email.message import EmailMessage
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
URL = "https://bauverein-haidhausen.de/wohnungsangebote"
STATE_FILE = "known_ads.txt"

# Outlook Secrets from GitHub
OUTLOOK_EMAIL = os.environ.get("OUTLOOK_EMAIL")
OUTLOOK_PASSWORD = os.environ.get("OUTLOOK_PASSWORD") # App Password recommended
TARGET_EMAIL = os.environ.get("TARGET_EMAIL") # Where you want to receive the alert

def send_outlook_email(subject, body):
    if not OUTLOOK_EMAIL or not OUTLOOK_PASSWORD:
        print("❌ Outlook secrets missing. Skipping notification.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = OUTLOOK_EMAIL
    msg["To"] = TARGET_EMAIL

    try:
        # Outlook / Office365 SMTP Settings
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls() # Secure the connection
        server.login(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✔ Email sent to {TARGET_EMAIL}")
    except Exception as e:
        print(f"❌ Failed to send email via Outlook: {e}")

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
            email_body = f"The apartment listings have changed!\n\nNew Content:\n{final_text}\n\nCheck here: {URL}"
            send_outlook_email("🏠 New Apartment Update!", email_body)
            
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                f.write(final_text)
        else:
            print("✔ No changes found.")
            
    else:
        error_msg = "❌ Could not find the listing section. Website structure might have changed."
        print(error_msg)
        send_outlook_email("⚠ Bot Error: Structure Changed", f"{error_msg}\n\nPlease check the script markers.")

if __name__ == "__main__":
    check_website()
