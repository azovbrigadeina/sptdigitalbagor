import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
from io import BytesIO
from PIL import Image
from docxtpl import DocxTemplate, InlineImage
from reportlab.lib.units import mm
import os
import re

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered", page_icon="📝")

# --- 2. KONEKSI GOOGLE SHEETS ---
@st.cache_resource
def get_sheets_service():
    try:
        if "gcp_service_account" in st.secrets:
            cred_info = st.secrets["gcp_service_account"]
            creds = service_account.Credentials.from_service_account_info(cred_info)
            return build('sheets', 'v4', credentials=creds)
        return None
    except Exception as e:
        return None

sheets_service = get_sheets_service()
SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

# --- 3. FUNGSI GENERATE DOCX ---
def create_docx_from_template(data, signature_img):
    template_name = "template spt simona.docx" 
    
    if not os.path.exists(template_name):
        st.error(f"File '{template_name}' tidak ditemukan!")
        return None

    try:
        doc = DocxTemplate(template_name)
        
        img_obj = ""
        if signature_img:
            temp_path = "temp_signature.png"
            signature_img.save(temp_path)
            img_obj = InlineImage(doc, temp_path, width=40 * mm)

        context = {
            'Unit_Kerja': data['unit_kerja'],
            'nama_admin': data['nama'],
            'pangkat_admin': data['pangkat'],
            'NIP_admin': data['nip'],
            'Jabatan_admin': data['jabatan'],
            'no_hpadmin': data['no_hp'],
            'email_admin': data['email'],
            'JABATAN_ATASAN': data['j_atasan'],
            'NAMA_ATASAN': data['n_atasan'],
            'NIP_ATASAN': data['nip_atasan'],
            'PANGKAT_GOL_ATASAN': data['p_atasan'],
            'Tanggal_Bulan_Tahun': datetime.datetime.now().strftime('%d %B %Y'),
            'ttd': img_obj 
        }

        doc.render(context)
        
        target_stream = BytesIO()
        doc.save(target_stream)
        target_stream.seek(0)
        
        if os.path.exists("temp_signature.png"):
            os.remove("temp_signature.png")
            
        return target_stream
    except Exception as e:
        st.error(f"Gagal memproses template: {e}")
        return None

# --- 4. TAMPILAN FORM ---
st.title("📝 Form SPT Admin OPD")

# I. PERIHAL (Ditambahkan sebelum Unit Kerja)
st.header("I. Perihal Surat Tugas")
perihal_spt = st.selectbox("Pilih Perihal:", ["SPT Rekon TPP dan SIMONA"])

# II. UNIT KERJA
st.header("II. Unit Kerja")
list_opd = [
    "Bagian Organisasi", "Bagian Umum", "Bagian Tata Pemerintahan", 
    "Bagian Hukum", "Bagian Kesejahteraan Rakyat", "Dinas Pendidikan dan Kebudayaan", 
    "Dinas Kesehatan", "RSUD Ahmad Ripin"
]
opsi_opd = st.selectbox("Pilih Unit Kerja / OPD:", [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"])
unit_kerja_final = st.text_input("Tulis Nama OPD (Jika pilih Lainnya):") if opsi_opd == "Lainnya (Isi Manual)" else opsi_opd

with st.form("spt_form"):
    # III. DATA ADMIN
    st.header("III. Data Admin")
    col1, col2 = st.columns(2)
    with col1:
        nama_admin = st.text_input("Nama Lengkap Admin")
        # Validasi NIP: max_chars=18 dan help text
        nip_admin = st.text_input("NIP Admin", max_chars=18, help="Masukkan 18 digit angka NIP")
        no_hp = st.text_input("Nomor WhatsApp")
    with col2:
        pangkat_admin = st.text_input("Pangkat / Golongan Admin")
        jabatan_admin = st.text_input("Jabatan Admin")
        email = st.text_input("Alamat Email Admin")

    st.write("---")
    
    # IV. DATA ATASAN
    st.header("IV. Data Atasan")
    jabatan_atasan_input = st.text_input("Jabatan Atasan (Contoh: KEPALA BAGIAN ORGANISASI)")
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan_input = st.text_input("Nama Lengkap Atasan")
        pangkat_atasan_input = st.text_input("Pangkat / Golongan Atasan")
    with col4:
        nip_atasan_input = st.text_input("NIP Atasan", max_chars=18)

    st.write("---")
    
    # V. TANDA TANGAN
    st.header("V. Tanda Tangan Atasan")
    canvas_result = st_canvas(
        stroke_width=2, stroke_color="#000000", background_color="#ffffff", 
        height=150, width=300, drawing_mode="freedraw", key="canvas_ttd"
    )

    submit_button = st.form_submit_button("Generate & Kirim Data SPT", type="primary")

# --- 5. LOGIKA SUBMIT & VALIDASI ---
if submit_button:
    # Validasi NIP Admin (Harus angka dan 18 digit)
    is_nip_valid = nip_admin.isdigit() and len(nip_admin) == 18
    
    if not unit_kerja_final or not nama_admin or not nama_atasan_input:
        st.warning("⚠️ Mohon lengkapi data Unit Kerja, Nama Admin, dan Nama Atasan.")
    elif not is_nip_valid:
        st.error("❌ NIP Admin harus berupa angka dan berjumlah tepat 18 digit!")
    else:
        try:
            with st.spinner('Sedang memproses dokumen Word...'):
                img_ttd = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                
                data_spt = {
                    'unit_kerja': unit_kerja_final,
                    'nama': nama_admin,
                    'nip': nip_admin,
                    'pangkat': pangkat_admin,
                    'jabatan': jabatan_admin,
                    'no_hp': no_hp,
                    'email': email,
                    'j_atasan': jabatan_atasan_input,
                    'n_atasan': nama_atasan_input,
                    'nip_atasan': nip_atasan_input,
                    'p_atasan': pangkat_atasan_input
                }
                
                docx_file = create_docx_from_template(data_spt, img_ttd)
                
                if docx_file:
                    if sheets_service:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        row = [[now, perihal_spt, unit_kerja_final, nama_admin, f"'{nip_admin}", email, nama_atasan_input]]
                        sheets_service.spreadsheets().values().append(
                            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                            valueInputOption="USER_ENTERED", body={'values': row}
                        ).execute()
                    
                    st.success("✅ SPT Berhasil Dibuat!")
                    st.download_button(
                        label="📥 Download SPT (Word)",
                        data=docx_file,
                        file_name=f"SPT_{nama_admin.replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {e}")
