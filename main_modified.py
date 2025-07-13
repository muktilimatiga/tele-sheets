import os
import json
import re
from datetime import datetime
from pytz import timezone
from collections import defaultdict
from dotenv import load_dotenv
from telethon.sync import TelegramClient, events
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# === Load ENV ===
load_dotenv()
api_id_str = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
spreadsheet_id = os.getenv("SPREADSHEET_ID")
service_account_file = "credentials.json"
target_group_name = 2570987538
session_name = "session_name"
output_file = "output/data_sementara.json"

if not api_id_str or not api_hash or not spreadsheet_id:
    raise EnvironmentError("Missing .env variables: API_ID, API_HASH, SPREADSHEET_ID")

api_id = int(api_id_str)

filter_keywords = [
    "FORWARD TO NOC",
    "PROCESSED BY NOC",
    "CLOSED BY NOC",
    "FORWARD TO TECHNICIAN",
]

os.makedirs(os.path.dirname(output_file), exist_ok=True)

# === Simpan data JSON lokal ===
def append_to_json(data):
    try:
        with open(output_file, "r+", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
            existing_data.append(data)
            f.seek(0)
            json.dump(existing_data, f, indent=4)
            f.truncate()
    except FileNotFoundError:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([data], f, indent=4)

# === Ekstrak data dari pesan ===
def extract_field(message, field):
    match = re.search(rf"{field}\s*:\s*(.+)", message, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def classify_status(message):
    upper = message.upper()
    if "FORWARD TO NOC" in upper:
        return "open"
    elif "PROCESSED BY" in upper:
        return "proses"
    elif "CLOSED BY" in upper or "FORWARD TO TECHNICIAN" in upper:
        return "done"
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

# === Ambil Sheet ID ===
def get_sheet_id(service, spreadsheet_id, sheet_name):
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet["sheets"]:
        if sheet["properties"]["title"] == sheet_name:
            return sheet["properties"]["sheetId"]
    return None

# === Upload ke Google Sheets ===
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
            "open":   {"red": 0.7, "green": 0.9, "blue": 1.0},  # light blue
            "proses": {"red": 0.8, "green": 1.0, "blue": 0.8},  # light green
            "done":   {"red": 1.0, "green": 1.0, "blue": 1.0},  # white
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
            sheet.batchUpdate(spreadsheetId=spreadsheet_id, body={
                "requests": [{
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "textFormat": {"bold": True}
                            }
                        },
                        "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
                    }
                }]
            }).execute()

            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A2:H"
            ).execute()
            existing_rows = result.get("values", [])

            ticket_map = {}
            for idx, row in enumerate(existing_rows):
                if len(row) >= 8:
                    ticket_map[row[7]] = idx + 2

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

                        if status in color_map:
                            format_requests.append({
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
                            })

            if format_requests:
                sheet.batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": format_requests}).execute()

        return True

    except Exception as e:
        print(f"[!] Upload failed: {e}")
        return False

# === Telegram Listener ===
jakarta_tz = timezone("Asia/Jakarta")

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=target_group_name))
async def handle_message(event):
    message = event.message
    if message.text:
        for keyword in filter_keywords:
            if keyword in message.text.upper():
                data = {
                    "timestamp": message.date.astimezone(jakarta_tz).strftime('%d-%B-%Y %H:%M'),
                    "message": message.text,
                }
                append_to_json(data)
                print(f"[+] Saved: {data}")
                success = upload_to_google_sheets([data])
                print(f"{'+' if success else '!'} {'Uploaded' if success else 'Failed to upload'} to Google Sheets")
                break

# === Jalankan ===
def main():
    print("[*] Connecting to Telegram...")
    with client:
        client.run_until_disconnected()
    print("[!] Disconnected from Telegram")

if __name__ == "__main__":
    main()
