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

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Kirim Surat Tugas", layout="wide", page_icon="📝")

# --- 2. KONEKSI GOOGLE SHEETS ---
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

# --- 2B. FUNGSI DATABASE (KEGIATAN & SUBMISI) ---
def get_kegiatan_list():
    if not sheets_service:
        return [
            {"nama": "SPT Rekon TPP dan SIMONA", "integrasi": "SITPP", "status": "Aktif"},
            {"nama": "Lainnya", "integrasi": "None", "status": "Aktif"}
        ]
    try:
        meta = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = [s['properties']['title'] for s in meta['sheets']]
        
        if "Config_Kegiatan" not in sheets:
            # Buat sheet baru
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': 'Config_Kegiatan'
                        }
                    }
                }]
            }
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
            
            # Tulis data default
            default_rows = [
                ["Nama Kegiatan", "Integrasi", "Status"],
                ["SPT Rekon TPP dan SIMONA", "SITPP", "Aktif"],
                ["Lainnya", "None", "Aktif"]
            ]
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range="Config_Kegiatan!A1",
                valueInputOption="USER_ENTERED",
                body={'values': default_rows}
            ).execute()
            return [
                {"nama": "SPT Rekon TPP dan SIMONA", "integrasi": "SITPP", "status": "Aktif"},
                {"nama": "Lainnya", "integrasi": "None", "status": "Aktif"}
            ]
        
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Config_Kegiatan!A2:C100"
        ).execute()
        rows = result.get('values', [])
        if not rows:
            return []
        
        kegiatan = []
        for r in rows:
            if len(r) >= 1:
                kegiatan.append({
                    "nama": r[0],
                    "integrasi": r[1] if len(r) > 1 else "None",
                    "status": r[2] if len(r) > 2 else "Aktif"
                })
        return kegiatan
    except Exception as e:
        return [
            {"nama": "SPT Rekon TPP dan SIMONA", "integrasi": "SITPP", "status": "Aktif"},
            {"nama": "Lainnya", "integrasi": "None", "status": "Aktif"}
        ]

def save_kegiatan_list(kegiatan_list):
    if not sheets_service:
        return False
    try:
        rows = [["Nama Kegiatan", "Integrasi", "Status"]]
        for k in kegiatan_list:
            rows.append([k["nama"], k["integrasi"], k["status"]])
        
        # Bersihkan data lama
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range="Config_Kegiatan!A1:C100"
        ).execute()
        
        # Tulis data baru
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="Config_Kegiatan!A1",
            valueInputOption="USER_ENTERED",
            body={'values': rows}
        ).execute()
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan konfigurasi kegiatan: {e}")
        return False

def get_submissions_data():
    if not sheets_service:
        return []
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A1:M1000"
        ).execute()
        return result.get('values', [])
    except Exception as e:
        return []


# --- 3. FUNGSI KONVERSI TTD KE BASE64 (Untuk Spreadsheet) ---
def get_base64_signature(signature_img):
    try:
        if signature_img is not None and signature_img.any():
            img_rgba = Image.fromarray(signature_img.astype('uint8'), 'RGBA')
            # Tambahkan background putih agar tidak transparan di Base64
            white_bg = Image.new("RGBA", img_rgba.size, (255, 255, 255, 255))
            final_img = Image.alpha_composite(white_bg, img_rgba).convert("RGB")
            
            buffered = BytesIO()
            final_img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        return "Tidak ada TTD"
    except:
        return "Error TTD"

# --- 4. FUNGSI GENERATE DOCX (Untuk Download) ---
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
            '{{perihal}}': str(data['perihal']),
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

