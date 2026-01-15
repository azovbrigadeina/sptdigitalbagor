import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
import datetime
import base64
from io import BytesIO
from PIL import Image

# --- SETUP KREDENSIAL SHEETS SAJA ---
creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
sheets_service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

st.title("Form Surat Perintah Tugas")
st.markdown("Pendataan Admin OPD - Kabupaten Muaro Jambi")

with st.form("spt_form"):
    # ... (Gunakan input yang sama seperti sebelumnya) ...
    opd = st.selectbox("Pilih OPD", ["Kecamatan Kumpeh", "Dinas Kesehatan", "Lainnya..."])
    nama = st.text_input("Nama Lengkap dan Gelar")
    nip = st.text_input("NIP (Angka)")
    pangkat = st.text_input("Pangkat/Golongan")
    jabatan = st.text_input("Jabatan")
    no_hp = st.text_input("No HP")
    email = st.text_input("Email")
    
    st.subheader("Data Atasan Langsung")
    nama_atasan = st.text_input("Nama Atasan")
    nip_atasan = st.text_input("NIP Atasan")
    pangkat_atasan = st.text_input("Pangkat Atasan")
    jabatan_atasan = st.text_input("Jabatan Atasan")
    
    st.subheader("Tanda Tangan")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff", height=150, width=450, key="ttd")
    
    submit = st.form_submit_button("Kirim Sekarang")

if submit:
    if not nama or not nip or canvas_result.image_data is None:
        st.warning("Mohon lengkapi data dan tanda tangan!")
    else:
        try:
            # --- PROSES TANDA TANGAN JADI TEKS (BASE64) ---
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            # Mengubah gambar menjadi string teks panjang
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            data_ttd_statis = f"data:image/png;base64,{img_base64}"

            # --- SIMPAN KE GOOGLE SHEETS ---
            row_data = [[
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                opd, nama, nip, pangkat, jabatan, no_hp, email, 
                nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan, 
                data_ttd_statis  # Kode tanda tangan masuk ke sini
            ]]
            
            sheets_service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                valueInputOption="RAW", body={'values': row_data}).execute()
                
            st.success("✅ Berhasil! Data dan Tanda Tangan telah tersimpan di Spreadsheet.")
            st.balloons()
        except Exception as e:
            st.error(f"Gagal kirim data: {e}")
