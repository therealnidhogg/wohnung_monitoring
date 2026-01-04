import os
import requests
from bs4 import BeautifulSoup
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# --- CONFIGURATION ---
URL = "https://bauverein-haidhausen.de/wohnungsangebote"
STATE_FILE = "known_ads.txt"

# Secrets from GitHub (We only need the API Key and your email)
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
MY_EMAIL = os.environ.get("MY_EMAIL")  # The email you want to receive alerts on

def send_email_via_brevo(subject, body):
    if not BREVO_API_KEY or not MY_EMAIL:
        print("❌ Brevo secrets missing. Skipping notification.")
        return

    # Configure API key authorization: api-key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY

    # Create an instance of the API class
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    # Define the email sender and recipient
    # Note: Sender must be a verified email in Brevo (usually the one you signed up with)
    sender = {"name": "Apartment Bot", "email": MY_EMAIL}
    to = [{"email": MY_EMAIL, "name": "Me"}]
    
    # Create the email object
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        text_content=body
    )

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"✔ Email sent successfully! ID: {api_response.message_id}")
    except ApiException as e:
        print(f"❌ Failed to send email via Brevo: {e}")

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
            send_email_via_brevo("🏠 New Apartment Update!", email_body)
            
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                f.write(final_text)
        else:
            print("✔ No changes found.")
            
    else:
        error_msg = "❌ Could not find the listing section. Website structure might have changed."
        print(error_msg)
        send_email_via_brevo("⚠ Bot Error: Structure Changed", f"{error_msg}\n\nPlease check the script markers.")

if __name__ == "__main__":
    check_website()
