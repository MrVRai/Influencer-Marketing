"""
Bulk Email Outreach Engine for Creator Orbit
Automates sending personalized campaign invitations and network onboarding emails to creators.

Features:
- Queries creators with valid emails from creators.db
- Deduplication: Keeps a local history log (sent_emails_history.json) to never double-email
- Randomized anti-spam delays (default 12-25s)
- Dry-run mode for testing and previewing before sending
"""

import os
import sys
import json
import time
import random
import sqlite3
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/creators.db"))
HISTORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/sent_emails_history.json"))

DEFAULT_SUBJECT = "[Collab Invite] Upcoming Beauty & Skincare Brand Campaigns for {name} 🎁✨"

DEFAULT_TEMPLATE = """Hey {name},

Hope you're having a great week! ✨

We’ve been following your content on Instagram (@{handle}) and love your aesthetic in the {niche} space.

We’re Creator Orbit (https://thecreatororbit.vercel.app/), a creator marketing agency partnering with fast-growing Indian D2C beauty, skincare, and lifestyle brands.

We are currently onboarding creators to our Official Creator Network for upcoming barter seeding & paid campaigns launching this month!

🌟 What you get as part of the Creator Orbit Network:
• 🎁 Free PR Hampers & Barter Seeding (Full-size premium products shipped direct to you)
• 💰 Paid Brand Collaborations & Whitelisting Deals
• ⏱️ Zero Follow-up Chaos (Dedicated campaign managers & clear, hassle-free briefs)
• 🚀 Regular, consistent campaign opportunities across top Indian D2C brands

👉 How to join our Creator Network (Takes 60 seconds):
Please fill out our quick Creator Onboarding Form so we have your preferred delivery address and content preferences on file:
🔗 {form_url}

📲 Connect with us on Instagram for live campaign calls:
https://www.instagram.com/thecreatororbit

We’d love to have you onboard and look forward to sending some exciting campaigns and hampers your way! 💫

Warm regards,

Creator Outreach Team
Creator Orbit Media
🌐 thecreatororbit.vercel.app
📸 @thecreatororbit
✉️ thecreatororbit.media@gmail.com
"""

def load_sent_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sent_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_eligible_creators(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, platform_id, description, extra_data FROM creators WHERE extra_data IS NOT NULL")
    
    rows = cur.fetchall()
    conn.close()
    
    sent_history = load_sent_history()
    eligible = []
    
    for cid, name, platform_id, desc, extra_json in rows:
        try:
            extra = json.loads(extra_json)
        except:
            continue
            
        email = extra.get("bio_email") or ""
        email = email.strip().lower()
        
        # Simple email validation
        if not email or "@" not in email or "." not in email or " " in email:
            continue
            
        # Skip if already sent
        if email in sent_history:
            continue
            
        handle = platform_id if platform_id else name
        creator_name = name if name and name.lower() != "none" else handle
        
        # Extract niche from extra or desc
        categories = extra.get("categories", [])
        niche = ", ".join(categories[:2]) if categories else "Beauty & Skincare"
        
        eligible.append({
            "id": cid,
            "name": creator_name,
            "handle": handle,
            "email": email,
            "niche": niche,
            "city": extra.get("city", "")
        })
        
        if len(eligible) >= limit:
            break
            
    return eligible

def send_bulk_emails(form_url="https://forms.gle/your-form-url", limit=50, dry_run=True, delay_range=(12, 20)):
    sender_email = os.getenv("SENDER_EMAIL", "thecreatororbit.media@gmail.com")
    app_password = os.getenv("SENDER_APP_PASSWORD", "")
    
    creators = get_eligible_creators(limit=limit)
    print(f"\n🚀 Found {len(creators)} eligible creators to email.")
    
    if not creators:
        print("No new eligible creators found. All available emails have already been reached or none are in DB.")
        return
        
    if dry_run:
        print("\n" + "="*70)
        print("🧪 RUNNING IN DRY-RUN MODE (No actual emails will be sent)")
        print("="*70)
        sample = creators[0]
        sample_subject = DEFAULT_SUBJECT.format(name=sample["name"], handle=sample["handle"])
        sample_body = DEFAULT_TEMPLATE.format(
            name=sample["name"],
            handle=sample["handle"],
            niche=sample["niche"],
            form_url=form_url
        )
        print(f"\n[Sample Email to: {sample['name']} <{sample['email']}>]")
        print(f"Subject: {sample_subject}\n")
        print(sample_body)
        print("="*70)
        print(f"Total recipients ready: {len(creators)}")
        print("\nTo send real emails, run with: python scripts/bulk_email_outreach.py --send")
        return

    # Real send mode
    if not app_password:
        print("\n❌ ERROR: SENDER_APP_PASSWORD not set in environment.")
        print("Please set your Gmail App Password in .env file or run:")
        print("set SENDER_APP_PASSWORD=your_16_digit_app_password")
        return

    print(f"\nConnecting to SMTP server with {sender_email}...")
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        print("✅ SMTP Login successful! Starting outreach...")
    except Exception as e:
        print(f"❌ Failed to connect to Gmail SMTP: {e}")
        return

    sent_history = load_sent_history()
    success_count = 0

    for i, c in enumerate(creators, 1):
        try:
            subject = DEFAULT_SUBJECT.format(name=c["name"], handle=c["handle"])
            body = DEFAULT_TEMPLATE.format(
                name=c["name"],
                handle=c["handle"],
                niche=c["niche"],
                form_url=form_url
            )
            
            msg = MIMEMultipart()
            msg["From"] = f"Creator Orbit <{sender_email}>"
            msg["To"] = c["email"]
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            server.sendmail(sender_email, [c["email"]], msg.as_string())
            
            sent_history[c["email"]] = {
                "name": c["name"],
                "handle": c["handle"],
                "sent_at": datetime.now().isoformat()
            }
            save_sent_history(sent_history)
            
            success_count += 1
            print(f"[{i}/{len(creators)}] ✅ Sent to {c['name']} ({c['email']})")
            
            if i < len(creators):
                sleep_time = random.uniform(delay_range[0], delay_range[1])
                print(f"   ⏳ Waiting {sleep_time:.1f}s to ensure high deliverability...")
                time.sleep(sleep_time)
                
        except Exception as e:
            print(f"[{i}/{len(creators)}] ❌ Failed to send to {c['email']}: {e}")

    server.quit()
    print(f"\n🎉 Outreach complete! Successfully sent {success_count}/{len(creators)} emails.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Creator Orbit Bulk Email Outreach Engine")
    parser.add_argument("--send", action="store_true", help="Execute actual email sending (default is dry-run)")
    parser.add_argument("--limit", type=int, default=50, help="Number of emails to send in this batch (default: 50)")
    parser.add_argument("--form", type=str, default="https://thecreatororbit.vercel.app/", help="Onboarding Form URL")
    
    args = parser.parse_args()
    send_bulk_emails(form_url=args.form, limit=args.limit, dry_run=not args.send)

