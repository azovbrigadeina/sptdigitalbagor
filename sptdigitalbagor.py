import streamlit as st
from streamlit_drawable_canvas import st_canvas
import datetime
from io import BytesIO
from PIL import Image
from docxtpl import DocxTemplate, InlineImage
from reportlab.lib.units import mm
import os

# --- 1. FUNGSI GENERATE (DIPERKUAT) ---
def create_docx_from_template(data, signature_img):
    template_name = "template spt simona.docx" 
    
    if not os.path.exists(template_name):
        st.error(f"File '{template_name}' tidak ditemukan!")
        return None

    try:
        doc = DocxTemplate(template_name)
        
        # PROSES Tanda Tangan
        img_obj = ""
        if signature_img is not None:
            # Pastikan folder temp ada
            if not os.path.exists("temp"):
                os.makedirs("temp")
            
            # Konversi ke RGB (Latar putih pekat)
            signature_img = signature_img.convert("RGBA")
            white_bg = Image.new("RGBA", signature_img.size, (255, 255, 255, 255))
            combined_img = Image.alpha_composite(white_bg, signature_img).convert("RGB")
            
            # SIMPAN FISIK (Gunakan nama unik agar tidak bentrok)
            path_ttd = os.path.join("temp", f"sig_{datetime.datetime.now().strftime('%H%M%S')}.png")
            combined_img.save(path_ttd)
            
            # Masukkan sebagai InlineImage
            img_obj = InlineImage(doc, path_ttd, width=45 * mm)

        # Mapping data (Sesuaikan persis dengan template word Anda)
        context = {
            'Unit_Kerja': data['unit_kerja'],
            'nama_admin': data['nama'],
            'pangkat_admin': data['pangkat'],
            'NIP_admin': data['nip'],
            'Jabatan_admin': data['jabatan'],
            'no_hpadmin': data['no_hp'],
            'email_admin': data['email'],
            'JABATAN_ATASAN': data['j_atasan'],
            'NAMA_ATASAN': data['n_atasan'],
            'NIP_ATASAN': data['nip_atasan'],
            'PANGKAT_GOL_ATASAN': data['p_atasan'],
            'Tanggal_Bulan_Tahun': datetime.datetime.now().strftime('%d %B %Y'),
            'ttd': img_obj 
        }

        doc.render(context)
        
        target_stream = BytesIO()
        doc.save(target_stream)
        target_stream.seek(0)
        
        return target_stream
    except Exception as e:
        st.error(f"Gagal memproses TTD: {e}")
        return None

# --- 2. TAMPILAN UI ---
st.title("📝 Form SPT Admin OPD")

with st.form("spt_form"):
    st.header("I. Data")
    opd = st.text_input("Nama OPD")
    nama = st.text_input("Nama Admin")
    nip = st.text_input("NIP Admin (18 Digit)", max_chars=18)
    
    st.header("II. Atasan")
    j_atasan = st.text_input("Jabatan Atasan")
    n_atasan = st.text_input("Nama Atasan")
    
    st.header("III. Tanda Tangan")
    st.write("Silakan tanda tangan di bawah:")
    canvas_result = st_canvas(
        stroke_width=3,
        stroke_color="#000000",
        background_color="#ffffff",
        height=150,
        width=300,
        drawing_mode="freedraw",
        key="canvas_signature"
    )

    submit = st.form_submit_button("Generate SPT")

# --- 3. EKSEKUSI ---
if submit:
    if canvas_result.image_data is not None:
        # Konversi canvas ke PIL Image
        raw_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        
        # Validasi sederhana apakah canvas kosong (opsional)
        # Kita anggap user sudah tanda tangan
        
        data_spt = {
            'unit_kerja': opd, 'nama': nama, 'nip': nip, 'pangkat': "", 
            'jabatan': "", 'no_hp': "", 'email': "", 'j_atasan': j_atasan, 
            'n_atasan': n_atasan, 'nip_atasan': "", 'p_atasan': ""
        }
        
        docx_res = create_docx_from_template(data_spt, raw_img)
        
        if docx_res:
            st.success("Berhasil! Klik tombol di bawah untuk download.")
            st.download_button("📥 Download File Word", docx_res, f"SPT_{nama}.docx")
