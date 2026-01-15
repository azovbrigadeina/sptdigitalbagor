import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from io import BytesIO
from PIL import Image

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered", page_icon="📝")

# --- 2. CSS "ANTI-ERROR" (STANDAR BERSIH) ---
st.markdown("""
    <style>
    /* A. PAKSA BACKGROUND HALAMAN JADI PUTIH BERSIH */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }
    
    /* B. WARNA TEKS UTAMA: HITAM */
    h1, h2, h3, h4, p, div, label, span {
        color: #000000 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    
    /* C. PERBAIKAN UTAMA: MENU DROPDOWN (YANG TADI HITAM) */
    /* Ini memaksa latar belakang daftar pilihan menjadi PUTIH */
    ul[data-baseweb="menu"] {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
    }
    /* Ini memaksa teks di dalam pilihan menjadi HITAM */
    li[data-baseweb="option"] {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    /* Ini memberi warna abu-abu muda saat mouse diarahkan ke pilihan (Hover) */
    li[data-baseweb="option"]:hover, li[data-baseweb="option"][aria-selected="true"] {
        background-color: #f0f0f0 !important;
        color: #000000 !important;
    }
    
    /* D. KOTAK INPUT (TEXT BOX) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #999999 !important; /* Garis tepi abu-abu tegas */
        border-radius: 4px !important;
    }
    
    /* E. TOMBOL KIRIM */
    .stButton button {
        background-color: #000000 !important; /* Tombol Hitam */
        color: #ffffff !important; /* Teks Putih */
        border-radius: 5px;
        font-weight: bold;
        width: 100%;
        border: none;
    }
    .stButton button:hover {
        background-color: #333333 !important; /* Sedikit terang saat hover */
    }

    /* F. FOOTER */
    .custom-footer {
        text-align: center;
        color: #666666 !important;
        font-size: 0.85rem;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #eeeeee;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. KONEKSI GOOGLE SHEETS ---
@st.cache_resource
def get_sheets_service():
    try:
        if "gcp_service_account" in st.secrets:
            creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
            return build('sheets', 'v4', credentials=creds)
        else:
            return None
    except Exception as e:
        st.error(f"Error Koneksi: {e}")
        return None

sheets_service = get_sheets_service()
SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

# --- 4. DATA LIST OPD ---
list_opd = [
    "Bagian Tata Pemerintahan", "Bagian Kesejahteraan Rakyat", "Bagian Hukum",
    "Bagian Kerjasama", "Bagian Perekonomian", "Bagian Pembangunan dan Sumber Daya Alam",
    "Bagian Pengadaan Barang dan Jasa", "Bagian Umum", "Bagian Organisasi",
    "Bagian Protokol dan Komunikasi Pimpinan", "Bagian Perencanaan dan Keuangan",
    "Sekretariat Dewan Perwakilan Rakyat Daerah", "Inspektorat Daerah",
    "Dinas Pendidikan dan Kebudayaan", "Dinas Pariwisata, Kepemudaan dan Olahraga",
    "Dinas Kesehatan", "Dinas Sosial, Pemberdayaan Perempuan dan Perlindungan Anak",
    "Dinas Pengendalian Penduduk dan Keluarga Berencana", "Dinas Kependudukan dan Pencatatan Sipil",
    "Dinas Pemberdayaan Masyarakat dan Desa", "Satuan Polisi Pamong Praja",
    "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu",
    "Dinas Koperasi, Usaha Kecil Menengah, Perindustrian dan Perdagangan",
    "Dinas Tenaga Kerja dan Transmigrasi", "Dinas Komunikasi dan Informatika",
    "Dinas Perumahan Dan Kawasan Permukiman", "Dinas Pekerjaan Umum dan Penataan Ruang",
    "Dinas Perhubungan", "Dinas Lingkungan Hidup", "Dinas Tanaman Pangan dan Hortikultura",
    "Dinas Ketahanan Pangan", "Dinas Perkebunan dan Peternakan", "Dinas Perikanan",
    "Dinas Perpustakaan dan Arsip Daerah", "Badan Perencanaan Pembangunan dan Riset Inovasi Daerah",
    "Badan Kepegawaian dan Pengembangan Sumber Daya Manusia", "Badan Pengelola Keuangan dan Aset Daerah",
    "Badan Pengelola Pajak dan Retribusi Daerah", "Dinas Pemadam Kebakaran dan Penyelematan",
    "Badan Penanggulangan Bencana Daerah", "Badan Kesatuan bangsa dan Politik",
    "Kecamatan Bahar Selatan", "Kecamatan Bahar Utara", "Kecamatan Jambi Luar Kota",
    "Kecamatan Taman Rajo", "Kecamatan Kumpeh", "Kecamatan Kumpeh Ulu",
    "Kecamatan Maro Sebo", "Kecamatan Mestong", "Kecamatan Sekernan",
    "Kecamatan Sungai Bahar", "Kecamatan Sungai Gelam", 
    "RSUD Ahmad Ripin", "RSUD Sungai Bahar", "RSUD Sungai Gelam"
]

# --- 5. TAMPILAN APLIKASI ---

st.title("FORM SURAT TUGAS")
st.caption("Pendataan Admin OPD - Pemerintah Kab. Muaro Jambi")
st.write("---")

# Dummy Selector (Label Hidden agar rapi)
st.caption("Jenis Layanan (Otomatis):")
st.selectbox(
    "Label Hidden", 
    ["SURAT PERINTAH TUGAS (SPT) - ADMIN OPD"], 
    disabled=True,
    label_visibility="collapsed"
)

st.write("") 

# --- BAGIAN I: IDENTITAS OPD ---
st.subheader("I. UNIT KERJA")

# Selectbox OPD
opsi_opd_terpilih = st.selectbox(
    "1. Pilih Unit Kerja / OPD", 
    [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"],
)

# Input Manual
opd_manual = ""
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_manual = st.text_input("   ➥ Tuliskan Nama OPD Anda:")

# Final Variable
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_final = opd_manual
else:
    opd_final = opsi_opd_terpilih

# --- FORM UTAMA ---
with st.form("spt_form", clear_on_submit=False):
    
    st.write("---")
    st.subheader("II. DATA ADMIN (PENERIMA TUGAS)")
    
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("2. Nama Lengkap (Beserta Gelar)")
        pangkat = st.text_input("4. Pangkat / Golongan")
        no_hp = st.text_input("6. No. Handphone (WA)")
    with col2:
        nip = st.text_input("3. NIP (18 Digit Angka)", max_chars=18)
        jabatan = st.text_input("5. Jabatan")
        email = st.text_input("7. Alamat E-mail")

    st.write("---")
    st.subheader("III. DATA ATASAN LANGSUNG")
    
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan = st.text_input("1. Nama Atasan (Beserta Gelar)")
        pangkat_atasan = st.text_input("3. Pangkat / Golongan Atasan")
    with col4:
        nip_atasan = st.text_input("2. NIP Atasan (18 Digit Angka)", max_chars=18)
        jabatan_atasan = st.text_input("4. Jabatan Atasan")

    st.write("---")
    st.subheader("IV. TANDA TANGAN")
    st.caption("Silakan tanda tangan pada kotak di bawah ini:")
    
    # Canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff", # Latar Canvas Putih
        height=180,
        width=300, # Lebar pas untuk HP
        drawing_mode="freedraw",
        key="canvas_admin",
    )

    st.write("")
    submit_button = st.form_submit_button(label="KIRIM DATA", type="primary")

# --- 6. PROSES VALIDASI & KIRIM ---
if submit_button:
    # A. Validasi
    if not opd_final:
        st.error("❌ Nama OPD belum dipilih.")
        st.stop()

    if not all([nama, nip, pangkat, jabatan, no_hp, email, nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan]):
        st.error("❌ Mohon lengkapi semua kolom isian.")
        st.stop()

    if not (nip.isdigit() and len(nip) == 18):
        st.error("❌ NIP Admin harus 18 digit angka.")
        st.stop()
    if not (nip_atasan.isdigit() and len(nip_atasan) == 18):
        st.error("❌ NIP Atasan harus 18 digit angka.")
        st.stop()

    if canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("❌ Tanda tangan belum diisi.")
        st.stop()

    # B. Kirim
    try:
        with st.spinner('Sedang mengirim data...'):
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            img.thumbnail((300, 150))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            data_ttd = f"data:image/png;base64,{img_base64}"

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            row_data = [[
                now, opd_final, "'" + nip, nama, pangkat, jabatan, no_hp, email, 
                "'" + nip_atasan, nama_atasan, pangkat_atasan, jabatan_atasan, data_ttd
            ]]
            
            if sheets_service:
                sheets_service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID, 
                    range="Sheet1!A1",
                    valueInputOption="USER_ENTERED", 
                    body={'values': row_data}
                ).execute()
            
                st.success(f"✅ SUKSES! Terima kasih Sdr/i {nama}.")
                st.balloons()
            else:
                st.error("Gagal terhubung ke Database Google Sheets.")

    except Exception as e:
        st.error(f"Terjadi kesalahan sistem: {e}")

# --- 7. FOOTER ---
st.markdown("""
<div class="custom-footer">
    Made in Love ❤️ oleh Tim Anjab Bagor Muaro Jambi
</div>
""", unsafe_allow_html=True)
