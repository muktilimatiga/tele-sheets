import os
import json
import re
from datetime import datetime
from pytz import timezone
from collections import defaultdict
from dotenv import load_dotenv
from telethon import TelegramClient, events
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# === Load ENV ===
load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
spreadsheet_id = os.getenv("SPREADSHEET_ID")

if not api_id or not api_hash:
    raise ValueError("API_ID and API_HASH must be set in .env")

service_account_file = "credentials.json"
target_group_id = 398840035
session_name = "sessions/session_name"

# Ensure session folder exists
os.makedirs(os.path.dirname(session_name), exist_ok=True)

# === Output paths ===
output_dir = "output"
output_komplain = os.path.join(output_dir, "data_sementara.json")
output_psb = os.path.join(output_dir, "data_psb.json")
os.makedirs(output_dir, exist_ok=True)

# === Keywords ===
filter_keywords_komplain = [
    "FORWARD TO NOC",
    "PROCESSED BY NOC",
    "CLOSED BY NOC",
    "FORWARD TO TECHNICIAN",
]

filter_keywords_psb = [
    "PROSES TICKET PSB"
]

# === JSON Utility ===
def append_to_json(filepath, data):
    try:
        with open(filepath, "r+", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
            existing_data.append(data)
            f.seek(0)
            json.dump(existing_data, f, indent=4)
            f.truncate()
    except FileNotFoundError:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([data], f, indent=4)

# === Field Extraction Helpers ===
def extract_field(message, field):
    match = re.search(rf"{field}\s*:\s*(.+)", message, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def classify_status(message):
    upper = message.upper()
    if "FORWARD TO NOC" in upper:
        return "open"
    elif "PROCESSED BY" in upper:
        return "proses"
    elif "CLOSED BY" in upper:
        return "done"
    elif "FORWARD TO TECHNICIAN" in upper:
        return "fwd teknis"
    elif "PROSES TICKET PSB" in upper:
        return "data psb"
    return ""

# === Data Conversion ===
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

def data_to_psb(item):
    nama = extract_field(item["message"], "Nama")
    alamat = extract_field(item["message"], "Alamat")
    user_ppoe = extract_field(item["message"], 'user ppoe')
    pass_ppoe = extract_field(item["message"], 'pass ppoe')
    return {
        "Tgl proses": item["timestamp"],
        "Nama": nama,
        "Alamat": alamat,
        "User PPPoE": user_ppoe,
        "Pass PPPoE": pass_ppoe
    }

# === Google Sheets Formatting ===
def format_status_cell(sheet_id, row_idx, status, color_map):
    if status not in color_map:
        return None
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row_idx - 1,
                "endRowIndex": row_idx,
                "startColumnIndex": 4,
                "endColumnIndex": 5
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": color_map[status]
                }
            },
            "fields": "userEnteredFormat.backgroundColor"
        }
    }

# === Google Sheets Helper ===
def get_sheet_id(service, spreadsheet_id, sheet_name):
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet["sheets"]:
        if sheet["properties"]["title"] == sheet_name:
            return sheet["properties"]["sheetId"]
    return None

def upload_to_google_sheets(data):
    if not os.path.exists(service_account_file):
        print(f"[!] {service_account_file} not found!")
        return False

    try:
        creds = Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        grouped = defaultdict(list)
        for item in data:
            tanggal, row = extract_row(item)
            current_date = datetime.now().strftime("%d-%B-%Y")
            grouped[current_date].append(row)

        color_map = {
            "open":       {"red": 0.2, "green": 0.6, "blue": 1.0},
            "proses":     {"red": 0.4, "green": 0.9, "blue": 0.4},
            "done":       {"red": 0.85, "green": 0.85, "blue": 0.85},
            "fwd teknis": {"red": 1.0, "green": 0.6, "blue": 0.6},
        }

        for sheet_name, rows in grouped.items():
            header = ["Tanggal", "Waktu", "Nama Pelanggan", "Kendala", "Status", "Action", "Note", "Nomor Tiket"]

            try:
                sheet.batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
                ).execute()
            except:
                pass

            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption="RAW",
                body={"values": [header]}
            ).execute()

            sheet_id = get_sheet_id(service, spreadsheet_id, sheet_name)
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A2:H"
            ).execute()
            existing_rows = result.get("values", [])

            ticket_map = {row[7]: idx + 2 for idx, row in enumerate(existing_rows) if len(row) >= 8}
            format_requests = []

            for row in rows:
                tiket = row[7]
                status, action, note = row[4], row[5], row[6]
                found = False

                if tiket in ticket_map:
                    row_idx = ticket_map[tiket]
                    update_range = f"{sheet_name}!E{row_idx}:H{row_idx}"
                    sheet.values().update(
                        spreadsheetId=spreadsheet_id,
                        range=update_range,
                        valueInputOption="RAW",
                        body={"values": [[status, action, note, tiket]]}
                    ).execute()
                    found = True

                if not found:
                    append_result = sheet.values().append(
                        spreadsheetId=spreadsheet_id,
                        range=f"{sheet_name}!A2",
                        valueInputOption="RAW",
                        insertDataOption="INSERT_ROWS",
                        body={"values": [row]}
                    ).execute()

                    match = re.search(rf"{sheet_name}!A(\d+)", append_result["updates"]["updatedRange"])
                    if match:
                        row_idx = int(match.group(1))
                        fmt = format_status_cell(sheet_id, row_idx, status, color_map)
                        if fmt:
                            format_requests.append(fmt)

            if format_requests:
                sheet.batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={"requests": format_requests}
                ).execute()

        return True

    except Exception as e:
        print(f"[!] Upload failed: {e}")

    return False

# === Telegram Listener ===
jakarta_tz = timezone("Asia/Jakarta")

client = TelegramClient(session_name, api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage(chats=target_group_id))
async def handle_message(event):
    message = event.message.text
    if not message:
        return

    upper_msg = message.upper()

    for keyword in filter_keywords_komplain:
        if keyword in upper_msg:
            data = {
                "timestamp": event.message.date.astimezone(jakarta_tz).strftime('%d-%B-%Y %H:%M'),
                "message": message,
            }
            append_to_json(output_komplain, data)
            print(f"[+] Saved KOMPLAIN: {data}")
            uploaded = upload_to_google_sheets([data])
            print(f"{'+' if uploaded else '!'} {'Uploaded' if uploaded else 'Failed to upload'} to Google Sheets")
            return

    for keyword in filter_keywords_psb:
        if keyword in upper_msg:
            timestamp = event.message.date.astimezone(jakarta_tz).strftime('%d-%B-%Y %H:%M')
            raw_data = {"message": message, "timestamp": timestamp}
            psb_data = data_to_psb(raw_data)
            append_to_json(output_psb, psb_data)
            print(f"[+] Saved PSB: {psb_data}")
            return

# === Main Entry Point ===
def main():
    print("[*] Listening for Telegram messages...")
    client.start()
    client.run_until_disconnected()
    print("[!] Disconnected.")

if __name__ == "__main__":
    main()
