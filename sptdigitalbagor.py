import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from io import BytesIO
from PIL import Image

# --- 1. KONFIGURASI HALAMAN (STANDAR) ---
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered", page_icon="📝")

# --- 2. KONEKSI GOOGLE SHEETS ---
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

# --- 3. DATA LIST OPD ---
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

# --- 4. TAMPILAN APLIKASI (STANDAR) ---

st.title("Form Surat Perintah Tugas")
st.markdown("Pendataan Admin OPD - Pemerintah Kabupaten Muaro Jambi")
st.write("---")

# Dummy Selector (Tampilan Saja)
st.selectbox(
    "Jenis Layanan", 
    ["Surat Perintah Tugas (SPT) - Penunjukan Admin"], 
    disabled=True
)

st.write("") 

# --- BAGIAN I: IDENTITAS OPD ---
st.header("I. Unit Kerja")

# Selectbox OPD (Di luar form agar interaktif)
opsi_opd_terpilih = st.selectbox(
    "Pilih Unit Kerja / OPD", 
    [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"],
)

# Logic Manual Input
opd_manual = ""
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_manual = st.text_input("Tuliskan Nama Unit Kerja / OPD Anda:")

# Variable Final OPD
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_final = opd_manual
else:
    opd_final = opsi_opd_terpilih

# --- BAGIAN FORM UTAMA ---
with st.form("spt_form", clear_on_submit=False):
    
    st.write("")
    st.header("II. Data Admin (Penerima Tugas)")
    
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("Nama Lengkap (Beserta Gelar)")
        pangkat = st.text_input("Pangkat / Golongan")
        no_hp = st.text_input("No. Handphone (WA)")
    with col2:
        nip = st.text_input("NIP Admin (18 Digit)", max_chars=18)
        jabatan = st.text_input("Jabatan")
        email = st.text_input("Alamat E-mail")

    st.write("---")
    st.header("III. Data Atasan Langsung")
    
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan = st.text_input("Nama Atasan (Beserta Gelar)")
        pangkat_atasan = st.text_input("Pangkat / Golongan Atasan")
    with col4:
        nip_atasan = st.text_input("NIP Atasan (18 Digit)", max_chars=18)
        jabatan_atasan = st.text_input("Jabatan Atasan")

    st.write("---")
    st.header("IV. Tanda Tangan")
    st.caption("Silakan tanda tangan pada area di bawah ini:")
    
    # Canvas (Background putih agar kontras dengan tinta hitam)
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff", # Tetap putih agar tanda tangan terlihat
        height=180,
        width=300, 
        drawing_mode="freedraw",
        key="canvas_admin",
    )

    st.write("")
    submit_button = st.form_submit_button(label="Kirim Data SPT", type="primary")

# --- 5. PROSES VALIDASI & KIRIM ---
if submit_button:
    # A. Validasi
    if not opd_final:
        st.error("Nama OPD belum dipilih.")
        st.stop()

    if not all([nama, nip, pangkat, jabatan, no_hp, email, nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan]):
        st.error("Mohon lengkapi semua kolom isian.")
        st.stop()

    if not (nip.isdigit() and len(nip) == 18):
        st.error("NIP Admin harus 18 digit angka.")
        st.stop()
    if not (nip_atasan.isdigit() and len(nip_atasan) == 18):
        st.error("NIP Atasan harus 18 digit angka.")
        st.stop()

    if canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("Tanda tangan belum diisi.")
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
            
                st.success(f"Berhasil! Data SPT {nama} telah tersimpan.")
                st.balloons()
            else:
                st.error("Gagal terhubung ke Database.")

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

# --- Footer Sederhana ---
st.markdown("---")
st.caption("© 2026 Tim Anjab Bagor Muaro Jambi")
