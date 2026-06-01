# 🚀 Panduan Setup & Deployment Google Apps Script (GAS)

Guna memastikan aplikasi berjalan **100% stabil, bebas crash, dan gratis selamanya**, seluruh aplikasi telah dimigrasikan ke Google Apps Script. 

Ikuti langkah-langkah di bawah ini untuk mengaktifkan aplikasi Anda:

---

## 📋 Langkah 1: Persiapkan Template Google Doc
Agar script dapat memasukkan data dan tanda tangan secara dinamis:
1. Upload file template Word Anda (`template spt simona.docx`) ke **Google Drive**.
2. Buka file tersebut di Google Drive, lalu klik **File** > **Simpan sebagai Google Dokumen** (Save as Google Docs).
3. Setelah terbuka sebagai Google Doc, salin **Dokumen ID** dari URL browser Anda:
   * URL format: `https://docs.google.com/document/d/DOKUMEN_ID_TEMPLAT_ANDA/edit`
   * Simpan ID ini.

---

## 📋 Langkah 2: Salin Kode ke Google Spreadsheet
1. Buka Google Spreadsheet database Anda (ID: `1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798`).
2. Klik menu **Ekstensi** > **Apps Script**.
3. Di dalam editor Apps Script:
   * Buat file script baru dan beri nama **`Code`** (salin seluruh isi dari file lokal [Code.js](file:///home/falcon/Documents/ProyekKirimSPTDigital/sptdigitalbagor/apps_script/Code.js)).
   * Edit baris nomor 8 di `Code.gs` dengan Dokumen ID dari **Langkah 1**:
     ```javascript
     var TEMPLATE_DOC_ID = "DOKUMEN_ID_TEMPLAT_ANDA";
     ```
   * Buat file HTML baru (klik ikon `+` di samping tulisan Files > pilih HTML), beri nama **`Index`**, lalu salin seluruh isi dari file lokal [Index.html](file:///home/falcon/Documents/ProyekKirimSPTDigital/sptdigitalbagor/apps_script/Index.html).
4. Klik tombol **Simpan** (ikon Floppy Disk).

---

## 📋 Langkah 3: Deploy sebagai Aplikasi Web (Web App)
1. Di kanan atas editor Apps Script, klik tombol **Terapkan (Deploy)** > **Penerapan Baru (New Deployment)**.
2. Klik ikon gir (Pilih jenis) > pilih **Aplikasi Web (Web App)**.
3. Konfigurasikan:
   * **Deskripsi**: `Versi 1.0`
   * **Jalankan sebagai (Execute as)**: `Saya` (akun Google Anda)
   * **Yang memiliki akses (Who has access)**: `Siapa saja` (Anyone)
4. Klik **Terapkan (Deploy)**.
5. Google akan meminta otorisasi akses. Klik **Berikan Akses** (Authorize access), lalu pilih akun Google Anda. Jika muncul peringatan keamanan, klik **Lanjutan (Advanced)** > **Buka Project (tidak aman)**, lalu klik **Izinkan (Allow)**.
6. Salin **URL Aplikasi Web (Web App URL)** yang diberikan. Selesai! Aplikasi Anda kini sudah online.

---

## ⚙️ Fitur yang Disediakan
1. **Form Operator (Kirim SPT)**:
   - Input profil admin & atasan.
   - Pilihan kegiatan dari database `Config_Kegiatan` Google Sheet.
   - **Canvas Tanda Tangan Atasan**: Tanda tangan langsung menggunakan jari (HP/tablet) atau mouse (PC).
   - Tombol kirim untuk menyimpan data ke Sheet & langsung mengunduh hasil dokumen dalam format Microsoft Word (.docx).
2. **Panel Admin (Dilindungi Password)**:
   - **Statistik & Progress**: Laporan real-time jumlah unit yang sudah melapor & belum melapor per kategori unit kerja.
   - **Data Submisi**: Cari, filter, dan hapus baris data langsung dari tabel rekap, serta ekspor rekap ke CSV.
   - **Manajemen Kegiatan**: Tambah, edit dasar hukum, dan hapus perihal kegiatan secara langsung.