# --- 5. TAMPILAN OPERATOR FORM ---
def show_operator_form():
    # TAMBAHAN: FUNGSI MODAL YANG LEBIH STABIL
    @st.dialog("PENGUMUMAN PENTING")
    def tampilkan_pengumuman():
        st.warning("⚠️ **Batas Pengiriman SPT:**")
        st.markdown("Pengiriman SPT sampai **Tanggal 6 Februari 2026**.")
        st.info("💡 **Informasi:**\n\nTidak perlu menyerahkan SPT Fisik ke Bagian Organisasi.")
        if st.button("Saya Mengerti", type="primary", use_container_width=True):
            st.session_state["sudah_baca_info"] = True
            st.rerun()

    # Logika agar hanya muncul satu kali saat aplikasi pertama kali dimuat
    if "sudah_baca_info" not in st.session_state:
        tampilkan_pengumuman()
    st.markdown("<h2 style='text-align: center;'>📝 Kirim Surat Tugas</h2>", unsafe_allow_html=True)
    st.write("---")

    # SEKSI I: PERIHAL & OPD
    st.subheader("I. Perihal & Unit Kerja")
    
    kegiatan_list = get_kegiatan_list()
    nama_kegiatan_active = [k["nama"] for k in kegiatan_list if k["status"] == "Aktif"]
    if not nama_kegiatan_active:
        nama_kegiatan_active = ["Lainnya"]
    elif "Lainnya" not in nama_kegiatan_active:
        nama_kegiatan_active.append("Lainnya")
        
    opsi_perihal = st.selectbox("Pilih Perihal / Kegiatan:", nama_kegiatan_active)
    perihal_final = st.text_input("Ketik Perihal Manual (Jika Lainnya):") if opsi_perihal == "Lainnya" else opsi_perihal
    
    selected_kegiatan = next((k for k in kegiatan_list if k["nama"] == opsi_perihal), None)
    integrasi_val = selected_kegiatan["integrasi"] if selected_kegiatan else "None"
    if opsi_perihal == "Lainnya":
        integrasi_val = "None"
        
    current_year_int = datetime.datetime.now().year
    target_tahun = st.selectbox("Tahun Kegiatan:", [str(y) for y in range(current_year_int - 1, current_year_int + 5)], index=1)

    list_opd = [
        "Bagian Tata Pemerintahan", "Bagian Kesejahteraan Rakyat", "Bagian Hukum", "Bagian Kerjasama", "Bagian Perekonomian", "Bagian Pembangunan dan Sumber Daya Alam", "Bagian Pengadaan Barang dan Jasa", "Bagian Umum", "Bagian Organisasi", "Bagian Protokol dan Komunikasi Pimpinan", "Bagian Perencanaan dan Keuangan", "Sekretariat DPRD", "Inspektorat Daerah",
        "Dinas Pendidikan dan Kebudayaan", "Dinas Kesehatan", "Dinas Pekerjaan Umum dan Penataan Ruang",
        "Dinas Perumahan dan Kawasan Permukiman", "Satuan Polisi Pamong Praja", "Dinas Pemadam Kebakaran dan Penyelamatan",
        "Dinas Sosial, Pemberdayaan Perempuan dan Perlindungan Anak", "Dinas Lingkungan Hidup",
        "Dinas Kependudukan dan Pencatatan Sipil", "Dinas Pemberdayaan Masyarakat dan Desa",
        "Dinas Perhubungan", "Dinas Komunikasi dan Informatika", "Dinas Koperasi, Perindustrian dan Perdagangan",
        "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu", "Dinas Pariwisata, Pemuda dan Olahraga",
        "Dinas Perpustakaan dan Arsip Daerah", "Dinas Perikanan", "Dinas Ketahanan Pangan",
        "Dinas Tanaman Pangan dan Hortikultura", "Dinas Perkebunan dan Peternakan",
        "Dinas Tenaga Kerja dan Transmigrasi", "Dinas Pengendalian Penduduk dan Keluarga Berencana",
        "Badan Perencanaan Pembanguan Dan Riset Inovasi Daerah", "Badan Pengelola Keuangan dan Aset Daerah", 
        "Badan Pengelola Pajak dan Retribusi Daerah", "Badan Kepegawaian dan Pengembangan Sumber Daya Manusia ", 
        "Badan Penanggulangan Bencana Daerah", "Kesbangpol",
        "RSUD Ahmad Ripin", "RSUD Sungai Gelam", "RSUD Sungai Bahar",
        "Kecamatan Sekernan", "Kecamatan Jaluko", "Kecamatan Maro Sebo", "Kecamatan Kumpeh",
        "Kecamatan Kumpeh Ulu", "Kecamatan Mestong", "Kecamatan Sungai Gelam", "Kecamatan Sungai Bahar",
        "Kecamatan Bahar Utara", "Kecamatan Bahar Selatan", "Kecamatan Taman Rajo", "Puskesmas Penyengat Olak", "Puskesmas Kemingking Dalam", "Puskesmas Puding", "Puskesmas Sungai Bahar IV", "Puskesmas Simpang Sungai Duren", "Puskesmas Tempino", "Puskesmas Tanjung", "Puskesmas Bahar VII", "Puskesmas Tantan", "Puskesmas Kasang Pudak", "Puskesmas Sengeti", "Puskesmas Pir II Bajubang", "Puskesmas Pondok Meja", "Puskesmas Markanding", "Puskesmas Tangkit", "Puskesmas Talang Bukit", "Puskesmas Sekernan Ilir", "Puskesmas Jambi Kecil", "Puskesmas Muara Kumpeh", "Puskesmas Sungai Bahar I", "Puskesmas Kebon IX", "Puskesmas Suko Awin", "Puskesmas Petaling Jaya"
    ]
    opsi_opd = st.selectbox("Pilih Unit Kerja / OPD:", [""] + sorted(list_opd) + ["Lainnya"])
    unit_kerja_final = st.text_input("Ketik Nama OPD (Jika Lainnya):") if opsi_opd == "Lainnya" else opsi_opd

    st.write("---")

    # SEKSI II: DATA ADMIN
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

    # SEKSI III: DATA ATASAN
    st.subheader("III. Data Atasan")
    n_atasan = st.text_input("Nama Lengkap Atasan")
    j_atasan = st.text_input("Jabatan Atasan (Contoh: Kepala Bagian Organisasi)")

    c3, c4 = st.columns(2)
    with c3:
        p_atasan = st.text_input("Pangkat / Golongan Atasan")
    with c4:
        nip_atasan = st.text_input("NIP Atasan", max_chars=18)
        st.info(f"Tanggal Surat: {datetime.datetime.now().strftime('%d %B %Y')}")

    st.write("---")

    # SEKSI IV: TANDA TANGAN
    st.subheader("IV. Tanda Tangan Atasan")

    canvas_result = st_canvas(
        stroke_width=3, 
        stroke_color="#000000", 
        background_color="#ffffff",
        height=150, 
        width=350, 
        drawing_mode="freedraw", 
        key="canvas_final",
        display_toolbar=True
    )

    st.markdown("""
        <p style='color: #ff4b4b; font-size: 0.85rem; font-weight: bold; margin-top: -10px;'>
            ⚠️ Pastikan kolom di atas ditandatangani oleh Atasan yang bersangkutan! (Contoh: kepala dinas/badan)
        </p>
        """, unsafe_allow_html=True)

    st.write("")
    if st.button("KIRIM DATA", type="primary", use_container_width=True):
        val_nip = nip_admin.isdigit() and len(nip_admin) == 18 and nip_atasan.isdigit() and len(nip_atasan) == 18
        val_email = email.lower().endswith("@gmail.com")

        if not val_nip:
            st.error("❌ NIP Admin dan Atasan harus 18 digit angka!")
        elif not val_email:
            st.error("❌ Email wajib menggunakan domain @gmail.com!")
        elif not nama_admin or not unit_kerja_final or not n_atasan:
            st.warning("⚠️ Mohon lengkapi semua field yang tersedia!")
        else:
            with st.spinner('Memproses data...'):
                ttd_b64 = get_base64_signature(canvas_result.image_data)
                
            if sheets_service:
                try:
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    row = [[
                        now,                    # Kolom A: Waktu
                        perihal_final,          # Kolom B: Perihal
                        unit_kerja_final,       # Kolom C: Unit Kerja
                        f"({status_pegawai}) {nama_admin}", # Kolom D: Nama Admin
                        f"'{nip_admin}",        # Kolom E: NIP Admin
                        email,                  # Kolom F: Email
                        n_atasan,               # Kolom G: Nama Atasan
                        j_atasan,               # Kolom H: Jabatan Atasan
                        p_atasan,               # Kolom I: Pangkat Atasan
                        f"'{nip_atasan}",       # Kolom J: NIP Atasan
                        ttd_b64,                # Kolom K: Base64 TTD
                        integrasi_val,          # Kolom L: Integrasi
                        str(target_tahun)       # Kolom M: Tahun
                    ]]
                    
                    sheets_service.spreadsheets().values().append(
                        spreadsheetId=SPREADSHEET_ID, 
                        range="Sheet1!A1",
                        valueInputOption="USER_ENTERED", 
                        body={'values': row}
                    ).execute()
                    
                except Exception as e:
                    st.error(f"Gagal kirim ke Sheets: {e}")

                data_spt = {
                    'unit_kerja': unit_kerja_final, 'nama': nama_admin, 'nip': nip_admin,
                    'pangkat': pangkat_admin, 'jabatan': jabatan_admin, 'no_hp': no_hp,
                    'email': email, 'j_atasan': j_atasan, 'n_atasan': n_atasan,
                    'nip_atasan': nip_atasan, 'p_atasan': p_atasan, 'perihal': perihal_final
                }
                docx_file = create_docx_final(data_spt, canvas_result.image_data)
                
                if docx_file:
                    st.success("✅ Data berhasil masuk, Terima Kasih")
                    st.download_button("📥 Download SPT Sekarang", docx_file, f"SPT_{nama_admin.replace(' ','_')}.docx", use_container_width=True)

