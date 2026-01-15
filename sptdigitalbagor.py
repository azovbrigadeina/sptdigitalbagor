import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from PIL import Image
import datetime

# Kredensial
creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
drive_service = build('drive', 'v3', credentials=creds)
sheets_service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"
FOLDER_DRIVE_ID = "1zfMcewEJEcAiWZfmqF6rDAPSFUIGIlB3"

def upload_to_drive(img_bytes, filename):
    # 1. Metadata file tetap diarahkan ke folder Anda
    file_metadata = {
        'name': filename, 
        'parents': [FOLDER_DRIVE_ID]
    }
    
    media = MediaIoBaseUpload(img_bytes, mimetype='image/png')
    
    # 2. Upload file
    file = drive_service.files().create(
        body=file_metadata, 
        media_body=media, 
        fields='id, webViewLink',
        supportsAllDrives=True
    ).execute()
    
    file_id = file.get('id')

    # 3. SOLUSI PENTING: Berikan izin ke email pribadi Anda agar file "diakui" oleh folder induk
    # Ganti 'EMAIL_PRIBADI_ANDA@gmail.com' dengan email asli Anda
    user_permission = {
        'type': 'user',
        'role': 'owner', # Mencoba menjadikan Anda pemilik
        'emailAddress': 'EMAIL_PRIBADI_ANDA@gmail.com' 
    }
    
    try:
        # Pindahkan kepemilikan ke Anda agar kuota Service Account tidak terpakai
        drive_service.permissions().create(
            fileId=file_id,
            body=user_permission,
            transferOwnership=True,
            supportsAllDrives=True
        ).execute()
    except Exception as e:
        # Jika gagal transfer owner (karena beda domain), minimal jadikan akun Anda editor
        user_permission['role'] = 'writer'
        drive_service.permissions().create(
            fileId=file_id,
            body=user_permission,
            supportsAllDrives=True
        ).execute()

    return file.get('webViewLink')
    
    st.title("Form Surat Perintah Tugas")
st.info("Pendataan Admin OPD SIMONA E-ANJAB-ABK 2026")

with st.form("spt_form"):
    st.subheader("I. Data Admin OPD")
    opd = st.selectbox("Pilih OPD", ["Dinas Kesehatan", "Kecamatan Kumpeh", "Bagian Hukum"]) # Lengkapi listnya
    nama = st.text_input("Nama Lengkap dan Gelar")
    nip = st.text_input("NIP (Angka saja)")
    pangkat = st.text_input("Pangkat / Golongan")
    jabatan = st.text_input("Jabatan")
    no_hp = st.text_input("Nomor Handphone")
    email = st.text_input("Email")
    
    st.subheader("II. Data Atasan Langsung")
    nama_atasan = st.text_input("Nama Atasan")
    nip_atasan = st.text_input("NIP Atasan")
    pangkat_atasan = st.text_input("Pangkat Atasan")
    jabatan_atasan = st.text_input("Jabatan Atasan")
    
    st.subheader("III. Tanda Tangan")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=450, key="ttd")
    
    submit = st.form_submit_button("Kirim Sekarang")

if submit:
    if not nip.isdigit() or not nip_atasan.isdigit():
        st.error("NIP harus berupa angka!")
    elif canvas_result.image_data is not None:
        # Proses Gambar
        img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        # Upload & Simpan
        link_drive = upload_to_drive(buf, f"TTD_{nama}_{nip}.png")
        row_data = [[
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            opd, nama, nip, pangkat, jabatan, no_hp, email, 
            nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan, link_drive
        ]]
        
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
            valueInputOption="RAW", body={'values': row_data}).execute()
            
        st.success("✅ Berhasil! Data dan Tanda Tangan telah tersimpan.")
        st.balloons()
