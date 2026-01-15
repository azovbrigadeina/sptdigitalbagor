import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from io import BytesIO
from PIL import Image

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered", page_icon="📝")

# --- CUSTOM CSS (PERBAIKAN KONTRAS WARNA) ---
st.markdown("""
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #1e293b;
    }

    /* 1. Main Background */
    [data-testid="stAppViewContainer"] {
        background-color: #f1f5f9;
        background-image: radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.1) 0, transparent 50%), 
                          radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.1) 0, transparent 50%);
        background-attachment: fixed;
    }
    
    /* 2. Main Content Container (Glass-like Card) */
    .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 3rem 3rem !important;
        border-radius: 24px;
        box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.05), 
                    0 0 0 1px rgba(0, 0, 0, 0.02);
        margin-top: 2rem;
        max-width: 850px;
    }
    
    /* 3. Typography & Headings */
    h1 {
        background: linear-gradient(120deg, #0f172a, #334155);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.025em;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 2.5rem;
    }
    
    h2, h3 {
        color: #334155;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    p, label, .stMarkdown {
        color: #475569;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    /* 4. Input Fields Styling */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        color: #1e293b;
        padding: 0.6rem 0.8rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #6366f1;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
        transform: translateY(-1px);
    }
    
    /* Input Labels */
    .stTextInput label, .stSelectbox label {
        color: #334155 !important;
        font-weight: 600;
        font-size: 0.875rem;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }

    /* 5. Modern Buttons */
    .stButton button {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
        color: white;
        border: none;
        padding: 0.75rem 0;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.01em;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2), 
                    0 2px 4px -1px rgba(79, 70, 229, 0.1);
        transition: all 0.2s;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
        background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%);
    }
    
    .stButton button:active {
        transform: translateY(0);
    }
    
    /* 6. Footer (Elegant) */
    .custom-footer {
        text-align: center;
        margin-top: 5rem;
        padding-top: 2rem;
        border-top: 1px dashed #e2e8f0;
        color: #94a3b8;
        font-size: 0.875rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }
    
    /* Remove default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;} /* Hides the top colored bar for cleaner look */
    </style>
    """, unsafe_allow_html=True)

# --- KREDENSIAL GOOGLE SHEETS ---
@st.cache_resource
def get_sheets_service():
    try:
        # Check if secrets exist before trying to load
        if "gcp_service_account" not in st.secrets:
            st.error("Kredensial GCP tidak ditemukan di st.secrets")
            return None
            
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        st.error(f"Gagal memuat kredensial: {e}")
        return None

sheets_service = get_sheets_service()
SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

# --- DAFTAR OPD ---
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

# --- JUDUL & DUMMY SELECTOR ---
st.title("📝 Form Administrasi Surat")

# Dummy Dropdown
st.selectbox(
    "Jenis Layanan / Surat (Default System)", 
    ["Surat Perintah Tugas (SPT) - Penunjukan Admin"], 
    disabled=True,
    help="Jenis surat terkunci oleh sistem untuk saat ini."
)

st.write("---")

# --- BAGIAN 1: PEMILIHAN OPD ---
st.subheader("I. Identitas Unit Kerja")

opsi_opd_terpilih = st.selectbox(
    "1. Pilih Unit Kerja / OPD", 
    [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"]
)

opd_manual = ""
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_manual = st.text_input("   ➥ Tuliskan Nama Unit Kerja / OPD Anda:", placeholder="Contoh: Puskesmas Jambi Kecil")

if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_final = opd_manual
else:
    opd_final = opsi_opd_terpilih

# --- BAGIAN 2: FORMULIR DATA DIRI ---
with st.form("spt_form", clear_on_submit=False):
    
    st.write("---")
    st.subheader("II. Data Admin (Penerima Tugas)")
    
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("2. Nama Lengkap (Beserta Gelar)")
        pangkat = st.text_input("4. Pangkat / Golongan")
        no_hp = st.text_input("6. No. Handphone (WA)")
    with col2:
        nip = st.text_input("3. NIP Admin (18 Digit Angka)", max_chars=18)
        jabatan = st.text_input("5. Jabatan")
        email = st.text_input("7. Alamat E-mail")

    st.write("---")
    st.subheader("III. Data Atasan Langsung")
    
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan = st.text_input("1. Nama Atasan (Beserta Gelar)")
        pangkat_atasan = st.text_input("3. Pangkat / Golongan Atasan")
    with col4:
        nip_atasan = st.text_input("2. NIP Atasan (18 Digit Angka)", max_chars=18)
        jabatan_atasan = st.text_input("4. Jabatan Atasan")

    st.write("---")
    st.subheader("IV. Tanda Tangan")
    st.caption("Silakan tanda tangan pada kotak di bawah ini:")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#f8f9fa",
        height=180,
        width=400,
        drawing_mode="freedraw",
        key="canvas_admin",
    )

    st.write("")
    submit_button = st.form_submit_button(label="Kirim Data", type="primary")

# --- PROSES VALIDASI & PENGIRIMAN ---
if submit_button:
    if not opd_final:
        st.error("❌ Nama OPD belum dipilih atau diisi!")
        st.stop()

    input_wajib = [nama, nip, pangkat, jabatan, no_hp, email, nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan]
    if not all(input_wajib):
        st.error("❌ Mohon lengkapi semua kolom isian data!")
        st.stop()

    if not (nip.isdigit() and len(nip) == 18):
        st.error("❌ NIP Admin tidak valid! Harus 18 digit angka.")
        st.stop()
        
    if not (nip_atasan.isdigit() and len(nip_atasan) == 18):
        st.error("❌ NIP Atasan tidak valid! Harus 18 digit angka.")
        st.stop()

    if canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("❌ Tanda tangan belum diisi!")
        st.stop()

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
            
                st.success(f"✅ Data Terkirim! Terima kasih {nama}.")
                st.balloons()
            else:
                st.error("Gagal koneksi ke server. Service Sheets tidak tersedia.")

    except Exception as e:
        st.error(f"Error: {e}")

# --- FOOTER BARU (MADE IN LOVE) ---
st.markdown("---")
st.markdown("""
<div class="custom-footer">
    Made in Love ❤️ oleh Tim Anjab Bagor Muaro Jambi
</div>
""", unsafe_allow_html=True)
