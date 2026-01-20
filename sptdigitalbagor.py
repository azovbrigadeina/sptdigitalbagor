import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from io import BytesIO
from PIL import Image
import os

# Penanganan error memori pada server Linux
os.environ['OPENBLAS_NUM_THREADS'] = '1'

# Library untuk PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Form SPT Admin OPD", layout="centered", page_icon="📝")

# --- 2. KONEKSI GOOGLE SHEETS ---
def get_sheets_service():
    try:
        if "gcp_service_account" in st.secrets:
            creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
            return build('sheets', 'v4', credentials=creds)
        return None
    except Exception:
        return None

sheets_service = get_sheets_service()
SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

# --- 3. FUNGSI GENERATE PDF ---
def create_pdf(data, signature_img):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Kop Surat
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 2 * cm, "Pemerintah Kabupaten Muaro Jambi")
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, height - 2.6 * cm, f"UNIT KERJA: {data['opd'].upper()}")
    c.line(2*cm, height - 3*cm, width - 2*cm, height - 3*cm)

    # Judul
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 4.5 * cm, "SURAT PERINTAH TUGAS")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 5 * cm, f"Nomor: 800 / {datetime.datetime.now().strftime('%m')} / ORG / 2026")

    # Isi Surat
    y = height - 7 * cm
    c.setFont("Helvetica", 11)
    c.drawString(2.5 * cm, y, "Yang bertanda tangan di bawah ini:")
    c.drawString(3 * cm, y - 0.8*cm, f"Nama      : {data['nama_atasan']}")
    c.drawString(3 * cm, y - 1.4*cm, f"NIP       : {data['nip_atasan']}")
    c.drawString(3 * cm, y - 2.0*cm, f"Jabatan   : {data['jabatan_atasan']}")

    c.drawString(2.5 * cm, y - 3.5*cm, "MEMERINTAHKAN / MENUGASKAN KEPADA:")
    c.drawString(3 * cm, y - 4.5*cm, f"Nama      : {data['nama']}")
    c.drawString(3 * cm, y - 5.1*cm, f"NIP       : {data['nip']}")
    c.drawString(3 * cm, y - 5.7*cm, f"Pangkat   : {data['pangkat']}")
    c.drawString(3 * cm, y - 6.3*cm, f"Jabatan   : {data['jabatan']}")

    c.drawString(2.5 * cm, y - 8.5*cm, "Untuk:")
    c.drawString(3 * cm, y - 9.1*cm, "1. Menjadi ADMIN OPD pada Aplikasi SIMONA / E-ANJAB-ABK.")
    c.drawString(3 * cm, y - 9.7*cm, "2. Melaksanakan tugas dengan penuh tanggung jawab.")

    # Tanda Tangan
    y_sign = y - 13*cm
    c.drawString(11 * cm, y_sign, "Ditetapkan di: Sengeti")
    c.drawString(11 * cm, y_sign - 0.6*cm, f"Tanggal : {datetime.datetime.now().strftime('%d-%m-%Y')}")
    c.drawString(11 * cm, y_sign - 1.5*cm, "Yang Memberi Perintah,")
    
    if signature_img:
        img_reader = ImageReader(signature_img)
        c.drawImage(img_reader, 11 * cm, y_sign - 4.5*cm, width=4*cm, height=2*cm, mask='auto')

    c.setFont("Helvetica-Bold", 11)
    c.drawString(11 * cm, y_sign - 5.5*cm, f"{data['nama_atasan']}")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 4. DIALOG BERHASIL ---
@st.dialog("✅ Data Berhasil Disimpan")
def success_dialog(nama_admin, pdf_data):
    st.success(f"Terimakasih **{nama_admin}**. Data telah terkirim.")
    st.write("Silakan unduh dokumen SPT Anda:")
    st.download_button(label="📄 Download SPT (PDF)", data=pdf_data, 
                       file_name=f"SPT_{nama_admin.replace(' ', '_')}.pdf", mime="application/pdf")
    if st.button("Tutup & Input Baru"): st.rerun()