# --- 5B. TAMPILAN ADMIN DASHBOARD ---
def show_admin_page():
    st.markdown("<h2 style='text-align: center;'>🔒 Panel Admin SPT Digital</h2>", unsafe_allow_html=True)
    st.write("---")
    
    correct_password = st.secrets.get("admin_password", "adminbagor123")
    
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False
        
    if not st.session_state["admin_authenticated"]:
        passwd = st.text_input("Masukkan Password Admin:", type="password")
        if st.button("LOG IN", type="primary", use_container_width=True):
            if passwd == correct_password:
                st.session_state["admin_authenticated"] = True
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Password salah!")
        return

    if st.sidebar.button("Log Out Admin"):
        st.session_state["admin_authenticated"] = False
        st.rerun()
        
    tab1, tab2 = st.tabs(["📊 Dashboard & Data Submisi", "⚙️ Pengaturan Kegiatan (Perihal)"])
    
    with tab1:
        with st.spinner("Memuat data dari Google Sheets..."):
            rows = get_submissions_data()
        
        if not rows or len(rows) <= 1:
            st.info("Belum ada data submisi SPT.")
        else:
            headers = rows[0]
            data_rows = rows[1:]
            
            import pandas as pd
            
            max_cols = max(len(headers), max(len(r) for r in data_rows) if data_rows else 0)
            
            padded_headers = list(headers)
            while len(padded_headers) < max_cols:
                padded_headers.append(f"Kolom_{len(padded_headers)+1}")
            
            padded_data = []
            for r in data_rows:
                padded_r = r + [""] * (max_cols - len(r))
                padded_data.append(padded_r)
                
            df = pd.DataFrame(padded_data, columns=padded_headers)
            
            column_mapping = {}
            if len(df.columns) > 0: column_mapping[df.columns[0]] = "Waktu"
            if len(df.columns) > 1: column_mapping[df.columns[1]] = "Perihal"
            if len(df.columns) > 2: column_mapping[df.columns[2]] = "Unit Kerja"
            if len(df.columns) > 3: column_mapping[df.columns[3]] = "Nama Admin"
            if len(df.columns) > 4: column_mapping[df.columns[4]] = "NIP Admin"
            if len(df.columns) > 5: column_mapping[df.columns[5]] = "Email"
            
            df.rename(columns=column_mapping, inplace=True)
            
            if "Integrasi" not in df.columns:
                if len(df.columns) > 11:
                    df.rename(columns={df.columns[11]: "Integrasi"}, inplace=True)
                else:
                    df["Integrasi"] = "None"
            if "Tahun" not in df.columns:
                if len(df.columns) > 12:
                    df.rename(columns={df.columns[12]: "Tahun"}, inplace=True)
                else:
                    def get_year_from_time(t):
                        try:
                            return str(t).split("-")[0].strip()
                        except:
                            return str(datetime.datetime.now().year)
                    df["Tahun"] = df["Waktu"].apply(get_year_from_time)
            
            df["Tahun"] = df["Tahun"].apply(lambda x: str(x).strip() if x else str(datetime.datetime.now().year))
            df["Integrasi"] = df["Integrasi"].apply(lambda x: str(x).strip() if x else "None")
            
            available_years = sorted(list(df["Tahun"].unique()))
            if not available_years:
                available_years = [str(datetime.datetime.now().year)]
                
            selected_year = st.selectbox("Pilih Tahun Kegiatan:", available_years, index=len(available_years)-1)
            
            df_filtered = df[df["Tahun"] == selected_year]
            
            c1, c2, c3 = st.columns(3)
            total_spt = len(df_filtered)
            sitpp_spt = len(df_filtered[df_filtered["Integrasi"] == "SITPP"])
            other_spt = total_spt - sitpp_spt
            
            with c1:
                st.metric("Total SPT Dikirim", total_spt)
            with c2:
                st.metric("Integrasi SiTPP", sitpp_spt)
            with c3:
                st.metric("SPT Lainnya / Tanpa Integrasi", other_spt)
                
            st.write("---")
            
            if total_spt > 0:
                col_chart1, col_chart2 = st.columns(2)
                
                opd_counts = df_filtered["Unit Kerja"].value_counts().reset_index()
                opd_counts.columns = ["Unit Kerja", "Jumlah"]
                
                keg_counts = df_filtered["Perihal"].value_counts().reset_index()
                keg_counts.columns = ["Kegiatan", "Jumlah"]
                
                with col_chart1:
                    st.subheader("Distribusi SPT per Unit Kerja / OPD")
                    st.bar_chart(opd_counts.set_index("Unit Kerja"))
                with col_chart2:
                    st.subheader("Distribusi SPT berdasarkan Kegiatan")
                    st.bar_chart(keg_counts.set_index("Kegiatan"))
                    
            st.write("---")
            
            st.subheader("Detail Data Submisi SPT")
            search_query = st.text_input("Cari berdasarkan Nama, NIP, OPD, atau Email:")
            
            if search_query:
                q = search_query.lower()
                df_display = df_filtered[
                    df_filtered["Nama Admin"].astype(str).str.lower().str.contains(q) |
                    df_filtered["NIP Admin"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Unit Kerja"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Email"].astype(str).str.lower().str.contains(q)
                ]
            else:
                df_display = df_filtered
                
            preview_cols = [c for c in df_display.columns if c not in ["Base64 TTD", "ttd_b64", "ttd"]]
            
            st.dataframe(df_display[preview_cols], use_container_width=True)
            
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Data Rekap (CSV)",
                data=csv,
                file_name=f"Rekap_SPT_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
    with tab2:
        st.subheader("Manajemen Daftar Kegiatan / Perihal")
        kegiatan_list = get_kegiatan_list()
        
        with st.form("tambah_kegiatan_form"):
            st.write("**Tambah Kegiatan Baru**")
            nama_baru = st.text_input("Nama Kegiatan (Contoh: Rekon TPP)")
            integrasi_baru = st.selectbox("Target Integrasi:", ["None", "SITPP", "Lainnya"])
            kustom_integrasi = st.text_input("Nama Integrasi Kustom (Jika memilih Lainnya):")
            
            submit_keg = st.form_submit_button("Tambah Kegiatan", type="primary")
            if submit_keg:
                if not nama_baru.strip():
                    st.error("Nama kegiatan tidak boleh kosong!")
                else:
                    final_integrasi = kustom_integrasi.strip() if integrasi_baru == "Lainnya" else integrasi_baru
                    new_item = {"nama": nama_baru.strip(), "integrasi": final_integrasi, "status": "Aktif"}
                    kegiatan_list.append(new_item)
                    if save_kegiatan_list(kegiatan_list):
                        st.success(f"Kegiatan '{nama_baru}' berhasil ditambahkan!")
                        st.rerun()
                        
        st.write("---")
        st.write("**Daftar Kegiatan Aktif**")
        
        if not kegiatan_list:
            st.info("Belum ada kegiatan terdaftar.")
        else:
            for idx, k in enumerate(kegiatan_list):
                col_name, col_int, col_status, col_action = st.columns([4, 2, 2, 2])
                with col_name:
                    st.write(f"**{k['nama']}**")
                with col_int:
                    st.code(k["integrasi"])
                with col_status:
                    st.write(k["status"])
                with col_action:
                    if st.button("Hapus", key=f"del_{idx}", type="secondary"):
                        kegiatan_list.pop(idx)
                        if save_kegiatan_list(kegiatan_list):
                            st.success("Kegiatan berhasil dihapus!")
                            st.rerun()

# --- 6. NAVIGASI SIDEBAR ---
st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Pilih Halaman:", ["📝 Kirim SPT", "🔒 Halaman Admin"])

if menu == "📝 Kirim SPT":
    show_operator_form()
else:
    show_admin_page()

# --- 7. FOOTER ---
st.write("")
st.write("---")
st.markdown(
    """
    <div style='text-align: center; color: #808495; font-size: 0.9em;'>
        Made with Love ❤️ oleh <br>
        <strong>Tim Bagian Organisasi Setda Kab. Muaro Jambi #SlavaUkraini</strong>
    </div>
    """, 
    unsafe_allow_html=True
)

