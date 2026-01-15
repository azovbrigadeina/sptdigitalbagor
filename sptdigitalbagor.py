import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from io import BytesIO
from PIL import Image

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered")

# --- KREDENSIAL ---
# Pastikan secrets "gcp_service_account" sudah terisi di Streamlit Cloud
creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
sheets_service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

# --- DAFTAR OPD LENGKAP ---
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
    "Kecamatan Sungai Bahar", "Kecamatan Sungai Gelam", "Puskesmas",
    "RSUD Ahmad Ripin", "RSUD Sungai Bahar", "RSUD Sungai Gelam"
]

# --- JUDUL & DESKRIPSI ---
st.title("Form Surat Perintah Tugas")
st.markdown("""
Formulir ini digunakan untuk mendata petugas yang ditunjuk sebagai **Admin Organisasi Perangkat Daerah** dalam rangka penginputan Informasi Jabatan ke aplikasi SIMONA E-ANJAB-ABK. Pendataan ini merupakan tindak lanjut dari Surat Sekretaris Daerah Kabupaten Muaro Jambi Nomor **000.8/040/Org** Tanggal **16 Januari 2026**.

Tujuan utama dari penugasan ini adalah pemenuhan bukti dukung (*evidence*) dalam rangka pemberian persetujuan **Tambahan Penghasilan Pegawai (TPP)** di lingkungan Pemerintah Kabupaten Muaro Jambi.
""")

st.write("---")

# --- FORMULIR ---
with st.form("spt_form"):
    st.subheader("I. Data Admin OPD")
    opd = st.selectbox("1. Pilih OPD", [""] + list_opd)
    nama = st.text_input("2. Nama Lengkap dan Gelar")
    
    nip = st.text_input("3. NIP Admin (18 Digit Angka)")
    if nip and not nip.isdigit():
        st.error("⚠️ NIP harus berupa angka saja!")
        
    pangkat = st.text_input("4. Pangkat / Golongan")
    jabatan = st.text_input("5. Jabatan")
    no_hp = st.text_input("6. Nomor Handphone (WhatsApp)")
    email = st.text_input("7. Alamat E-mail")

    st.write("---")
    st.subheader("II. Data Atasan Langsung")
    nama_atasan = st.text_input("1. Nama Atasan Lengkap dan Gelar")
    
    nip_atasan = st.text_input("2. NIP Atasan (Angka)")
    if nip_atasan and not nip_atasan.isdigit():
        st.error("⚠️ NIP Atasan harus berupa angka saja!")
        
    pangkat_atasan = st.text_input("3. Pangkat / Golongan Atasan")
    jabatan_atasan = st.text_input("4. Jabatan Atasan")

    st.write("---")
    st.subheader("III. Tanda Tangan")
    st.info("Silakan coret tanda tangan Anda pada kotak di bawah ini:")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#ffffff",
        height=180,
        width=500,
        drawing_mode="freedraw",
        key="canvas_admin",
    )

    # Tombol Submit
    submit_button = st.form_submit_button(label="Kirim Data SPT")

# --- PROSES VALIDASI & PENGIRIMAN ---
if submit_button:
    # 1. Cek Kelengkapan Data
    data_list = [opd, nama, nip, pangkat, jabatan, no_hp, email, nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan]
    
    if "" in data_list:
        st.error("❌ Gagal Terkirim! Semua kolom data wajib diisi.")
    elif not nip.isdigit() or not nip_atasan.isdigit():
        st.error("❌ Gagal Terkirim! NIP dan NIP Atasan harus berupa angka.")
    elif canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("❌ Gagal Terkirim! Tanda tangan tidak boleh kosong.")
    else:
        # 2. Proses Tanda Tangan ke Base64
        try:
            with st.spinner('Sedang memproses data...'):
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                # Optimasi sedikit agar render di Sheets lebih enteng
                img.thumbnail((400, 200)) 
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                data_ttd = f"data:image/png;base64,{img_base64}"

                # 3. Kirim ke Google Sheets
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row_data = [[
                    now, opd, nama, nip, pangkat, jabatan, no_hp, email, 
                    nama_atasan, nip_atasan, pangkat_atasan, jabatan_atasan, data_ttd
                ]]
                
                sheets_service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID, 
                    range="Sheet1!A1",
                    valueInputOption="RAW", 
                    body={'values': row_data}
                ).execute()
                
                st.success(f"✅ Berhasil! Data SPT untuk {nama} telah tersimpan di sistem.")
                st.balloons()
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {e}")

st.write("---")
st.caption("© 2026 Pemerintah Kabupaten Muaro Jambi - Bagian Organisasi")