# --- 5. DAFTAR OPD ---
list_opd = [
    "Bagian Tata Pemerintahan", "Bagian Kesejahteraan Rakyat", "Bagian Hukum",
    "Bagian Kerjasama", "Bagian Perekonomian", "Bagian Pembangunan dan Sumber Daya Alam",
    "Bagian Pengadaan Barang dan Jasa", "Bagian Umum", "Bagian Organisasi",
    "Bagian Protokol dan Komunikasi Pimpinan", "Bagian Perencanaan dan Keuangan",
    "Sekretariat DPRD", "Inspektorat Daerah", "Dinas Pendidikan dan Kebudayaan",
    "Dinas Pariwisata, Kepemudaan dan Olahraga", "Dinas Kesehatan", 
    "Dinas Sosial, PP dan PA", "Dinas Pengendalian Penduduk dan KB",
    "Dinas Dukcapil", "Dinas PMD", "Satuan Polisi Pamong Praja",
    "DPMPTSP", "Diskoperindag", "Disnakertrans", "Diskominfo",
    "Dinas Perkim", "Dinas PUPR", "Dinas Perhubungan", "Dinas Lingkungan Hidup",
    "Dinas Tanaman Pangan dan Hortikultura", "Dinas Ketahanan Pangan",
    "Dinas Perkebunan dan Peternakan", "Dinas Perikanan", "Dinas Perpustakaan dan Arsip",
    "Bapperida", "BKPSDM", "BPKAD", "BPPRD", "Dinas Damkar", "BPBD", "Kesbangpol",
    "Kecamatan Bahar Selatan", "Kecamatan Bahar Utara", "Kecamatan Jambi Luar Kota",
    "Kecamatan Taman Rajo", "Kecamatan Kumpeh", "Kecamatan Kumpeh Ulu",
    "Kecamatan Maro Sebo", "Kecamatan Mestong", "Kecamatan Sekernan",
    "Kecamatan Sungai Bahar", "Kecamatan Sungai Gelam", 
    "RSUD Ahmad Ripin", "RSUD Sungai Bahar", "RSUD Sungai Gelam"
]

# --- 6. TAMPILAN ---
st.title("Form Surat Perintah Tugas")
st.write("---")

st.header("I. Unit Kerja")
opsi_opd = st.selectbox("Pilih Unit Kerja / OPD", [""] + sorted(list_opd) + ["LAINNYA (ISI MANUAL)"])

opd_final = ""
if opsi_opd == "LAINNYA (ISI MANUAL)":
    opd_final = st.text_input("Tuliskan Nama Unit Kerja / OPD Anda:")
else:
    opd_final = opsi_opd

with st.form("spt_form"):
    st.header("II. Data Admin (Penerima Tugas)")
    status_asn = st.radio("Status Admin:", ["PNS", "PPPK"], horizontal=True)
    c1, c2 = st.columns(2)
    with c1:
        nama = st.text_input("Nama Lengkap Admin")
        nip = st.text_input("NIP Admin (18 Digit)", max_chars=18)
        pangkat = st.text_input("Pangkat Admin")
        no_hp = st.text_input("No. HP (WA)")
    with c2:
        jabatan = st.text_input("Jabatan Admin")
        email = st.text_input("Email Admin")

    st.header("III. Data Atasan Langsung")
    c3, c4 = st.columns(2)
    with c3:
        nama_atasan = st.text_input("Nama Atasan")
        nip_atasan = st.text_input("NIP Atasan (18 Digit)", max_chars=18)
    with c4:
        pangkat_atasan = st.text_input("Pangkat Atasan")
        jabatan_atasan = st.text_input("Jabatan Atasan")

    st.header("IV. Tanda Tangan Atasan")
    canvas_result = st_canvas(stroke_width=2, stroke_color="#000", background_color="#fff",
                             height=150, width=400, drawing_mode="freedraw", key="canvas")

    submit = st.form_submit_button("Kirim Data", type="primary")

# --- 7. LOGIKA ---
if submit:
    if not opd_final or "" in [nama, nip, pangkat, jabatan, nama_atasan, nip_atasan]:
        st.error("❌ Semua kolom wajib diisi!")
    elif not (nip.isdigit() and len(nip) == 18) or not (nip_atasan.isdigit() and len(nip_atasan) == 18):
        st.error("❌ NIP harus 18 digit angka!")
    elif canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("❌ Tanda tangan belum diisi!")
    else:
        try:
            with st.spinner("Memproses..."):
                # Proses gambar dengan aman
                img_pil = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                
                # Untuk PDF
                img_pdf = img_pil.copy()
                img_pdf.thumbnail((400, 200))
                
                # Untuk Sheets (Base64)
                img_sheets = img_pil.copy()
                img_sheets.thumbnail((200, 100))
                buffered = BytesIO()
                img_sheets.save(buffered, format="PNG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()

                # Generate PDF & Kirim Sheets
                data_spt = {'opd': opd_final, 'nama': nama, 'nip': nip, 'pangkat': pangkat, 
                            'jabatan': jabatan, 'nama_atasan': nama_atasan, 
                            'nip_atasan': nip_atasan, 'jabatan_atasan': jabatan_atasan}
                pdf_file = create_pdf(data_spt, img_pdf)

                row = [[datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                        opd_final, status_asn, "'" + nip, nama, pangkat, jabatan, 
                        no_hp, email, "'" + nip_atasan, nama_atasan, 
                        pangkat_atasan, jabatan_atasan, f"data:image/png;base64,{img_b64}"]]
                
                sheets_service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                    valueInputOption="USER_ENTERED", body={'values': row}).execute()

                success_dialog(nama, pdf_file)
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
