# telegram_client_full.py
import os
import re
from datetime import datetime
from pytz import timezone
from collections import defaultdict
from dotenv import load_dotenv
from telethon import TelegramClient, events
from pymongo import MongoClient
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# === Load Environment Variables ===
load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
spreadsheet_id = os.getenv("SPREADSHEET_ID")
MONGO_URI = os.getenv("MONGO_URI")

if not all([api_id, api_hash, spreadsheet_id, MONGO_URI]):
    raise ValueError("API_ID, API_HASH, SPREADSHEET_ID, and MONGO_URI must be set in .env")

# === Script Configuration ===
service_account_file = "credentials.json"
target_group_id = 398840035
session_name = "sessions/session_name"
os.makedirs(os.path.dirname(session_name), exist_ok=True)

# === Direct Database Connection ===
try:
    print("Connecting to MongoDB...")
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.get_database("telegram_data")
    komplain_collection = db.get_collection("komplain")
    mongo_client.admin.command('ping')
    print("MongoDB connection successful.")
except Exception as e:
    print(f"Error: Could not connect to MongoDB. {e}")
    exit()

# === Keywords ===
filter_keywords_komplain = [
    "FORWARD TO NOC", "PROCESSED BY NOC", "CLOSED BY NOC", "FORWARD TO TECHNICIAN",
]

# === Field Extraction & Data Conversion (No Changes Needed) ===
def extract_field(message, field):
    match = re.search(rf"{field}\s*:\s*(.+)", message, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def classify_status(message):
    upper = message.upper()
    if "FORWARD TO NOC" in upper: return "open"
    if "PROCESSED BY" in upper: return "proses"
    if "CLOSED BY" in upper: return "done"
    if "FORWARD TO TECHNICIAN" in upper: return "fwd teknis"
    return ""

def extract_row(item):
    msg = item["message"]
    dt = datetime.strptime(item["timestamp"], "%d-%B-%Y %H:%M")
    tanggal = dt.strftime("%d-%B-%Y")
    waktu = dt.strftime("%H:%M")
    nama = extract_field(msg, "Nama")
    kendala = extract_field(msg, "Desc")
    status = classify_status(msg)
    action = extract_field(msg, "Action") or "-"
    note = " "
    tiket = extract_field(msg, 'Ref')
    return tanggal, [tanggal, waktu, nama, kendala, status, action, note, tiket]

# (Keep all your Google Sheets functions exactly as they were)
# format_status_cell, get_sheet_id, and upload_to_google_sheets...
def get_sheet_id(service, spreadsheet_id, sheet_name):
    # ... (your existing code)
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet["sheets"]:
        if sheet["properties"]["title"] == sheet_name:
            return sheet["properties"]["sheetId"]
    return None


def upload_to_google_sheets(data):
    # ... (your existing code for this function)
    # This function will be called directly after the DB insert.
    if not os.path.exists(service_account_file):
        print(f"[!] {service_account_file} not found!")
        return False
    # The rest of your function logic remains the same
    try:
        creds = Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=creds)
        # ... and so on
        return True
    except Exception as e:
        print(f"[GSHEETS ERROR] Upload failed: {e}")
        return False


# === Telegram Listener ===
jakarta_tz = timezone("Asia/Jakarta")
tg_client = TelegramClient(session_name, api_id, api_hash)

@tg_client.on(events.NewMessage(chats=target_group_id))
async def handle_message(event):
    message = event.message.text
    if not message:
        return

    upper_msg = message.upper()

    for keyword in filter_keywords_komplain:
        if keyword in upper_msg:
            # 1. Prepare the data object
            data = {
                "timestamp": event.message.date.astimezone(jakarta_tz).strftime('%d-%B-%Y %H:%M'),
                "message": message,
            }

            # 2. Insert into MongoDB
            try:
                result = komplain_collection.insert_one(data)
                print(f"[DB] Successfully inserted document with ID: {result.inserted_id}")
            except Exception as e:
                print(f"[DB ERROR] Failed to insert document. Error: {e}")

            # 3. Upload to Google Sheets
            print("[GSHEETS] Attempting to upload...")
            uploaded = upload_to_google_sheets([data]) # Pass the same data object
            if uploaded:
                print("[GSHEETS] Successfully uploaded to Google Sheets.")
            else:
                print("[GSHEETS] Failed to upload to Google Sheets.")
            
            return

# === Main Entry Point ===
def main():
    print("[*] Listening for Telegram messages...")
    tg_client.start()
    tg_client.run_until_disconnected()
    print("[!] Disconnected.")
    mongo_client.close() # Close the DB connection when the script stops

if __name__ == "__main__":
    main()
