import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from io import BytesIO
from PIL import Image

# --- LIBRARY UNTUK PDF TEMPLATE ---
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered", page_icon="📝")

# --- 2. KONEKSI GOOGLE SHEETS ---
@st.cache_resource
def get_sheets_service():
    try:
        if "gcp_service_account" in st.secrets:
            cred_info = st.secrets["gcp_service_account"]
            creds = service_account.Credentials.from_service_account_info(cred_info)
            return build('sheets', 'v4', credentials=creds)
        else:
            return None
    except Exception as e:
        st.error(f"Error Koneksi Google Sheets: {e}")
        return None

sheets_service = get_sheets_service()
SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

# --- 3. FUNGSI GENERATE PDF (OVERLAY TEMPLATE) ---
def create_pdf_from_template(data, signature_img):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    # --- KOORDINAT DATA ADMIN ---
    can.setFont("Helvetica", 11)
    x_data = 7.2 * cm  # Sesuaikan dengan letak titik dua di template
    
    # Menyesuaikan tinggi (Y) dengan baris di template PDF Anda
    can.drawString(x_data, 19.3 * cm, f": {data['nama']}")
    can.drawString(x_data, 18.6 * cm, f": {data['nip']}")
    can.drawString(x_data, 17.9 * cm, f": {data['pangkat']}")
    can.drawString(x_data, 17.2 * cm, f": {data['jabatan']}")
    can.drawString(x_data, 16.5 * cm, f": {data['no_hp']}")
    can.drawString(x_data, 15.8 * cm, f": {data['email']}")

    # --- KOORDINAT TANDA TANGAN & ATASAN ---
    x_ttd = 12.0 * cm
    
    # Tanggal di bagian bawah
    tgl_teks = datetime.datetime.now().strftime('%d %B %Y')
    can.drawString(x_ttd + 2.0 * cm, 7.8 * cm, tgl_teks)
    
    # Jabatan Atasan
    can.setFont("Helvetica-Bold", 10)
    can.drawString(x_ttd, 6.8 * cm, data['jabatan_atasan'].upper())

    # Gambar Tanda Tangan
    if signature_img:
        img_temp = signature_img.convert("RGBA")
        img_reader = ImageReader(img_temp)
        can.drawImage(img_reader, x_ttd + 0.5 * cm, 4.3 * cm, width=4*cm, height=2*cm, mask='auto')

    # Nama dan NIP Atasan
    can.setFont("Helvetica-Bold", 11)
    can.drawString(x_ttd, 4.0 * cm, data['nama_atasan'])
    can.setFont("Helvetica", 11)
    can.drawString(x_ttd, 3.5 * cm, f"NIP. {data['nip_atasan']}")
    can.drawString(x_ttd, 3.0 * cm, data['pangkat_atasan'])

    can.save()
    packet.seek(0)

    try:
        new_pdf = PdfReader(packet)
        existing_pdf = PdfReader(open("templatespt.pdf", "rb"))
        output = PdfWriter()

        page = existing_pdf.pages[0]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

        final_buffer = BytesIO()
        output.write(final_buffer)
        final_buffer.seek(0)
        return final_buffer
    except Exception as e:
        st.error(f"Sistem tidak menemukan file 'templatespt.pdf'. Error: {e}")
        return None

# --- 4. FUNGSI DIALOG ---
@st.dialog("✅ SPT Berhasil Dibuat")
def show_success_dialog(nama_admin, pdf_data):
    st.write(f"Halo **{nama_admin}**, data Anda telah berhasil disimpan.")
    st.success("Silakan unduh dokumen SPT Anda di bawah ini:")
    
    st.download_button(
        label="📥 Download SPT (PDF)",
        data=pdf_data,
        file_name=f"SPT_{nama_admin.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
    
    if st.button("Tutup"):
        st.rerun()

# --- 5. DATA LIST OPD ---
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
    "RSUD Ahmad Ripin", "RSUD Sungai Bahar", "RSUD Sungai Gelam"
]

# --- 6. TAMPILAN APLIKASI ---
st.title("📝 Form SPT Admin OPD")
st.write("---")

# KOLOM BARU: PERIHAL SURAT TUGAS
st.header("I. Perihal & Unit Kerja")
perihal_spt = st.selectbox("Perihal Surat Tugas", ["SPT Rekon TPP dan SIMONA"])
opd_final = st.selectbox("Pilih Unit Kerja / OPD", [""] + sorted(list_opd))

with st.form("spt_form"):
    st.header("II. Data Admin (Penerima Tugas)")
    status_asn = st.radio("Status ASN:", ["PNS", "PPPK"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("Nama Lengkap & Gelar")
        pangkat = st.text_input("Pangkat / Golongan")
        no_hp = st.text_input("No. WhatsApp")
    with col2:
        nip = st.text_input("NIP Admin (18 Digit)", max_chars=18)
        jabatan = st.text_input("Jabatan")
        email = st.text_input("Email Aktif")

    st.write("---")
    st.header("III. Data Atasan Pemberi Perintah")
    col3, col4 = st.columns(2)
    with col3:
        nama_atasan = st.text_input("Nama Atasan & Gelar")
        pangkat_atasan = st.text_input("Pangkat Atasan")
    with col4:
        nip_atasan = st.text_input("NIP Atasan (18 Digit)", max_chars=18)
        jabatan_atasan = st.text_input("Jabatan Atasan")

    st.write("---")
    st.header("IV. Tanda Tangan Atasan")
    canvas_result = st_canvas(
        stroke_width=2, stroke_color="#000000", background_color="#ffffff",
        height=150, width=300, drawing_mode="freedraw", key="canvas_ttd"
    )

    submit_button = st.form_submit_button("Generate & Kirim SPT", type="primary")

# --- 7. LOGIKA SUBMIT ---
if submit_button:
    if not opd_final or not nama or not nip or not nama_atasan:
        st.error("Gagal: Mohon lengkapi semua data dan tanda tangan!")
    elif len(nip) != 18 or len(nip_atasan) != 18:
        st.error("Gagal: NIP harus 18 digit!")
    elif canvas_result.image_data is None:
        st.error("Gagal: Tanda tangan diperlukan!")
    else:
        try:
            with st.spinner('Memproses dokumen...'):
                img_ttd = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                
                data_spt = {
                    'perihal': perihal_spt,
                    'opd': opd_final, 'nama': nama, 'nip': nip, 'pangkat': pangkat,
                    'jabatan': jabatan, 'no_hp': no_hp, 'email': email,
                    'nama_atasan': nama_atasan, 'nip_atasan': nip_atasan,
                    'jabatan_atasan': jabatan_atasan, 'pangkat_atasan': pangkat_atasan
                }

                pdf_file = create_pdf_from_template(data_spt, img_ttd)
                
                if pdf_file:
                    if sheets_service:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        # Data yang dikirim ke Sheets termasuk Kolom Perihal
                        row = [[now, perihal_spt, opd_final, status_asn, f"'{nip}", nama, pangkat, jabatan, no_hp, email, f"'{nip_atasan}", nama_atasan]]
                        sheets_service.spreadsheets().values().append(
                            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                            valueInputOption="USER_ENTERED", body={'values': row}
                        ).execute()
                        
                        st.balloons()
                        show_success_dialog(nama, pdf_file)
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {e}")

st.markdown("---")
st.caption("Tim Bagian Organisasi Muaro Jambi - 2026")
