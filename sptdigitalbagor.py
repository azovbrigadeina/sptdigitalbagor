import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from io import BytesIO
from PIL import Image

# --- LIBRARY BARU UNTUK PDF ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered", page_icon="📝")

# --- 2. CSS ---
st.markdown("""
    <style>
    .custom-footer {
        text-align: center;
        color: #666;
        font-size: 0.8rem;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #eee;
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

# --- 4. FUNGSI GENERATE PDF (SEDERHANA) ---
def create_pdf(data, signature_img):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # -- KOP SURAT (SIMPEL) --
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 2 * cm, "PEMERINTAH KABUPATEN MUARO JAMBI")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 2.6 * cm, f"OPD: {data['opd'].upper()}")
    c.line(2*cm, height - 3*cm, width - 2*cm, height - 3*cm) # Garis bawah kop

    # -- JUDUL SURAT --
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 4.5 * cm, "SURAT PERINTAH TUGAS")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 5 * cm, "Nomor: 800 / ... / 2026") # Dummy Nomor

    # -- ISI SURAT --
    y_start = height - 7 * cm
    c.setFont("Helvetica", 11)
    
    text_opening = "Yang bertanda tangan di bawah ini:"
    c.drawString(2.5 * cm, y_start, text_opening)
    
    # Data Atasan
    c.drawString(3 * cm, y_start - 1*cm, f"Nama   : {data['nama_atasan']}")
    c.drawString(3 * cm, y_start - 1.6*cm, f"NIP    : {data['nip_atasan']}")
    c.drawString(3 * cm, y_start - 2.2*cm, f"Jabatan: {data['jabatan_atasan']}")

    # Kalimat Perintah
    c.drawString(2.5 * cm, y_start - 3.5*cm, "MEMERINTAHKAN / MENUGASKAN KEPADA:")

    # Data Admin (Yang Bertugas)
    c.drawString(3 * cm, y_start - 4.5*cm, f"Nama   : {data['nama']}")
    c.drawString(3 * cm, y_start - 5.1*cm, f"NIP    : {data['nip']}")
    c.drawString(3 * cm, y_start - 5.7*cm, f"Pangkat: {data['pangkat']}")
    c.drawString(3 * cm, y_start - 6.3*cm, f"Jabatan: {data['jabatan']}")
    c.drawString(3 * cm, y_start - 6.9*cm, f"Status : {data['status_asn']}")

    # Keperluan
    c.drawString(2.5 * cm, y_start - 8.5*cm, "Untuk:")
    c.drawString(3 * cm, y_start - 9.1*cm, "1. Bertugas sebagai ADMIN OPD pada Aplikasi SIMONA / E-ANJAB.")
    c.drawString(3 * cm, y_start - 9.7*cm, "2. Melaksanakan perintah ini dengan seksama dan tanggung jawab.")

    # -- TANDA TANGAN --
    # Posisi di kanan bawah
    y_sign = y_start - 14*cm
    c.drawString(11 * cm, y_sign, "Ditetapkan di: Sengeti")
    c.drawString(11 * cm, y_sign - 0.6*cm, f"Pada Tanggal : {datetime.datetime.now().strftime('%d-%m-%Y')}")
    
    c.drawString(11 * cm, y_sign - 2*cm, "Yang Memberi Perintah,")
    
    # Memproses Gambar Tanda Tangan agar masuk ke PDF
    if signature_img:
        # Resize gambar ttd agar pas
        signature_img.thumbnail((150, 80))
        img_reader = ImageReader(signature_img)
        c.drawImage(img_reader, 11 * cm, y_sign - 5*cm, width=4*cm, height=2*cm, mask='auto')

    c.drawString(11 * cm, y_sign - 6*cm, f"({data['nama']})") # Nama Admin Tanda Tangan
    c.setFont("Helvetica", 9)
    c.drawString(11 * cm, y_sign - 6.5*cm, "Dokumen ini ditandatangani secara elektronik")

    # -- SIMPAN --
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 5. FUNGSI DIALOG ---
@st.dialog("✅ Data Berhasil Disimpan")
def show_success_dialog(nama_admin, pdf_data):
    st.write(f"Terimakasih **{nama_admin}**.")
    st.success("Data telah terkirim ke DB Bagian Organisasi.")
    
    st.write("---")
    st.write("👇 **Silakan Unduh Bukti SPT Anda:**")
    
    # TOMBOL DOWNLOAD PDF
    st.download_button(
        # Perhatikan: Saya pakai tanda petik satu (') di awal dan akhir kalimat
        label='📄 Download SPT (PDF) "Hanya Eksperimental"', 
        data=pdf_data,
        file_name=f"SPT_{nama_admin.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
    
    st.write("")
    if st.button("Tutup & Input Baru"):
        st.rerun()
        
# --- 6. DATA LIST OPD ---
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

# --- 7. TAMPILAN APLIKASI ---

st.title("Form Surat Perintah Tugas")
st.markdown("Pendataan Admin OPD")
st.write("---")

st.selectbox("Jenis Layanan", ["Surat Perintah Tugas (SPT) - Penunjukan Admin"], disabled=True)
st.write("") 

# --- BAGIAN I: IDENTITAS OPD ---
st.header("I. Unit Kerja")
opsi_opd_terpilih = st.selectbox("Pilih Unit Kerja / OPD", [""] + sorted(list_opd) + ["Lainnya (Isi Manual)"])

opd_manual = ""
if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_manual = st.text_input("Tuliskan Nama Unit Kerja / OPD Anda:")

if opsi_opd_terpilih == "Lainnya (Isi Manual)":
    opd_final = opd_manual
else:
    opd_final = opsi_opd_terpilih

# --- BAGIAN FORM UTAMA ---
with st.form("spt_form", clear_on_submit=False):
    
    st.write("")
    st.header("II. Data Admin (Penerima Tugas)")
    
    status_asn = st.radio("Status ASN:", ["PNS", "PPPK"], horizontal=True)
    st.write("")
    
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
    st.header("IV. Tanda Tangan Atasan")
    st.caption("Silakan tanda tangan pada area di bawah ini:")
    
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
    submit_button = st.form_submit_button(label="Kirim Data SPT", type="primary")

# --- 8. PROSES VALIDASI & KIRIM ---
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
        with st.spinner('Sedang mengirim & membuat PDF...'):
            # 1. Proses Gambar Tanda Tangan
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            
            # Klon gambar untuk PDF (resolusi asli lebih baik)
            img_for_pdf = img.copy()

            # Proses untuk Excel (Resize kecil)
            img.thumbnail((300, 150))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            data_ttd = f"data:image/png;base64,{img_base64}"

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 2. Susun Data Dictionary untuk PDF
            data_spt = {
                'opd': opd_final,
                'status_asn': status_asn,
                'nama': nama,
                'nip': nip,
                'pangkat': pangkat,
                'jabatan': jabatan,
                'nama_atasan': nama_atasan,
                'nip_atasan': nip_atasan,
                'jabatan_atasan': jabatan_atasan
            }

            # 3. Generate PDF
            pdf_file = create_pdf(data_spt, img_for_pdf)

            # 4. Kirim ke Google Sheets
            row_data = [[
                now, opd_final, status_asn, "'" + nip, nama, pangkat, jabatan, no_hp, email, 
                "'" + nip_atasan, nama_atasan, pangkat_atasan, jabatan_atasan, data_ttd
            ]]
            
            if sheets_service:
                sheets_service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID, 
                    range="Sheet1!A1",
                    valueInputOption="USER_ENTERED", 
                    body={'values': row_data}
                ).execute()
                
                st.balloons()
                
                # 5. Tampilkan Dialog dengan Tombol Download
                show_success_dialog(nama, pdf_file)
                
            else:
                st.error("Gagal terhubung ke Database.")

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div class="custom-footer">
    Made in Love ❤️ oleh Tim Anjab Bagor Muaro Jambi
</div>
""", unsafe_allow_html=True)
