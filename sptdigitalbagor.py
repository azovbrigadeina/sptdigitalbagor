import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from io import BytesIO
from PIL import Image

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SPT Admin OPD", layout="centered", page_icon="📝")

# --- 2. GAYA RETRO/STANDAR (CSS SEDERHANA) ---
# Kita hanya mengubah Font menjadi Monospace (seperti mesin ketik)
# dan memberi garis batas tegas (border) agar form terlihat jelas.
st.markdown("""
    <style>
    /* Background Halaman: Sedikit krem seperti kertas lama */
    .stApp {
        background-color: #fdfbf7;
    }
    
    /* Container Utama: Putih dengan Border Hitam Tegas */
    .block-container {
        background-color: #ffffff;
        border: 2px solid #000000; /* Garis hitam tebal retro */
        padding: 3rem !important;
        box-shadow: 10px 10px 0px rgba(0,0,0,0.1); /* Bayangan kaku ala retro */
        max-width: 750px;
    }

    /* Font ala Mesin Ketik */
    h1, h2, h3, p, div, label, input {
        font-family: 'Courier New', Courier, monospace !important;
        color: #000000 !important; /* Paksa hitam agar terbaca */
    }
    
    /* Input Fields: Kotak Putih dengan Garis Hitam */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid #000000 !important;
        border-radius: 0px !important; /* Sudut lancip retro */
        color: #000000 !important;
    }
    
    /* Tombol: Hitam Putih Klasik */
    .stButton button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border-radius: 0px !important;
        border: 1px solid #000000 !important;
        font-weight: bold;
        text-transform: uppercase;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #333333 !important;
    }

    /* Footer */
    .custom-footer {
        text-align: center;
        font-size: 0.8rem;
        margin-top: 30px;
        padding-top: 10px;
        border-top: 2px dashed #000000; /* Garis putus-putus */
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
st.write("---")

# Dummy Selector
st.caption("JENIS LAYANAN:")
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
    "PILIH UNIT KERJA / OPD:", 
    [""] + sorted(list_opd) + ["LAINNYA (ISI MANUAL)"],
)

# Input Manual
opd_manual = ""
if opsi_opd_terpilih == "LAINNYA (ISI MANUAL)":
    opd_manual = st.text_input("KETIK NAMA OPD:")

# Final Variable
if opsi_opd_terpilih == "LAINNYA (ISI MANUAL)":
    opd_final = opd_manual
else:
    opd_final = opsi_opd_terpilih

# --- FORM UTAMA ---
with st.form("spt_form", clear_on_submit=False):
    
    st.write("---")
    st.subheader("II. DATA ADMIN (YANG DITUGASKAN)")
    
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("NAMA LENGKAP & GELAR")
        pangkat = st.text_input("PANGKAT / GOLONGAN")
        no_hp = st.text_input("NO. HP (WHATSAPP)")
    with col2:
        nip = st.text_input("NIP (18 DIGIT ANGKA)", max_chars=18)
        jabatan = st.text_input("JABATAN")
        email = st.text_input("ALAMAT E-MAIL")

    st.write("---")
    st.subheader("III. DATA ATASAN LANGSUNG")
    
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan = st.text_input("NAMA ATASAN")
        pangkat_atasan = st.text_input("PANGKAT ATASAN")
    with col4:
        nip_atasan = st.text_input("NIP ATASAN (18 DIGIT)", max_chars=18)
        jabatan_atasan = st.text_input("JABATAN ATASAN")

    st.write("---")
    st.subheader("IV. TANDA TANGAN")
    st.caption("Goreskan tanda tangan pada kotak di bawah ini:")
    
    # Canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff",
        height=180,
        width=300,
        drawing_mode="freedraw",
        key="canvas_admin",
    )

    st.write("")
    submit_button = st.form_submit_button(label="KIRIM DATA", type="primary")

# --- 6. PROSES VALIDASI & KIRIM ---
if submit_button:
    # A. Validasi
    if not opd_final:
        st.error("ERROR: NAMA OPD BELUM DIPILIH.")
        st.stop()

    if not all([nama, nip, pangkat, jabatan, no_hp, email, nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan]):
        st.error("ERROR: SEMUA KOLOM WAJIB DIISI.")
        st.stop()

    if not (nip.isdigit() and len(nip) == 18):
        st.error("ERROR: NIP ADMIN HARUS 18 DIGIT ANGKA.")
        st.stop()
    if not (nip_atasan.isdigit() and len(nip_atasan) == 18):
        st.error("ERROR: NIP ATASAN HARUS 18 DIGIT ANGKA.")
        st.stop()

    if canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("ERROR: TANDA TANGAN KOSONG.")
        st.stop()

    # B. Kirim
    try:
        with st.spinner('SEDANG MENGIRIM DATA...'):
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
            
                st.success(f"SUKSES! DATA TERKIRIM. TERIMA KASIH {nama}.")
                st.balloons()
            else:
                st.error("GAGAL KONEKSI KE SERVER.")

    except Exception as e:
        st.error(f"SYSTEM ERROR: {e}")

# --- 7. FOOTER ---
st.markdown("""
<div class="custom-footer">
    Made in Love ❤️ oleh Tim Anjab Bagor Muaro Jambi
</div>
""", unsafe_allow_html=True)
