import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from PIL import Image
import pandas as pd
import datetime

# --- SETUP KREDENSIAL ---
creds_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(creds_info)
drive_service = build('drive', 'v3', credentials=creds)
sheets_service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"
FOLDER_DRIVE_ID = "1zfMcewEJEcAiWZfmqF6rDAPSFUIGIlB3"

def upload_ttd_to_drive(img_bytes, filename):
    file_metadata = {'name': filename, 'parents': [FOLDER_DRIVE_ID]}
    media = MediaIoBaseUpload(img_bytes, mimetype='image/png')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    return file.get('webViewLink')

# --- FORM UI ---
st.title("Form Surat Perintah Tugas")
with st.form("main_form"):
    # ... (Masukkan semua input text: OPD, Nama, NIP, dsb sesuai list sebelumnya) ...
    opd = st.selectbox("Pilih OPD", ["Dinas Kesehatan", "Kecamatan Kumpeh"]) # Contoh singkat
    nama = st.text_input("Nama Lengkap")
    nip = st.text_input("NIP")
    # ... tambahkan field lainnya ...
    
    st.write("### Tanda Tangan")
    canvas_result = st_canvas(height=150, width=500, drawing_mode="freedraw", key="canvas")
    
    submit = st.form_submit_button("Kirim")

if submit:
    if canvas_result.image_data is not None and nama:
        # 1. Olah Gambar
        img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        # 2. Upload Drive
        link_ttd = upload_ttd_to_drive(buf, f"TTD_{nama}_{nip}.png")
        
        # 3. Kirim ke Sheets (Append Row)
        values = [[datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), opd, nama, nip, link_ttd]]
        body = {'values': values}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
            valueInputOption="RAW", body=body).execute()
            
        st.success("✅ Sukses! Data & Tanda Tangan tersimpan.")
