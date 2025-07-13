import json
import os
from datetime import datetime
from collections import defaultdict
from pytz import timezone
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()


load_dotenv()
# === CONFIG ===
service_account_file = "credentials.json"
spreadsheet_id = os.getenv("SPREADSHEET_ID")
jakarta_tz = timezone("Asia/Jakarta")

header = ["Tanggal", "Waktu", "Nama Pelanggan", "Kendala", "Status", "Action", "Note", "Nomor Tiket"]

def input_manual_data():
    now = datetime.now(jakarta_tz)
    tanggal = now.strftime("%d-%B-%Y")
    waktu = now.strftime("%H:%M")

    nama = input("Nama Pelanggan: ")
    kendala = input("Kendala: ")
    status = input("Status (open/proses/done): ").lower()
    action = input("Action: ")
    note = input("Note: ")
    tiket = input("Nomor Tiket: ")

    return [tanggal, waktu, nama, kendala, status, action, note, tiket]

def get_sheet_id(service, spreadsheet_id, sheet_name):
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet["sheets"]:
        if sheet["properties"]["title"] == sheet_name:
            return sheet["properties"]["sheetId"]
    return None

def upload_to_google_sheets(row):
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

        sheet_name = row[0]  # Tanggal as sheet name

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

        if row[7] in ticket_map:
            row_idx = ticket_map[row[7]]
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!E{row_idx}:H{row_idx}",
                valueInputOption="RAW",
                body={"values": [[row[4], row[5], row[6], row[7]]]}
            ).execute()
        else:
            sheet.values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A2",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]}
            ).execute()

        # Bold the header row
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

        print("[+] Data uploaded successfully")
        return True

    except Exception as e:
        print(f"[!] Upload failed: {e}")
        return False

if __name__ == "__main__":
    print("[*] Manual Data Entry Mode")
    data = input_manual_data()
    upload_to_google_sheets(data)
