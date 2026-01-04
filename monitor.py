import os
import smtplib
from email.message import EmailMessage
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
URL = "https://bauverein-haidhausen.de/wohnungsangebote"
STATE_FILE = "known_ads.txt"

# Email Settings (Loaded from GitHub Secrets)
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD") # This must be an App Password, not your login password
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT") # Can be the same as EMAIL_ADDRESS

def send_email(subject, body):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("❌ Email secrets are missing. Skipping notification.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_RECIPIENT

    try:
        # Connect to Gmail SMTP (change if using Outlook/Yahoo)
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✔ Email sent: {subject}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

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

    # --- YOUR CLEANING LOGIC ---
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
        
        # 1. Read previous state
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                old_text = f.read()
        else:
            old_text = ""
            
        # 2. Compare
        if final_text != old_text:
            print("🔄 Changes detected!")
            
            # Send Email
            email_body = f"The apartment listings have changed!\n\nNew Content:\n{final_text}\n\nCheck here: {URL}"
            send_email("🏠 New Apartment Update!", email_body)
            
            # Save new state
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                f.write(final_text)
        else:
            print("✔ No changes found.")
            
    else:
        # --- ERROR HANDLING ---
        error_msg = "❌ Could not find the listing section. Website structure might have changed."
        print(error_msg)
        send_email("⚠ Bot Error: Structure Changed", f"{error_msg}\n\nPlease check the script markers.")

if __name__ == "__main__":
    check_website()
