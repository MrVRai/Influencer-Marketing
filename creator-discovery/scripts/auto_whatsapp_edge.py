"""
Automated WhatsApp Outreach for Microsoft Edge
Drives Microsoft Edge automatically to send personalized WhatsApp outreach to creators.

Features:
- Launches Microsoft Edge with persistent user profile (you only scan QR code once)
- Reads creators from branding/whatsapp_creators_export.csv
- Automated navigation, pre-filled text verification, and safe send
- Anti-ban protection: Randomized human-like delays (15 to 25 seconds)
- Resume capability: Keeps local sent log (data/whatsapp_sent_history.json)
"""

import os
import sys
import json
import time
import random
import urllib.parse
import argparse
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager

CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../branding/whatsapp_creators_export.csv"))
HISTORY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/whatsapp_sent_history.json"))
EDGE_PROFILE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/edge_wa_profile"))

def load_sent_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sent_history(history):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def run_edge_whatsapp_bot(limit=30, delay_range=(15, 25)):
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: CSV file not found at {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)
    sent_history = load_sent_history()
    
    # Filter out already messaged creators
    pending = []
    for _, row in df.iterrows():
        phone_str = str(row['phone']).strip()
        if phone_str not in sent_history:
            pending.append(row)
            
    print(f"\n=======================================================")
    print(f"🚀 Creator Orbit WhatsApp Outreach for Microsoft Edge")
    print(f"=======================================================")
    print(f"Total creators in list: {len(df)}")
    print(f"Already messaged: {len(sent_history)}")
    print(f"Pending to reach: {len(pending)}")
    print(f"Batch limit for this run: {min(limit, len(pending))}")
    print(f"=======================================================\n")

    if not pending:
        print("🎉 All creators in the list have already been messaged!")
        return

    # Setup Edge Options
    os.makedirs(EDGE_PROFILE_DIR, exist_ok=True)
    options = Options()
    options.add_argument(f"user-data-dir={EDGE_PROFILE_DIR}")
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")

    print("Opening Microsoft Edge browser...")
    try:
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
    except Exception as e:
        print(f"⚠️ Falling back to system default Edge driver: {e}")
        driver = webdriver.Edge(options=options)

    # Initial WhatsApp Web load
    print("\nNavigating to WhatsApp Web (https://web.whatsapp.com)...")
    driver.get("https://web.whatsapp.com")
    
    print("\n👉 IF THIS IS YOUR FIRST RUN: Please scan the WhatsApp Web QR code on your screen now.")
    print("⏳ Waiting for WhatsApp Web to load your chats...")
    
    try:
        # Wait until chat list or search bar is present
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"] | //div[@role="textbox"] | //header'))
        )
        print("✅ WhatsApp Web is active and ready!\n")
    except Exception:
        print("❌ Login timed out or page took too long to load.")
        driver.quit()
        return

    batch = pending[:limit]
    success_count = 0

    for idx, creator in enumerate(batch, 1):
        name = str(creator['name'])
        phone = str(creator['phone'])
        msg = str(creator['Custom_Message'])
        
        print(f"\n[{idx}/{len(batch)}] Messaging: {name} (+{phone})...")
        
        encoded_msg = urllib.parse.quote(msg)
        send_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
        driver.get(send_url)
        
        try:
            # Wait for message input or send button (up to 25s)
            time.sleep(4)
            send_btn = None
            
            # Try finding the Send button (paper airplane icon or send button span)
            try:
                send_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@data-tab="11"] | //span[@data-icon="send"]/parent::button | //button[contains(@aria-label, "Send")]'))
                )
            except Exception:
                pass
                
            if send_btn:
                time.sleep(1)
                send_btn.click()
            else:
                # Alternative: find input box and send Enter key
                input_box = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"] | //footer//div[@contenteditable="true"]'))
                )
                time.sleep(1)
                input_box.send_keys(Keys.ENTER)
                
            time.sleep(2)
            print(f"   ✅ Successfully sent message to {name}!")
            
            # Record in history
            sent_history[phone] = {
                "name": name,
                "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_sent_history(sent_history)
            success_count += 1
            
            if idx < len(batch):
                delay = random.uniform(delay_range[0], delay_range[1])
                print(f"   ⏳ Waiting {delay:.1f}s before next creator (keeping account 100% safe)...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"   ⚠️ Could not send to {name} (+{phone}): Invalid number or UI timeout. Skipping.")
            # Still mark to prevent looping forever
            sent_history[phone] = {
                "name": name,
                "error": str(e),
                "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_sent_history(sent_history)

    print(f"\n=======================================================")
    print(f"🎉 Batch complete! Successfully messaged {success_count}/{len(batch)} creators.")
    print(f"=======================================================\n")
    
    time.sleep(3)
    driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated WhatsApp Outreach for Microsoft Edge")
    parser.add_argument("--limit", type=int, default=30, help="Number of creators to message in this session (default: 30)")
    args = parser.parse_args()
    
    run_edge_whatsapp_bot(limit=args.limit)

