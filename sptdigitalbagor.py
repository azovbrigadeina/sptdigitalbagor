import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Mm
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered", page_icon="📝")

# --- 2. KONEKSI GOOGLE SHEETS (Sesuai kode stabil Anda) ---
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

# --- 3. FUNGSI GENERATE (METODE MANUAL INJECTION) ---
def create_docx_final(data, signature_img):
    template_name = "template spt simona.docx" 
    if not os.path.exists(template_name):
        st.error("File template tidak ditemukan!")
        return None

    try:
        doc = Document(template_name)
        
        # MAPPING BARU (Pastikan lurus indentasinya)
        replacements = {
            '{{unitkerja}}': str(data['unit_kerja']),
            '{{nama_admin}}': str(data['nama']),
            '{{pangkat_admin}}': str(data['pangkat']),
            '{{NIP_admin}}': str(data['nip']),
            '{{Jabatanadmin}}': str(data['jabatan']),
            '{{no_hpadmin}}': str(data['no_hp']),
            '{{email_admin}}': str(data['email']),
            '{{JABATAN_ATASAN}}': str(data['j_atasan']),
            '{{NAMA_ATASAN}}': str(data['n_atasan']),
            '{{NIP_ATASAN}}': str(data['nip_atasan']),
            '{{PANGKAT_GOL_ATASAN}}': str(data['p_atasan']),
            '{{TTL}}': datetime.datetime.now().strftime('%d %B %Y')
        }

        for paragraph in doc.paragraphs:
            # Proses penggantian teks sambil menjaga format Bold
            for key, value in replacements.items():
                if key in paragraph.text:
                    for run in paragraph.runs:
                        if key in run.text:
                            run.text = run.text.replace(key, value)
            
            # Proses Tanda Tangan
            if '{{ttd}}' in paragraph.text:
                for run in paragraph.runs:
                    if '{{ttd}}' in run.text:
                        run.text = run.text.replace('{{ttd}}', "")
                
                if signature_img is not None:
                    img_rgba = Image.fromarray(signature_img.astype('uint8'), 'RGBA')
                    white_bg = Image.new("RGBA", img_rgba.size, (255, 255, 255, 255))
                    final_img = Image.alpha_composite(white_bg, img_rgba).convert("RGB")
                    
                    img_io = BytesIO()
                    final_img.save(img_io, format='PNG')
                    img_io.seek(0)
                    
                    new_run = paragraph.add_run()
                    new_run.add_picture(img_io, width=Mm(45))

        target_stream = BytesIO()
        doc.save(target_stream)
        target_stream.seek(0)
        return target_stream
    except Exception as e:
        st.error(f"Gagal: {e}")
        return None

# --- 4. TAMPILAN FORM ---
st.title("📝 Form SPT Admin OPD")

# I. PERIHAL
perihal_spt = st.selectbox("I. Pilih Perihal:", ["SPT Rekon TPP dan SIMONA"])

# II. UNIT KERJA
st.header("II. Unit Kerja")
list_opd = ["Sekretariat Daerah", "Inspektorat", "Dinas Pendidikan", "Dinas Kesehatan", "RSUD Ahmad Ripin", "Bagian Organisasi", "Bagian Umum", "Bagian PBJ"]
opsi_opd = st.selectbox("Pilih OPD:", [""] + sorted(list_opd) + ["Lainnya"])
unit_kerja_final = st.text_input("Input Manual OPD:") if opsi_opd == "Lainnya" else opsi_opd

with st.form("spt_form"):
    st.header("III. Data Admin")
    col1, col2 = st.columns(2)
    with col1:
        nama_admin = st.text_input("Nama Lengkap")
        nip_admin = st.text_input("NIP (18 Digit)", max_chars=18)
    with col2:
        pangkat_admin = st.text_input("Pangkat/Golongan")
        jabatan_admin = st.text_input("Jabatan")
    
    no_hp = st.text_input("No WhatsApp")
    email = st.text_input("Email")

    st.header("IV. Data Atasan")
    j_atasan = st.text_input("Jabatan Atasan")
    n_atasan = st.text_input("Nama Atasan")
    p_atasan = st.text_input("Pangkat Atasan")
    nip_atasan = st.text_input("NIP Atasan", max_chars=18)

    st.header("V. Tanda Tangan Atasan")
    canvas_result = st_canvas(
        stroke_width=3, stroke_color="#000000", background_color="#ffffff", 
        height=150, width=300, drawing_mode="freedraw", key="canvas_last"
    )

    submit = st.form_submit_button("Generate & Kirim Data", type="primary")

# --- 5. LOGIKA SUBMIT ---
if submit:
    # Validasi NIP (Hanya Angka & 18 Digit)
    if not nip_admin.isdigit() or len(nip_admin) != 18:
        st.error("❌ NIP Admin harus 18 digit angka!")
    elif not nama_admin or not unit_kerja_final:
        st.warning("⚠️ Nama dan Unit Kerja wajib diisi!")
    else:
        with st.spinner('Sedang memproses...'):
            data_spt = {
                'unit_kerja': unit_kerja_final, 'nama': nama_admin, 'nip': nip_admin,
                'pangkat': pangkat_admin, 'jabatan': jabatan_admin, 'no_hp': no_hp,
                'email': email, 'j_atasan': j_atasan, 'n_atasan': n_atasan,
                'nip_atasan': nip_atasan, 'p_atasan': p_atasan
            }
            
            # Panggil fungsi baru
            docx_file = create_docx_final(data_spt, canvas_result.image_data)
            
            if docx_file:
                # Kirim ke Sheets (Jika servis aktif)
                if sheets_service:
                    try:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        row = [[now, perihal_spt, unit_kerja_final, nama_admin, f"'{nip_admin}", email, n_atasan]]
                        sheets_service.spreadsheets().values().append(
                            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                            valueInputOption="USER_ENTERED", body={'values': row}
                        ).execute()
                    except: pass
                
                st.success("✅ Berhasil! Submit SPT")
                st.download_button("📥 Download SPT Sekarang (hanya experimental)", docx_file, f"SPT_{nama_admin}.docx")
