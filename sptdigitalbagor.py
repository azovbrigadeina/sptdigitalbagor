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

# --- 2. CSS "ANTI-PECAH" (Desktop & Mobile Friendly) ---
st.markdown("""
    <style>
    /* A. BACKGROUND UTAMA (Nuansa Ukraina) */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to bottom, #0057B7 0%, #0057B7 50%, #FFDD00 50%, #FFDD00 100%);
        background-attachment: fixed;
    }

    /* B. KONTAINER PUTIH (Tempat Isi Form) */
    .block-container {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 2rem 2rem !important; /* Padding standar */
        margin-top: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        max-width: 700px;
    }

    /* C. RESPONSIVE MOBILE: Agar di HP tidak terlalu lebar paddingnya */
    @media (max-width: 576px) {
        .block-container {
            padding: 1rem 1rem !important;
            margin-top: 1rem;
        }
    }

    /* D. PAKSA SEMUA TEKS JADI HITAM (Mengatasi Isu Dark Mode) */
    h1, h2, h3, h4, p, span, div, label {
        color: #212529 !important;
    }
    
    /* E. PERBAIKAN KOLOM INPUT (Agar teks yang diketik kelihatan) */
    .stTextInput input, .stSelectbox div, .stNumberInput input {
        color: #000000 !important;
        background-color: #f8f9fa !important;
        border-color: #ced4da !important;
    }
    
    /* F. LABEL DI ATAS INPUT (Judul Kolom) */
    .stTextInput label, .stSelectbox label {
        color: #333333 !important;
        font-weight: 600 !important;
    }

    /* G. TOMBOL UTAMA */
    .stButton button {
        background-color: #0057B7 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        border: none;
    }
    .stButton button:hover {
        background-color: #004494 !important;
    }

    /* H. FOOTER */
    .custom-footer {
        text-align: center;
        color: #555555 !important;
        font-weight: bold;
        font-size: 0.85rem;
        margin-top: 30px;
        padding-top: 10px;
        border-top: 1px dashed #ccc;
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

# --- 5. LOGIKA APLIKASI ---

st.title("📝 Form Administrasi Surat")

# Dummy Selector (Hanya Tampilan)
st.selectbox(
    "Jenis Layanan / Surat", 
    ["Surat Perintah Tugas (SPT) - Penunjukan Admin"], 
    disabled=True
)

st.write("---")

# Bagian I: Pilih OPD (Di Luar Form agar Interaktif)
st.subheader("I. Identitas Unit Kerja")

opsi_opd_terpilih = st.selectbox(
    "1. Pilih Unit Kerja / OPD", 
    [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"]
)

opd_manual = ""
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_manual = st.text_input("   ➥ Ketik Nama Unit Kerja / OPD Anda:")

# Tentukan Nilai Akhir OPD
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_final = opd_manual
else:
    opd_final = opsi_opd_terpilih

# Bagian Form Utama
with st.form("spt_form", clear_on_submit=False):
    
    st.write("---")
    st.subheader("II. Data Admin (Penerima Tugas)")
    
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("2. Nama Lengkap (Gelar)")
        pangkat = st.text_input("4. Pangkat / Golongan")
        no_hp = st.text_input("6. No. Handphone (WA)")
    with col2:
        nip = st.text_input("3. NIP Admin (18 Digit)", max_chars=18)
        jabatan = st.text_input("5. Jabatan")
        email = st.text_input("7. Alamat E-mail")

    st.write("---")
    st.subheader("III. Data Atasan Langsung")
    
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan = st.text_input("1. Nama Atasan (Gelar)")
        pangkat_atasan = st.text_input("3. Pangkat / Golongan Atasan")
    with col4:
        nip_atasan = st.text_input("2. NIP Atasan (18 Digit)", max_chars=18)
        jabatan_atasan = st.text_input("4. Jabatan Atasan")

    st.write("---")
    st.subheader("IV. Tanda Tangan")
    st.caption("Silakan tanda tangan pada area kotak di bawah ini:")
    
    # Canvas Tanda Tangan
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff", # Latar putih solid untuk canvas
        height=180,
        width=300, # Ukuran aman untuk HP
        drawing_mode="freedraw",
        key="canvas_admin",
    )

    st.write("")
    submit_button = st.form_submit_button(label="Kirim Data", type="primary")

# --- 6. PROSES VALIDASI & KIRIM ---
if submit_button:
    # A. Validasi OPD
    if not opd_final:
        st.error("❌ Nama OPD belum dipilih/diisi.")
        st.stop()

    # B. Validasi Field Kosong
    if not all([nama, nip, pangkat, jabatan, no_hp, email, nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan]):
        st.error("❌ Mohon lengkapi semua kolom isian.")
        st.stop()

    # C. Validasi Angka NIP
    if not (nip.isdigit() and len(nip) == 18):
        st.error("❌ NIP Admin harus 18 digit angka.")
        st.stop()
    if not (nip_atasan.isdigit() and len(nip_atasan) == 18):
        st.error("❌ NIP Atasan harus 18 digit angka.")
        st.stop()

    # D. Validasi Tanda Tangan
    if canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("❌ Tanda tangan wajib diisi.")
        st.stop()

    # E. Proses Kirim
    try:
        with st.spinner('Sedang mengirim data...'):
            # Convert Gambar
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            img.thumbnail((300, 150))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            data_ttd = f"data:image/png;base64,{img_base64}"

            # Timestamp
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Susun Data (' di depan NIP agar jadi text di Excel)
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
            
                st.success(f"✅ Data Berhasil Terkirim! Terima kasih {nama}.")
                st.balloons()
            else:
                st.error("Gagal terhubung ke Database (Cek Secrets).")

    except Exception as e:
        st.error(f"Terjadi kesalahan sistem: {e}")

# --- 7. FOOTER ---
st.markdown("""
<div class="custom-footer">
    Made in Love ❤️ oleh Tim Anjab Bagor Muaro Jambi
</div>
""", unsafe_allow_html=True)
