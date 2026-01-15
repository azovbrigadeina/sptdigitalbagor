import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import datetime

# Judul Aplikasi
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered")
st.title("📝 Form SPT Admin OPD")
st.subheader("Pemerintah Kabupaten Muaro Jambi")

# 1. Pilihan OPD (Data yang Anda berikan)
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

with st.form("spt_form"):
    # Input Data
    opd_pilihan = st.selectbox("1. Pilih OPD", ["-- Pilih OPD --"] + list_opd)
    nama = st.text_input("2. Nama Lengkap & Gelar")
    nip = st.text_input("3. NIP")
    pangkat = st.text_input("4. Pangkat / Golongan")
    jabatan = st.text_input("5. Jabatan")
    no_hp = st.text_input("6. Nomor HP (WhatsApp)")
    email = st.text_input("7. Alamat E-mail")

    st.write("---")
    st.write("### ✍️ Tanda Tangan Digital")
    st.info("Silakan coret tanda tangan Anda pada kotak di bawah ini.")
    
    # Komponen Tanda Tangan
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#ffffff",
        height=200,
        width=400,
        drawing_mode="freedraw",
        key="canvas",
    )

    submit_button = st.form_submit_button(label="Kirim Data & Tanda Tangan")

if submit_button:
    if opd_pilihan == "-- Pilih OPD --" or not nama or not nip:
        st.error("Mohon lengkapi Data Utama (OPD, Nama, dan NIP) sebelum mengirim.")
    elif canvas_result.image_data is None:
        st.error("Tanda tangan belum diisi!")
    else:
        # Proses Simpan (Contoh: Simpan Lokal)
        st.success(f"Berhasil! Data {nama} dari {opd_pilihan} telah diterima.")
        
        # Konversi tanda tangan ke gambar
        img_data = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"TTD_{nama}_{timestamp}.png"
        
        # Opsi: Tampilkan hasil di aplikasi
        st.write("Pratinjau Tanda Tangan:")
        st.image(img_data)
        
        # Catatan: Untuk menyimpan ke Cloud atau Database, Anda bisa menambahkan
        # integrasi API Google Drive atau SQLAlchemy di sini.
