import streamlit as st
from streamlit_drawable_canvas import st_canvas
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Mm
import os
import base64

# --- 1. SETTING HALAMAN & CUSTOM CSS BACKGROUND ---
st.set_page_config(page_title="Kirim Surat Tugas", layout="centered", page_icon="📝")

st.markdown("""
    <style>
    /* 1. Latar Belakang Gradasi sesuai gambar */
    .stApp {
        background: linear-gradient(180deg, #245D8F 0%, #4CA085 50%, #D9E021 100%);
        background-attachment: fixed;
    }

    /* 2. Penyesuaian Warna Teks agar terbaca (Putih dengan Shadow) */
    h1, h2, h3, h4, label, .stMarkdown p {
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }

    /* 3. Styling Input Box agar tetap bersih */
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: black !important;
        border-radius: 8px !important;
    }

    /* 4. Styling Tombol Kirim */
    div.stButton > button:first-child {
        background-color: #245D8F;
        color: white;
        border: 2px solid #D9E021;
        border-radius: 10px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #D9E021;
        color: #245D8F;
    }

    /* 5. Footer Box */
    .footer-box {
        background-color: rgba(255, 255, 255, 0.2);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(5px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KONEKSI GOOGLE SHEETS (Logika Tetap) ---
@st.cache_resource
def get_sheets_service():
    try:
        if "gcp_service_account" in st.secrets:
            cred_info = st.secrets["gcp_service_account"]
            creds = service_account.Credentials.from_service_account_info(cred_info)
            return build('sheets', 'v4', credentials=creds)
        return None
    except:
        return None

sheets_service = get_sheets_service()
SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798"

# --- 3. FUNGSI KONVERSI TTD ---
def get_base64_signature(signature_img):
    try:
        if signature_img is not None and signature_img.any():
            img_rgba = Image.fromarray(signature_img.astype('uint8'), 'RGBA')
            white_bg = Image.new("RGBA", img_rgba.size, (255, 255, 255, 255))
            final_img = Image.alpha_composite(white_bg, img_rgba).convert("RGB")
            buffered = BytesIO()
            final_img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        return "Tidak ada TTD"
    except:
        return "Error TTD"

# --- 4. FUNGSI GENERATE DOCX ---
def create_docx_final(data, signature_img):
    template_name = "template spt simona.docx" 
    if not os.path.exists(template_name):
        st.error("File template tidak ditemukan!")
        return None
    try:
        doc = Document(template_name)
        replacements = {
            '{{unitkerja}}': str(data['unit_kerja']),
            '{{nama_admin}}': str(data['nama']),
            '{{pangkat_admin}}': str(data['pangkat']),
            '{{NIP_admin}}': str(data['nip']),
            '{{Jabatanadmin}}': str(data['jabatan']),
            '{{no_hpadmin}}': str(data['no_hp']),
            '{{email_admin}}': str(data['email']),
            '{{JABATAN_ATASAN}}': str(data['j_atasan']),
            '{{NAMA_ATASAN}}': str(data['n_atasan']),
            '{{NIP_ATASAN}}': str(data['nip_atasan']),
            '{{PANGKAT_GOL_ATASAN}}': str(data['p_atasan']),
            '{{TTL}}': datetime.datetime.now().strftime('%d %B %Y')
        }

        for paragraph in doc.paragraphs:
            for key, value in replacements.items():
                if key in paragraph.text:
                    for run in paragraph.runs:
                        if key in run.text:
                            run.text = run.text.replace(key, value)
            
            if '{{ttd}}' in paragraph.text:
                for run in paragraph.runs:
                    if '{{ttd}}' in run.text:
                        run.text = run.text.replace('{{ttd}}', "")
                if signature_img is not None:
                    img_rgba = Image.fromarray(signature_img.astype('uint8'), 'RGBA')
                    white_bg = Image.new("RGBA", img_rgba.size, (255, 255, 255, 255))
                    final_img = Image.alpha_composite(white_bg, img_rgba).convert("RGB")
                    img_io = BytesIO()
                    final_img.save(img_io, format='PNG')
                    img_io.seek(0)
                    new_run = paragraph.add_run()
                    new_run.add_picture(img_io, width=Mm(45))

        target_stream = BytesIO()
        doc.save(target_stream)
        target_stream.seek(0)
        return target_stream
    except Exception as e:
        st.error(f"Gagal memproses dokumen: {e}")
        return None

# --- 5. TAMPILAN UI ---
st.markdown("<h2 style='text-align: center;'>📝 Kirim Surat Tugas</h2>", unsafe_allow_html=True)
st.write("---")

st.subheader("I. Perihal & Unit Kerja")
opsi_perihal = st.selectbox("Pilih Perihal:", ["SPT Rekon TPP dan SIMONA", "Lainnya"])
perihal_final = st.text_input("Ketik Perihal Manual:") if opsi_perihal == "Lainnya" else opsi_perihal

list_opd = ["Sekretariat Daerah", "Sekretariat DPRD", "Inspektorat Daerah", "Dinas Pendidikan dan Kebudayaan", "Dinas Kesehatan", "Dinas Pekerjaan Umum dan Penataan Ruang", "Dinas Perumahan dan Kawasan Permukiman", "Satuan Polisi Pamong Praja dan Damkar", "Dinas Sosial, Pemberdayaan Perempuan dan Perlindungan Anak", "Dinas Lingkungan Hidup", "Dinas Kependudukan dan Pencatatan Sipil", "Dinas Pemberdayaan Masyarakat dan Desa", "Dinas Perhubungan", "Dinas Komunikasi dan Informatika", "Dinas Koperasi, Perindustrian dan Perdagangan", "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu", "Dinas Pariwisata, Pemuda dan Olahraga", "Dinas Perpustakaan dan Arsip Daerah", "Dinas Perikanan", "Dinas Ketahanan Pangan", "Dinas Tanaman Pangan dan Hortikultura", "Dinas Perkebunan dan Peternakan", "Dinas Tenaga Kerja dan Transmigrasi", "Dinas Pengendalian Penduduk dan Keluarga Berencana", "Badan Perencanaan Pembanguan Dan Riset Inovasi Daerah", "Badan Pengelola Keuangan dan Aset Daerah", "Badan Pengelola Pajak dan Retribusi Daerah", "Badan Kepegawaian dan Pengembangan Sumber Daya Manusia ", "Badan Penanggulangan Bencana Daerah", "Kesbangpol", "RSUD Ahmad Ripin", "RSUD Sungai Gelam", "RSUD Sungai Bahar", "Kecamatan Sekernan", "Kecamatan Jaluko", "Kecamatan Maro Sebo", "Kecamatan Kumpeh", "Kecamatan Kumpeh Ulu", "Kecamatan Mestong", "Kecamatan Sungai Gelam", "Kecamatan Sungai Bahar", "Kecamatan Bahar Utara", "Kecamatan Bahar Selatan", "Kecamatan Taman Rajo"]
opsi_opd = st.selectbox("Pilih Unit Kerja / OPD:", [""] + sorted(list_opd) + ["Lainnya"])
unit_kerja_final = st.text_input("Ketik Nama OPD (Jika Lainnya):") if opsi_opd == "Lainnya" else opsi_opd

st.write("---")

st.subheader("II. Data Admin")
status_pegawai = st.radio("Status Pegawai:", ["PNS", "PPPK"], horizontal=True)

c1, c2 = st.columns(2)
with c1:
    nama_admin = st.text_input("Nama Lengkap")
    nip_admin = st.text_input(f"NIP / NI {status_pegawai}", max_chars=18, placeholder="18 Digit Angka")
    no_hp = st.text_input("Nomor WhatsApp")
with c2:
    pangkat_admin = st.text_input("Pangkat / Golongan")
    jabatan_admin = st.text_input("Jabatan")
    email = st.text_input("Email", placeholder="harus @gmail.com")

st.write("---")

st.subheader("III. Data Atasan")
n_atasan = st.text_input("Nama Lengkap Atasan")
j_atasan = st.text_input("Jabatan Atasan")

c3, c4 = st.columns(2)
with c3:
    p_atasan = st.text_input("Pangkat / Golongan Atasan")
with c4:
    nip_atasan = st.text_input("NIP Atasan", max_chars=18)

st.write("---")

st.subheader("IV. Tanda Tangan Atasan")
canvas_result = st_canvas(
    stroke_width=3, stroke_color="#000000", background_color="#ffffff",
    height=150, width=350, drawing_mode="freedraw", key="canvas_final", display_toolbar=True
)

st.write("")
if st.button("KIRIM DATA SEKARANG", type="primary", use_container_width=True):
    val_nip = nip_admin.isdigit() and len(nip_admin) == 18 and nip_atasan.isdigit() and len(nip_atasan) == 18
    val_email = email.lower().endswith("@gmail.com")

    if not val_nip:
        st.error("❌ NIP Admin dan Atasan harus 18 digit angka!")
    elif not val_email:
        st.error("❌ Email wajib menggunakan domain @gmail.com!")
    elif not nama_admin or not unit_kerja_final or not n_atasan:
        st.warning("⚠️ Mohon lengkapi semua field!")
    else:
        with st.spinner('Memproses data...'):
            ttd_b64 = get_base64_signature(canvas_result.image_data)
            
            if sheets_service:
                try:
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row = [[now, perihal_final, unit_kerja_final, f"({status_pegawai}) {nama_admin}", f"'{nip_admin}", email, n_atasan, j_atasan, p_atasan, f"'{nip_atasan}", ttd_b64]]
                    sheets_service.spreadsheets().values().append(
                        spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                        valueInputOption="USER_ENTERED", body={'values': row}
                    ).execute()
                except Exception as e:
                    st.error(f"Gagal Sheets: {e}")

            data_spt = {
                'unit_kerja': unit_kerja_final, 'nama': nama_admin, 'nip': nip_admin,
                'pangkat': pangkat_admin, 'jabatan': jabatan_admin, 'no_hp': no_hp,
                'email': email, 'j_atasan': j_atasan, 'n_atasan': n_atasan,
                'nip_atasan': nip_atasan, 'p_atasan': p_atasan
            }
            docx_file = create_docx_final(data_spt, canvas_result.image_data)
            
            if docx_file:
                st.success("✅ Data berhasil terkirim!")
                st.download_button("📥 Download SPT", docx_file, f"SPT_{nama_admin.replace(' ','_')}.docx", use_container_width=True)

# --- 6. FOOTER ---
st.write("---")
st.markdown(
    """
    <div class="footer-box" style='text-align: center;'>
        <p style='margin: 0; color: white;'>Made with Love ❤️ oleh</p>
        <p style='margin: 0; font-weight: bold; color: white;'>Tim Bagian Organisasi Setda Kab. Muaro Jambi</p>
        <p style='margin: 5px 0 0 0; font-weight: bold; color: #D9E021;'>#SlavaUkraini 🇺🇦</p>
    </div>
    """, 
    unsafe_allow_html=True
)
