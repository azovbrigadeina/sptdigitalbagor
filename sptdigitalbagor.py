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
        st.error(f"File '{template_name}' tidak ditemukan di GitHub!")
        return None

    try:
        doc = DocxTemplate(template_name)
        
        img_obj = ""
        if signature_img:
            temp_path = "temp_sig.png"
            signature_img.save(temp_path)
            img_obj = InlineImage(doc, temp_path, width=40 * mm)

        # MAPPING SESUAI CLUE TAG ANDA
        context = {
            'Unit_Kerja': data['unit_kerja'],        # {{ Unit_Kerja }}
            'nama_admin': data['nama'],              # {{ nama_admin }}
            'pangkat_admin': data['pangkat'],        # {{ pangkat_admin }}
            'NIP_admin': data['nip'],                # {{ NIP_admin }}
            'Jabatan_admin': data['jabatan'],        # {{ Jabatan_admin }}
            'no_hpadmin': data['no_hp'],             # {{ no_hpadmin }}
            'email_admin': data['email'],            # {{ email_admin }}
            'JABATAN_ATASAN': data['j_atasan'],      # {{ JABATAN_ATASAN }}
            'NAMA_ATASAN': data['n_atasan'],         # {{ NAMA_ATASAN }}
            'NIP_ATASAN': data['nip_atasan'],       # {{ NIP_ATASAN }}
            'PANGKAT_GOL_ATASAN': data['p_atasan'], # {{ PANGKAT_GOL_ATASAN }}
            'Tanggal_Bulan_Tahun': datetime.datetime.now().strftime('%d %B %Y'),
            'ttd': img_obj 
        }

        doc.render(context)
        
        target_stream = BytesIO()
        doc.save(target_stream)
        target_stream.seek(0)
        
        if os.path.exists("temp_sig.png"):
            os.remove(temp_sig.png)
            
        return target_stream
    except Exception as e:
        st.error(f"Gagal mengisi template: {e}")
        return None

# --- 4. TAMPILAN FORM (KEMBALI KE FORMAT AWAL) ---
st.title("📝 Form SPT Admin OPD")
st.write("---")

st.header("I. Unit Kerja")
list_opd = ["Bagian Organisasi", "Bagian Umum", "Dinas Pendidikan", "RSUD Ahmad Ripin"]
opsi_opd = st.selectbox("Pilih Unit Kerja:", [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"])
unit_kerja_input = st.text_input("Tulis Nama OPD:") if opsi_opd == "Lainnya (Isi Manual)" else opsi_opd

with st.form("spt_form"):
    st.header("II. Data Admin")
    col1, col2 = st.columns(2)
    with col1:
        nama_admin = st.text_input("Nama")
        nip_admin = st.text_input("NIP")
    with col2:
        pangkat_admin = st.text_input("Pangkat/Gol")
        jabatan_admin = st.text_input("Jabatan")
    
    no_hp = st.text_input("Nomor Telepon")
    email = st.text_input("Alamat Email")

    st.header("III. Data Atasan")
    jabatan_atasan = st.text_input("Jabatan Atasan (Contoh: KEPALA DINAS)")
    nama_atasan = st.text_input("Nama Atasan")
    nip_atasan = st.text_input("NIP Atasan")
    pangkat_atasan = st.text_input("Pangkat Atasan")

    st.header("IV. Tanda Tangan")
    canvas_result = st_canvas(height=150, width=300, drawing_mode="freedraw", key="canvas_ttd")

    submit = st.form_submit_button("Generate SPT", type="primary")

# --- 5. EKSEKUSI ---
if submit:
    if not unit_kerja_input or not nama_admin:
        st.warning("Mohon lengkapi data Unit Kerja dan Nama Admin.")
    else:
        with st.spinner('Memproses...'):
            img_ttd = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # Kumpulkan data untuk mapping
            data_spt = {
                'unit_kerja': unit_kerja_input,
                'nama': nama_admin,
                'nip': nip_admin,
                'pangkat': pangkat_admin,
                'jabatan': jabatan_admin,
                'no_hp': no_hp,
                'email': email,
                'j_atasan': jabatan_atasan,
                'n_atasan': nama_atasan,
                'nip_atasan': nip_atasan,
                'p_atasan': pangkat_atasan
            }
            
            docx_file = create_docx_from_template(data_spt, img_ttd)
            
            if docx_file:
                # Simpan ke Sheets
                if sheets_service:
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row = [[now, unit_kerja_input, nama_admin, f"'{nip_admin}", email]]
                    sheets_service.spreadsheets().values().append(
                        spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                        valueInputOption="USER_ENTERED", body={'values': row}
                    ).execute()
                
                st.success("SPT Berhasil Dibuat!")
                st.download_button(
                    label="📥 Download SPT (Word)",
                    data=docx_file,
                    file_name=f"SPT_{nama_admin.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
