import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd
import datetime
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered")

# --- HEADER & DESKRIPSI ---
st.title("Form Surat Perintah Tugas")
st.markdown(f"""
**Formulir ini digunakan untuk mendata petugas yang ditunjuk sebagai Admin Organisasi Perangkat Daerah dalam rangka penginputan Informasi Jabatan ke aplikasi SIMONA E-ANJAB-ABK.** Pendataan ini merupakan tindak lanjut dari Surat Sekretaris Daerah Kabupaten Muaro Jambi Nomor **000.8/040/Org** Tanggal **16 Januari 2026**.

Tujuan utama dari penugasan ini adalah pemenuhan bukti dukung (*evidence*) dalam rangka pemberian persetujuan **Tambahan Penghasilan Pegawai (TPP)** di lingkungan Pemerintah Kabupaten Muaro Jambi.
""")
st.write("---")

# --- DATA PILIHAN OPD ---
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

# --- FORM INPUT ---
with st.form("spt_form", clear_on_submit=True):
    opd_pilihan = st.selectbox("Pilih Organisasi Perangkat Daerah (OPD)", ["-- Pilih OPD --"] + list_opd)
    nama = st.text_input("Nama Lengkap & Gelar")
    nip = st.text_input("NIP (18 Digit)")
    pangkat = st.text_input("Pangkat / Golongan")
    jabatan = st.text_input("Jabatan")
    no_hp = st.text_input("Nomor HP (WhatsApp)")
    email = st.text_input("Alamat E-mail")

    st.write("### Tanda Tangan Digital")
    st.caption("Gunakan jari (di HP) atau mouse (di laptop) untuk tanda tangan pada kotak di bawah:")
    
    # Komponen Canvas untuk TTD
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff",
        height=150,
        width=500,
        drawing_mode="freedraw",
        key="canvas",
    )

    submitted = st.form_submit_button("Kirim Data SPT")

# --- PROSES SIMPAN ---
if submitted:
    if opd_pilihan == "-- Pilih OPD --" or not nama or not nip:
        st.warning("⚠️ Mohon lengkapi OPD, Nama, dan NIP.")
    else:
        # Menyiapkan data untuk disimpan
        data_baru = {
            "Waktu": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "OPD": opd_pilihan,
            "Nama": nama,
            "NIP": nip,
            "Pangkat": pangkat,
            "Jabatan": jabatan,
            "No HP": no_hp,
            "Email": email
        }
        
        # Simpan ke CSV (database lokal sederhana)
        df = pd.DataFrame([data_baru])
        if not os.path.isfile('data_spt_2026.csv'):
            df.to_csv('data_spt_2026.csv', index=False)
        else:
            df.to_csv('data_spt_2026.csv', mode='a', index=False, header=False)
            
        # Simpan Gambar TTD
        if canvas_result.image_data is not None:
            img_ttd = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            img_ttd.save(f"TTD_{nip}_{datetime.datetime.now().strftime('%H%M%S')}.png")

        st.success(f"✅ Berhasil! Data Admin OPD untuk {nama} telah tersimpan.")
        st.balloons()

# --- BAGIAN ADMIN (HANYA UNTUK LIHAT DATA) ---
with st.expander("Lihat Data Terkirim (Khusus Admin)"):
    if os.path.isfile('data_spt_2026.csv'):
        view_df = pd.read_csv('data_spt_2026.csv')
        st.dataframe(view_df)
        st.download_button("Download Excel (CSV)", view_df.to_csv(index=False), "data_spt_2026.csv", "text/csv")
    else:
        st.info("Belum ada data yang masuk.")
