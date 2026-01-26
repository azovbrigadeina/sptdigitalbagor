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
st.set_page_config(page_title="Digital SPT SIMONA", layout="wide", page_icon="📝")

# Custom CSS untuk mempercantik tampilan
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
        border: 1px solid #e1e4e8;
    }
    .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: 0px 4px 6px rgba(0,0,0,0.1); background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KONEKSI GOOGLE SHEETS ---
@st.cache_resource
def get_sheets_service():
    try:
        if "gcp_service_account" in st.secrets:
            cred_info = st.secrets["gcp_service_account"]
            creds = service_account.Credentials.from_service_account_info(cred_info)
            return build('sheets', 'v4', credentials=creds)
        return None
    except Exception:
        return None

sheets_service = get_sheets_service()
SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

# --- 3. FUNGSI GENERATE ---
def create_docx_final(data, signature_img):
    template_name = "template spt simona.docx" 
    if not os.path.exists(template_name):
        st.error("File template tidak ditemukan!")
        return None

    try:
        doc = Document(template_name)
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
            for key, value in replacements.items():
                if key in paragraph.text:
                    for run in paragraph.runs:
                        if key in run.text:
                            run.text = run.text.replace(key, value)
            
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

# --- 4. TAMPILAN UTAMA ---
st.markdown("<h1 style='text-align: center; color: #007bff;'>📝 Sistem Digital SPT SIMONA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Mudah, Cepat, dan Otomatis</p>", unsafe_allow_html=True)

with st.expander("ℹ️ Petunjuk Penggunaan"):
    st.write("""
    1. Pilih **Unit Kerja** terlebih dahulu.
    2. Isi data admin dan data atasan pada tab yang tersedia.
    3. Bubuhkan tanda tangan di bagian paling bawah.
    4. Klik **Generate** dan tunggu file siap di-download.
    """)

# --- 5. FORM DINAMIS DENGAN TABS ---
tab1, tab2, tab3 = st.tabs(["🏢 Satuan Kerja", "👤 Identitas Admin", "✍️ Otorisasi Atasan"])

with st.form("main_form"):
    with tab1:
        st.subheader("Data Instansi")
        perihal = st.selectbox("Perihal Surat:", ["SPT Rekon TPP dan SIMONA"])
        list_opd = ["Sekretariat Daerah", "Inspektorat", "Dinas Pendidikan", "Dinas Kesehatan", "RSUD Ahmad Ripin", "Bagian Organisasi", "Bagian Umum", "Bagian PBJ"]
        opsi_opd = st.selectbox("Pilih OPD/Unit Kerja:", [""] + sorted(list_opd) + ["Lainnya"])
        unit_kerja_final = st.text_input("Ketik Nama OPD (Jika pilih Lainnya):") if opsi_opd == "Lainnya" else opsi_opd

    with tab2:
        st.subheader("Informasi Admin OPD")
        col1, col2 = st.columns(2)
        with col1:
            nama_admin = st.text_input("Nama Lengkap Admin")
            nip_admin = st.text_input("NIP / NI PPPK", max_chars=18, help="Masukkan 18 digit angka")
        with col2:
            pangkat_admin = st.text_input("Pangkat / Golongan")
            jabatan_admin = st.text_input("Jabatan Admin")
        
        c3, c4 = st.columns(2)
        with c3: no_hp = st.text_input("No. WhatsApp (Aktif)")
        with c4: email = st.text_input("Alamat Email")

    with tab3:
        st.subheader("Informasi Penandatangan")
        j_atasan = st.text_input("Jabatan Atasan (Contoh: Kepala Bagian Organisasi)")
        col5, col6 = st.columns(2)
        with col5:
            n_atasan = st.text_input("Nama Lengkap Atasan")
            p_atasan = st.text_input("Pangkat Atasan")
        with col6:
            nip_atasan = st.text_input("NIP Atasan", max_chars=18)
        
        st.write("---")
        st.markdown("##### Tanda Tangan Atasan")
        st.caption("Gunakan mouse atau layar sentuh untuk tanda tangan di kotak bawah:")
        canvas_result = st_canvas(
            stroke_width=3, stroke_color="#000000", background_color="#ffffff",
            height=150, width=400, drawing_mode="freedraw", key="canvas_last",
            display_toolbar=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.form_submit_button("🚀 GENERATE & SUBMIT SPT", use_container_width=True)

# --- 6. LOGIKA EKSEKUSI ---
if submit:
    if not nip_admin.isdigit() or len(nip_admin) != 18:
        st.error("❌ Validasi Gagal: NIP Admin harus 18 digit angka!")
    elif not nama_admin or not unit_kerja_final or not n_atasan:
        st.warning("⚠️ Mohon lengkapi Nama Admin, Unit Kerja, dan Nama Atasan.")
    else:
        with st.status("🛠️ Memproses Dokumen...", expanded=True) as status:
            data_spt = {
                'unit_kerja': unit_kerja_final, 'nama': nama_admin, 'nip': nip_admin,
                'pangkat': pangkat_admin, 'jabatan': jabatan_admin, 'no_hp': no_hp,
                'email': email, 'j_atasan': j_atasan, 'n_atasan': n_atasan,
                'nip_atasan': nip_atasan, 'p_atasan': p_atasan
            }
            
            docx_file = create_docx_final(data_spt, canvas_result.image_data)
            
            if docx_file:
                # Kirim data ke Google Sheets
                if sheets_service:
                    try:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        row = [[now, perihal, unit_kerja_final, nama_admin, f"'{nip_admin}", email, n_atasan]]
                        sheets_service.spreadsheets().values().append(
                            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                            valueInputOption="USER_ENTERED", body={'values': row}
                        ).execute()
                    except Exception: pass
                
                status.update(label="✅ SPT Berhasil Dibuat!", state="complete", expanded=False)
                
                st.balloons()
                st.success("SPT Anda siap diunduh.")
                st.download_button(
                    label="📥 DOWNLOAD FILE SPT (WORD)", 
                    data=docx_file, 
                    file_name=f"SPT_{nama_admin.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
