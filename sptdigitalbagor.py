import streamlit as st
from streamlit_drawable_canvas import st_canvas
from streamlit_gsheets import GSheetsConnection
from PIL import Image
import pandas as pd
import datetime

st.set_page_config(page_title="Form SPT Admin OPD", layout="centered")

# --- KONEKSI KE GOOGLE SHEETS ---
# Di Streamlit Cloud, masukkan URL Spreadsheet di Secrets (langkah ada di bawah)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- HEADER ---
st.title("Form Surat Perintah Tugas")
st.markdown("""
**Formulir ini digunakan untuk mendata petugas yang ditunjuk sebagai Admin OPD...**
*(Deskripsi sesuai permintaan Anda)*
""")

# --- LIST OPD ---
list_opd = ["Bagian Tata Pemerintahan", "Bagian Kesejahteraan Rakyat", "Dinas Kesehatan", "Kecamatan Kumpeh"] # Tambahkan list lengkap Anda di sini

with st.form("spt_form"):
    st.header("I. Data Admin OPD")
    opd = st.selectbox("Pilih OPD", [""] + list_opd)
    nama = st.text_input("Nama Lengkap dan Gelar")
    nip = st.text_input("NIP (Angka saja)")
    pangkat = st.text_input("Pangkat / Golongan")
    jabatan = st.text_input("Jabatan")
    no_hp = st.text_input("Nomor Handphone")
    email = st.text_input("Email")

    st.header("II. Data Atasan Langsung")
    nama_atasan = st.text_input("Nama Atasan Lengkap")
    nip_atasan = st.text_input("NIP Atasan")
    pangkat_atasan = st.text_input("Pangkat Golongan Atasan")
    jabatan_atasan = st.text_input("Jabatan Atasan")

    st.header("III. Tanda Tangan")
    canvas_result = st_canvas(stroke_width=3, stroke_color="#000", background_color="#eee", height=150, width=500, key="canvas")

    submit = st.form_submit_button("Kirim Data")

if submit:
    if not nip.isdigit() or not nip_atasan.isdigit():
        st.error("NIP harus berupa angka!")
    elif "" in [opd, nama, nip, nama_atasan]:
        st.warning("Mohon lengkapi semua data wajib.")
    else:
        # Menyiapkan baris data baru
        new_row = pd.DataFrame([{
            "Tanggal": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "OPD": opd,
            "Nama": nama,
            "NIP": nip,
            "Pangkat": pangkat,
            "Jabatan": jabatan,
            "No_HP": no_hp,
            "Email": email,
            "Nama_Atasan": nama_atasan,
            "NIP_Atasan": nip_atasan,
            "Pangkat_Atasan": pangkat_atasan,
            "Jabatan_Atasan": jabatan_atasan
        }])

        # MENGIRIM KE GOOGLE SHEETS
        try:
            existing_data = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798/edit?usp=sharing")
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(spreadsheet="https://docs.google.com/spreadsheets/d/1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798/edit?usp=sharing", data=updated_df)
            st.success("Data Berhasil Terkirim ke Spreadsheet!")
        except Exception as e:
            st.error(f"Gagal kirim ke Sheets: {e}")
