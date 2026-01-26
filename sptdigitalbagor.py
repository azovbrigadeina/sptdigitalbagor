import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
from io import BytesIO
from PIL import Image
from docxtpl import DocxTemplate, InlineImage
from reportlab.lib.units import Mm
import os

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
        else:
            return None
    except Exception as e:
        st.error(f"Error Koneksi Google Sheets: {e}")
        return None

sheets_service = get_sheets_service()
SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

# --- 3. FUNGSI GENERATE DOCX (MAIL MERGE) ---
def create_docx_from_template(data, signature_img):
    try:
        # Muat template Word
        doc = DocxTemplate("templatespt.docx")
        
        # Proses Tanda Tangan
        img_obj = ""
        if signature_img:
            # Simpan sementara untuk diinsert ke Word
            temp_path = "temp_sig.png"
            signature_img.save(temp_path)
            # Ukuran lebar 40mm (4cm)
            img_obj = InlineImage(doc, temp_path, width=Mm(40))

        # Data Mapping (Isi {{ tag }} di Word)
        context = {
            'perihal': data['perihal'],
            'opd': data['opd'],
            'nama': data['nama'],
            'nip': data['nip'],
            'pangkat': data['pangkat'],
            'jabatan': data['jabatan'],
            'no_hp': data['no_hp'],
            'email': data['email'],
            'nama_atasan': data['nama_atasan'],
            'nip_atasan': data['nip_atasan'],
            'pangkat_atasan': data['pangkat_atasan'],
            'jabatan_atasan': data['jabatan_atasan'].upper(),
            'tanggal': datetime.datetime.now().strftime('%d %B %Y'),
            'ttd': img_obj
        }

        doc.render(context)
        
        target_stream = BytesIO()
        doc.save(target_stream)
        target_stream.seek(0)
        
        # Hapus file sementara
        if signature_img and os.path.exists("temp_sig.png"):
            os.remove("temp_sig.png")
            
        return target_stream
    except Exception as e:
        st.error(f"Gagal memproses template Word: {e}")
        return None

# --- 4. FUNGSI DIALOG ---
@st.dialog("✅ SPT Berhasil Dibuat")
def show_success_dialog(nama_admin, docx_data):
    st.write(f"Halo **{nama_admin}**, data Anda telah disimpan.")
    st.success("Silakan unduh dokumen SPT (Word) Anda di bawah ini:")
    
    st.download_button(
        label="📥 Download SPT (DOCX)",
        data=docx_data,
        file_name=f"SPT_{nama_admin.replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    if st.button("Tutup"):
        st.rerun()

# --- 5. DATA LIST OPD ---
list_opd = ["Bagian Organisasi", "Dinas Pendidikan", "Dinas Kesehatan", "RSUD Ahmad Ripin"] # Sederhanakan untuk contoh

# --- 6. TAMPILAN APLIKASI ---
st.title("📝 Form SPT Admin OPD")

st.header("I. Perihal Surat Tugas")
perihal_spt = st.selectbox("Pilih Perihal:", ["SPT Rekon TPP dan SIMONA"])

st.header("II. Unit Kerja")
opsi_opd = st.selectbox("Pilih Unit Kerja:", [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"])
opd_final = st.text_input("Tulis Nama OPD:") if opsi_opd == "Lainnya (Isi Manual)" else opsi_opd

with st.form("spt_form"):
    st.header("III. Data Admin")
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("Nama Lengkap")
        nip = st.text_input("NIP", max_chars=18)
    with col2:
        pangkat = st.text_input("Pangkat")
        jabatan = st.text_input("Jabatan")
    
    no_hp = st.text_input("WhatsApp")
    email = st.text_input("Email")

    st.header("IV. Data Atasan")
    nama_atasan = st.text_input("Nama Atasan")
    nip_atasan = st.text_input("NIP Atasan")
    jabatan_atasan = st.text_input("Jabatan Atasan")
    pangkat_atasan = st.text_input("Pangkat Atasan")

    st.header("V. Tanda Tangan")
    canvas_result = st_canvas(height=150, width=300, drawing_mode="freedraw", key="canvas")

    submit = st.form_submit_button("Generate SPT", type="primary")

if submit:
    if not opd_final or not nama:
        st.error("Lengkapi data!")
    else:
        img_ttd = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        data_spt = {
            'perihal': perihal_spt, 'opd': opd_final, 'nama': nama, 'nip': nip,
            'pangkat': pangkat, 'jabatan': jabatan, 'no_hp': no_hp, 'email': email,
            'nama_atasan': nama_atasan, 'nip_atasan': nip_atasan, 
            'jabatan_atasan': jabatan_atasan, 'pangkat_atasan': pangkat_atasan
        }
        
        docx_file = create_docx_from_template(data_spt, img_ttd)
        
        if docx_file:
            # Simpan ke Sheets (Logika sama seperti sebelumnya)
            # ...
            show_success_dialog(nama, docx_file)
