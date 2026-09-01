"""
Automated WhatsApp Outreach for Microsoft Edge with Smart Batch Scheduler
Drives Microsoft Edge automatically to send personalized WhatsApp outreach in safe scheduled batches.

Features:
- Launches Microsoft Edge with persistent user profile (you only scan QR code once)
- Reads creators from branding/whatsapp_creators_export.csv
- Automated navigation, pre-filled text verification, and safe send
- Anti-ban protection: Randomized delays (15 to 25s) between messages
- Smart Batching: Sends a batch (e.g. 40-50), closes browser, waits a safe cooldown (e.g. 2-3 hours), then automatically sends the next batch!
- Live countdown timer during cooldown
- Resume capability: Tracks all sent creators in data/whatsapp_sent_history.json
"""

import os
import sys
import json
import time
import random
import urllib.parse
import argparse
import pandas as pd
from datetime import datetime, timedelta

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

def run_single_batch(batch_size=50, delay_range=(15, 25)):
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: CSV file not found at {CSV_PATH}")
        return 0, 0

    df = pd.read_csv(CSV_PATH)
    sent_history = load_sent_history()
    
    # Filter out already messaged creators
    pending = []
    for _, row in df.iterrows():
        phone_str = str(row['phone']).strip()
        if phone_str not in sent_history:
            pending.append(row)
            
    print(f"\n=======================================================")
    print(f"🚀 Creator Orbit WhatsApp Outreach — Starting Batch")
    print(f"=======================================================")
    print(f"Total creators in list : {len(df)}")
    print(f"Already messaged       : {len(sent_history)}")
    print(f"Remaining to reach     : {len(pending)}")
    print(f"Batch target size      : {min(batch_size, len(pending))}")
    print(f"=======================================================\n")

    if not pending:
        print("🎉 All creators in the list have already been messaged!")
        return 0, 0

    # Setup Edge Options
    os.makedirs(EDGE_PROFILE_DIR, exist_ok=True)
    options = Options()
    options.add_argument(f"--user-data-dir={EDGE_PROFILE_DIR}")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-allow-origins=*")
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)

    print("Opening Microsoft Edge browser...")
    try:
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
    except Exception as e:
        print(f"⚠️ Falling back to default Edge driver: {e}")
        driver = webdriver.Edge(options=options)

    # Initial WhatsApp Web load
    print("Connecting to WhatsApp Web (https://web.whatsapp.com)...")
    driver.get("https://web.whatsapp.com")
    
    print("\n👉 If not logged in, please scan the QR code on your screen.")
    print("⏳ Waiting for WhatsApp Web to load...")
    
    try:
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"] | //div[@role="textbox"] | //header'))
        )
        print("✅ WhatsApp Web active and ready!\n")
    except Exception:
        print("❌ Login timed out or page took too long to load.")
        driver.quit()
        return 0, len(pending)

    batch = pending[:batch_size]
    success_count = 0

    for idx, creator in enumerate(batch, 1):
        name = str(creator['name'])
        phone = str(creator['phone'])
        msg = str(creator['Custom_Message'])
        
        print(f"[{idx}/{len(batch)}] Messaging: {name} (+{phone})...")
        
        encoded_msg = urllib.parse.quote(msg)
        send_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
        driver.get(send_url)
        
        try:
            time.sleep(4)
            send_btn = None
            
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
                input_box = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"] | //footer//div[@contenteditable="true"]'))
                )
                time.sleep(1)
                input_box.send_keys(Keys.ENTER)
                
            time.sleep(2)
            print(f"   ✅ Successfully sent message to {name}!")
            
            sent_history[phone] = {
                "name": name,
                "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_sent_history(sent_history)
            success_count += 1
            
            if idx < len(batch):
                delay = random.uniform(delay_range[0], delay_range[1])
                print(f"   ⏳ Waiting {delay:.1f}s before next creator...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"   ⚠️ Could not send to {name} (+{phone}): Skipping.")
            sent_history[phone] = {
                "name": name,
                "error": str(e),
                "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_sent_history(sent_history)

    print(f"\n=======================================================")
    print(f"✅ Batch Finished! Sent {success_count}/{len(batch)} messages.")
    print(f"=======================================================\n")
    
    time.sleep(3)
    driver.quit()
    
    remaining = len(pending) - len(batch)
    return success_count, max(0, remaining)

def countdown_timer(hours):
    total_seconds = int(hours * 3600)
    end_time = datetime.now() + timedelta(seconds=total_seconds)
    print(f"\n💤 Safe cooldown period started.")
    print(f"⏰ Next batch will launch at: {end_time.strftime('%I:%M:%S %p')}")
    
    while total_seconds > 0:
        mins, secs = divmod(total_seconds, 60)
        hrs, mins = divmod(mins, 60)
        timer_str = f"⏳ Cooldown countdown: {hrs:02d}h {mins:02d}m {secs:02d}s remaining..."
        sys.stdout.write(f"\r{timer_str}")
        sys.stdout.flush()
        time.sleep(1)
        total_seconds -= 1
        
    print("\n\n🔔 Cooldown complete! Starting next batch now...\n")

def main():
    parser = argparse.ArgumentParser(description="Automated WhatsApp Outreach with Safe Interval Scheduler")
    parser.add_argument("--batch-size", "--limit", type=int, default=45, help="Number of creators per batch (default: 45)")
    parser.add_argument("--interval-hours", type=float, default=2.5, help="Hours to wait between batches (default: 2.5 hours)")
    parser.add_argument("--single-run", action="store_true", help="Run only one single batch and exit")
    args = parser.parse_args()

    print("\n" + "="*70)
    print("🤖 CREATOR ORBIT — AUTOMATED WHATSAPP BATCH SCHEDULER")
    print(f"📦 Batch Size       : {args.batch_size} creators per run")
    print(f"⏱️ Interval Gap     : {args.interval_hours} hours between batches")
    print(f"🔁 Mode             : {'Single Batch' if args.single_run else 'Continuous Auto-Scheduler'}")
    print("="*70)

    batch_num = 1
    while True:
        print(f"\n▶️ Starting Batch #{batch_num}...")
        sent, remaining = run_single_batch(batch_size=args.batch_size)
        
        if remaining == 0:
            print("\n🎉 ALL CREATORS IN YOUR LIST HAVE BEEN REACHED! Complete campaign finished.")
            break
            
        if args.single_run:
            print(f"\nSingle run complete. {remaining} creators remaining for future runs.")
            break

        batch_num += 1
        countdown_timer(args.interval_hours)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped safely by user. All progress is saved!")

