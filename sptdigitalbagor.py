import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from io import BytesIO
from PIL import Image

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Form SPT Admin OPD - Muaro Jambi", layout="centered", page_icon="📝")

# --- KREDENSIAL GOOGLE SHEETS ---
@st.cache_resource
def get_sheets_service():
    try:
        # Mengambil credentials dari secrets Streamlit
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        st.error(f"Gagal memuat kredensial: {e}")
        return None

sheets_service = get_sheets_service()
SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798" # Pastikan ID ini benar

# --- DAFTAR OPD (Puskesmas Dihapus) ---
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

# --- JUDUL & HEADER ---
st.title("📝 Form Surat Perintah Tugas")
st.markdown("""
**Pendataan Admin OPD - SIMONA E-ANJAB-ABK** *Dasar: Surat Sekda Kab. Muaro Jambi No. 000.8/040/Org Tanggal 16 Januari 2026*
""")
st.info("ℹ️ Formulir ini digunakan sebagai bukti dukung (evidence) persetujuan TPP.")
st.write("---")

# --- BAGIAN 1: PEMILIHAN OPD (Di luar Form agar Interaktif) ---
st.subheader("I. Identitas OPD")
st.caption("Pilih nama OPD Anda. Jika tidak ada di daftar, pilih 'Lainnya' dan ketik manual.")

# Dropdown Pilihan
opsi_opd_terpilih = st.selectbox(
    "1. Pilih Unit Kerja / OPD", 
    [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"]
)

# Logic Input Manual
opd_manual = ""
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_manual = st.text_input("   ➥ Tuliskan Nama Unit Kerja / OPD Anda:", placeholder="Contoh: Puskesmas Jambi Kecil")

# Menentukan variabel final OPD untuk disimpan nanti
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_final = opd_manual
else:
    opd_final = opsi_opd_terpilih

# --- BAGIAN 2: FORMULIR DATA DIRI (Di dalam st.form) ---
# clear_on_submit=False agar isian OPD di atas tidak hilang saat submit gagal/sukses
with st.form("spt_form", clear_on_submit=False):
    
    st.write("---")
    st.subheader("II. Data Admin (Yang Diberi Tugas)")
    
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
    st.subheader("IV. Tanda Tangan Admin")
    st.caption("Silakan tanda tangan pada kotak di bawah ini menggunakan jari atau mouse:")
    
    # Canvas Tanda Tangan
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#f0f2f6", # Warna background kotak tanda tangan
        height=180,
        width=400,
        drawing_mode="freedraw",
        key="canvas_admin",
    )

    st.write("")
    submit_button = st.form_submit_button(label="Kirim Data SPT", type="primary")

# --- PROSES VALIDASI & PENGIRIMAN ---
if submit_button:
    # 1. Validasi OPD
    if not opd_final:
        st.error("❌ Nama OPD belum dipilih atau diisi!")
        st.stop()

    # 2. Validasi Kelengkapan Data
    input_wajib = [nama, nip, pangkat, jabatan, no_hp, email, nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan]
    if not all(input_wajib):
        st.error("❌ Mohon lengkapi semua kolom isian data!")
        st.stop()

    # 3. Validasi Format NIP (Harus Angka & 18 Digit)
    if not (nip.isdigit() and len(nip) == 18):
        st.error("❌ NIP Admin tidak valid! Harus berupa 18 digit angka.")
        st.stop()
        
    if not (nip_atasan.isdigit() and len(nip_atasan) == 18):
        st.error("❌ NIP Atasan tidak valid! Harus berupa 18 digit angka.")
        st.stop()

    # 4. Validasi Tanda Tangan
    if canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("❌ Tanda tangan belum diisi!")
        st.stop()

    # 5. Proses Kirim ke Google Sheets
    try:
        with st.spinner('Sedang mengirim data ke server...'):
            # A. Proses Gambar ke Base64
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            img.thumbnail((300, 150)) # Resize agar tidak terlalu besar di Excel
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            data_ttd = f"data:image/png;base64,{img_base64}"

            # B. Timestamp
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # C. Susun Data (Tambah ' di depan NIP agar terbaca Text di Excel)
            row_data = [[
                now, 
                opd_final, 
                "'" + nip, 
                nama, 
                pangkat, 
                jabatan, 
                no_hp, 
                email, 
                "'" + nip_atasan, 
                nama_atasan, 
                pangkat_atasan, 
                jabatan_atasan, 
                data_ttd
            ]]
            
            # D. Kirim
            if sheets_service:
                sheets_service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID, 
                    range="Sheet1!A1",
                    valueInputOption="USER_ENTERED", 
                    body={'values': row_data}
                ).execute()
            
                st.success(f"✅ Data berhasil dikirim! Terima kasih Sdr/i {nama}.")
                st.balloons()
            else:
                st.error("Gagal terhubung ke Google Sheets. Cek koneksi server.")

    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey; font-size: 0.8em;'>© 2026 Bagian Organisasi Setda Kab. Muaro Jambi</div>", unsafe_allow_html=True)
