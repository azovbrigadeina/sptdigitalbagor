import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
from io import BytesIO
from PIL import Image
from docxtpl import DocxTemplate, InlineImage
from reportlab.lib.units import mm  # mm di sini adalah nilai float (2.8346...)
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

# --- 3. FUNGSI GENERATE DOCX ---
def create_docx_from_template(data, signature_img):
    try:
        # Nama file template di GitHub
        doc = DocxTemplate("template spt simona.docx")
        
        img_obj = ""
        if signature_img:
            temp_path = "temp_sig.png"
            signature_img.save(temp_path)
            
            # PERBAIKAN DI SINI: Gunakan perkalian (40 * mm), bukan mm(40)
            img_obj = InlineImage(doc, temp_path, width=40 * mm) 

        # Mapping data ke {{ tag }} di Word
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
        
        if os.path.exists("temp_sig.png"):
            os.remove("temp_sig.png")
            
        return target_stream
    except Exception as e:
        st.error(f"Gagal memproses template Word: {e}")
        return None

# --- 4. DATA LIST OPD ---
list_opd = [
    "Bagian Organisasi", "Bagian Umum", "Bagian Tata Pemerintahan",
    "Dinas Pendidikan dan Kebudayaan", "Dinas Kesehatan", "RSUD Ahmad Ripin"
] 

# --- 5. TAMPILAN UTAMA ---
st.title("📝 Form SPT Admin OPD")
st.write("---")

st.header("I. Perihal Surat Tugas")
perihal_spt = st.selectbox("Pilih Perihal:", ["SPT Rekon TPP dan SIMONA"])

st.header("II. Unit Kerja")
opsi_opd = st.selectbox("Pilih Unit Kerja / OPD:", [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"])
opd_final = st.text_input("Tulis Nama Unit Kerja:") if opsi_opd == "Lainnya (Isi Manual)" else opsi_opd

st.write("---")

with st.form("spt_form"):
    st.header("III. Data Admin (Penerima Tugas)")
    status_asn = st.radio("Status ASN:", ["PNS", "PPPK"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("Nama Lengkap & Gelar")
        pangkat = st.text_input("Pangkat / Golongan")
        no_hp = st.text_input("No. WhatsApp")
    with col2:
        nip = st.text_input("NIP Admin (18 Digit)", max_chars=18)
        jabatan = st.text_input("Jabatan")
        email = st.text_input("Email Aktif")

    st.write("---")
    st.header("IV. Data Atasan Pemberi Perintah")
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan = st.text_input("Nama Atasan & Gelar")
        pangkat_atasan = st.text_input("Pangkat Atasan")
    with col4:
        nip_atasan = st.text_input("NIP Atasan (18 Digit)", max_chars=18)
        jabatan_atasan = st.text_input("Jabatan Atasan")

    st.write("---")
    st.header("V. Tanda Tangan Atasan")
    canvas_result = st_canvas(
        stroke_width=2, stroke_color="#000000", background_color="#ffffff",
        height=150, width=300, drawing_mode="freedraw", key="canvas_ttd"
    )

    submit_button = st.form_submit_button("Generate & Kirim SPT", type="primary")

if submit_button:
    if not opd_final or not nama or not nip:
        st.error("Mohon lengkapi data wajib!")
    else:
        try:
            with st.spinner('Memproses dokumen...'):
                img_ttd = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                
                data_spt = {
                    'perihal': perihal_spt, 'opd': opd_final, 'nama': nama, 
                    'nip': nip, 'pangkat': pangkat, 'jabatan': jabatan, 
                    'no_hp': no_hp, 'email': email, 'nama_atasan': nama_atasan, 
                    'nip_atasan': nip_atasan, 'jabatan_atasan': jabatan_atasan, 
                    'pangkat_atasan': pangkat_atasan
                }

                docx_file = create_docx_from_template(data_spt, img_ttd)
                
                if docx_file:
                    if sheets_service:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        row = [[now, perihal_spt, opd_final, status_asn, f"'{nip}", nama, pangkat, jabatan, no_hp, email, f"'{nip_atasan}", nama_atasan]]
                        sheets_service.spreadsheets().values().append(
                            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                            valueInputOption="USER_ENTERED", body={'values': row}
                        ).execute()
                    
                    st.balloons()
                    st.success("SPT Berhasil Dibuat!")
                    st.download_button(
                        label="📥 Download SPT (Word)",
                        data=docx_file,
                        file_name=f"SPT_{nama.replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {e}")
