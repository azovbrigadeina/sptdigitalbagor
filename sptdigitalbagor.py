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
            # Tanda tangan dimasukkan ke tag {{ttd}}
            img_obj = InlineImage(doc, temp_path, width=40 * mm)

        # Mapping data ke Tag Word (Harus sesuai dengan yang Anda ketik di Word)
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

# --- 4. TAMPILAN FORM LENGKAP ---
st.title("📝 Form SPT Admin OPD")
st.write("Silakan lengkapi data di bawah ini untuk menghasilkan Surat Perintah Tugas.")

# Bagian Unit Kerja
st.header("I. Unit Kerja")
list_opd = [
    "Bagian Organisasi", "Bagian Umum", "Bagian Tata Pemerintahan", 
    "Bagian Hukum", "Bagian Kesejahteraan Rakyat", "Dinas Pendidikan dan Kebudayaan", 
    "Dinas Kesehatan", "RSUD Ahmad Ripin", "Dinas Pekerjaan Umum"
]
opsi_opd = st.selectbox("Pilih Unit Kerja / OPD:", [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"])
unit_kerja_input = st.text_input("Tulis Nama OPD (Jika pilih Lainnya):") if opsi_opd == "Lainnya (Isi Manual)" else opsi_opd

with st.form("spt_form"):
    # Bagian Data Admin
    st.header("II. Data Admin")
    col1, col2 = st.columns(2)
    with col1:
        nama_admin = st.text_input("Nama Lengkap Admin")
        nip_admin = st.text_input("NIP Admin")
        no_hp = st.text_input("Nomor WhatsApp")
    with col2:
        pangkat_admin = st.text_input("Pangkat / Golongan Admin")
        jabatan_admin = st.text_input("Jabatan Admin")
        email = st.text_input("Alamat Email Admin")

    st.write("---")
    
    # Bagian Data Atasan
    st.header("III. Data Atasan")
    jabatan_atasan_input = st.text_input("Jabatan Atasan (Contoh: KEPALA BAGIAN ORGANISASI)")
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan_input = st.text_input("Nama Lengkap Atasan")
        pangkat_atasan_input = st.text_input("Pangkat / Golongan Atasan")
    with col4:
        nip_atasan_input = st.text_input("NIP Atasan")

    st.write("---")
    
    # Bagian Tanda Tangan
    st.header("IV. Tanda Tangan Atasan")
    st.write("Gunakan mouse atau layar sentuh untuk menandatangani kotak di bawah:")
    canvas_result = st_canvas(
        stroke_width=2, 
        stroke_color="#000000", 
        background_color="#ffffff", 
        height=150, 
        width=300, 
        drawing_mode="freedraw", 
        key="canvas_ttd"
    )

    submit_button = st.form_submit_button("Generate & Kirim Data SPT", type="primary")

# --- 5. LOGIKA EKSEKUSI ---
if submit_button:
    if not unit_kerja_input or not nama_admin or not nama_atasan_input:
        st.warning("⚠️ Mohon lengkapi data Unit Kerja, Nama Admin, dan Nama Atasan.")
    else:
        try:
            with st.spinner('Sedang memproses dokumen Word...'):
                # Ubah hasil canvas menjadi gambar
                img_ttd = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                
                # Paketkan data
                data_spt = {
                    'unit_kerja': unit_kerja_input,
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
                    # Simpan data ke Google Sheets (Log)
                    if sheets_service:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        row = [[now, unit_kerja_input, nama_admin, f"'{nip_admin}", email, nama_atasan_input]]
                        sheets_service.spreadsheets().values().append(
                            spreadsheetId=SPREADSHEET_ID, 
                            range="Sheet1!A1", 
                            valueInputOption="USER_ENTERED", 
                            body={'values': row}
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
