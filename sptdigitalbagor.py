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
            # Menghasilkan gambar tanda tangan di Word
            img_obj = InlineImage(doc, temp_path, width=40 * mm)

        # MAPPING: Kunci di sini harus SAMA PERSIS dengan {{tag}} di Word
        # Contoh: 'Unit_Kerja' akan mengisi {{Unit_Kerja}}
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

# --- 4. TAMPILAN FORM (GAYA AWAL) ---
st.title("📝 Form SPT Admin OPD")
st.write("---")

st.header("I. Unit Kerja")
list_opd = ["Bagian Organisasi", "Bagian Umum", "Bagian Tata Pemerintahan", "Dinas Pendidikan", "Dinas Kesehatan"]
opsi_opd = st.selectbox("Pilih Unit Kerja / OPD:", [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"])
unit_kerja_final = st.text_input("Tulis Nama OPD:") if opsi_opd == "Lainnya (Isi Manual)" else opsi_opd

with st.form("spt_form"):
    st.header("II. Data Admin")
    col1, col2 = st.columns(2)
    with col1:
        nama_admin = st.text_input("Nama Admin")
        nip_admin = st.text_input("NIP Admin")
        no_hp = st.text_input("WhatsApp")
    with col2:
        pangkat_admin = st.text_input("Pangkat Admin")
        jabatan_admin = st.text_input("Jabatan Admin")
        email = st.text_input("Email Admin")

    st.write("---")
    st.header("III. Data Atasan")
    jabatan_atasan = st.text_input("Jabatan Atasan (CONTOH: KEPALA BAGIAN ORGANISASI)")
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan = st.text_input("Nama Lengkap Atasan")
        pangkat_atasan = st.text_input("Pangkat Atasan")
    with col4:
        nip_atasan = st.text_input("NIP Atasan")

    st.header("IV. Tanda Tangan")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000000", background_color="#ffffff", height=150, width=300, drawing_mode="freedraw", key="canvas_ttd")

    submit_button = st.form_submit_button("Simpan & Generate SPT", type="primary")

# --- 5. EKSEKUSI ---
if submit_button:
    if not unit_kerja_final or not nama_admin:
        st.warning("⚠️ Unit Kerja dan Nama Admin wajib diisi.")
    else:
        try:
            with st.spinner('Menghasilkan Word...'):
                img_ttd = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                data_spt = {
                    'unit_kerja': unit_kerja_final, 'nama': nama_admin, 'nip': nip_admin,
                    'pangkat': pangkat_admin, 'jabatan': jabatan_admin, 'no_hp': no_hp, 'email': email,
                    'j_atasan': jabatan_atasan, 'n_atasan': nama_atasan, 'nip_atasan': nip_atasan, 'p_atasan': pangkat_atasan
                }
                
                docx_file = create_docx_from_template(data_spt, img_ttd)
                
                if docx_file:
                    st.success("✅ SPT Berhasil Dibuat!")
                    st.download_button(
                        label="📥 Download SPT (Word)",
                        data=docx_file,
                        file_name=f"SPT_{nama_admin}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
        except Exception as e:
            st.error(f"Error: {e}")
