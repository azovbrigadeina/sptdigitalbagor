# Spesifikasi Desain: Redesain UI/UX Mobile-Friendly & Nuansa Bendera Ukraina

Tanggal: 2026-10-02  
Aplikasi: Kirim Surat Perintah Tugas (SPT) Digital - Bagian Organisasi Setda Muaro Jambi  
File Target Utama: `apps_script/Index.html`

---

## 1. Latar Belakang & Tujuan
Aplikasi web berbasis Google Apps Script saat ini melayani input pengiriman SPT oleh operator OPD dan pengelolaan oleh Admin. Desain awal didominasi nuansa indigo dan dirancang lebih untuk desktop, sehingga elemen menu navigasi, kanvas tanda tangan, dan tabel admin kurang ramah jempol (*thumb-friendly*) di ponsel pintar.

Tujuan redesain:
1. Menghadirkan pengalaman mobile-first yang intuitif, cepat, dan nyaman digunakan di ponsel pintar.
2. Mengadopsi palet warna bertema **Bendera Ukraina** (Azure Blue & Sunflower Gold/Amber) yang melambangkan stabilitas, ketegasan, dan kejelasan administrasi publik dengan standar aksesibilitas WCAG AA/AAA.
3. Menyederhanakan penamaan tombol aksi, khususnya tombol submit menjadi ringkas: **"Kirim SPT"**.

---

## 2. Struktur Navigasi & Menu Mobile

### 2.1 Sticky Top App Bar
- **Komponen**: Latar belakang putih bersih berkaca (*backdrop-filter blur*), border bawah biru lembut (`#DBEAFE`).
- **Elemen Kiri**: Ikon dokumen beraksen Azure Blue (`#0057B7`) berpadu dengan teks judul "KIRIM SPT DIGITAL" dan subjudul instansi "Bagian Organisasi Kabupaten Muaro Jambi".
- **Elemen Kanan (Desktop)**: Tab pill desktop untuk berganti antara "Form Operator" dan "Panel Admin".
- **Elemen Kanan (Mobile)**: Indikator status ringkas / badge koneksi SI-PRABU.

### 2.2 Bottom Navigation Bar (Mobile Dock)
- **Breakpoint**: Muncul otomatis di layar ponsel (`< 768px`) dan terpasang melayang (*fixed bottom dock*) dengan padding aman (*safe-area-inset-bottom*).
- **Item Navigasi**:
  1. **Form SPT**: Ikon formulir pensil, label "Form SPT".
  2. **Panel Admin**: Ikon gembok/perisai, label "Panel Admin".
- **Visual Feedback**: Item aktif diberi warna Azure Blue (`#0057B7`) dengan dot/pill aksen emas (`#F59E0B`), dan efek transisi lembut.
- **Area Konten**: Diberikan offset `pb-28` pada container utama agar konten terbawah tidak pernah terpotong atau tertutup dok navigasi.

### 2.3 Segmented Control Sub-Tab Admin
- Di dalam Panel Admin, perpindahan antara **Submisi & Statistik** dan **Manajemen Kegiatan** diubah menjadi pill tab modern yang responsif penuh, nyaman ditekan satu tangan tanpa perlu navigasi bertingkat yang rumit.

---

## 3. Skema Warna & Aksesibilitas (Ukraine Flag Palette)

| Elemen UI | Warna Hex / Token | Fungsi & Keterangan |
| :--- | :--- | :--- |
| **Primary (Azure Blue)** | `#0057B7` | Header brand, tombol aksi utama, border fokus input, tab aktif. |
| **Primary Hover/Dark** | `#00438F` | Status hover dan pressed pada tombol utama. |
| **Accent (Sunflower Gold)** | `#F59E0B` / `#FFD700` | Badge status aktif, highlight metrik KPI, aksen tombol verifikasi. |
| **On Accent Text** | `#0F172A` | Teks di atas latar belakang emas/kuning untuk kontras tinggi (> 7:1 WCAG AAA). |
| **Surface Background** | `#F8FAFC` s.d. `#EFF6FF` | Latar belakang aplikasi lembut dan ramah mata. |
| **Card Surface** | `#FFFFFF` | Permukaan kartu formulir dengan bayangan lembut dan border `#DBEAFE`. |
| **Text Primary** | `#0F172A` | Teks utama dengan kontras maksimal. |
| **Text Muted** | `#475569` | Teks label sekunder, placeholder, dan deskripsi pembantu. |
| **Success / Verified** | `#059669` | Status verifikasi BSrE dan unduhan berhasil. |
| **Destructive** | `#DC2626` | Tombol hapus dan notifikasi error. |

---

## 4. Formulir Operator & Komponen Responsif

### 4.1 Touch Targets & Form Inputs
- Seluruh input teks, nomor HP, email, select dropdown, dan textarea memiliki tinggi sentuh minimal 48px (`py-3.5`).
- Font input berukuran minimal 16px (`text-base` di mobile) untuk mencegah *auto-zoom* yang mengganggu pada browser mobile (Safari iOS & Chrome Android).
- Tiap tahapan formulir (Unit Kerja, Profil Pengirim, Profil Atasan, Tanda Tangan) dilengkapi dengan penomoran badge bulat biru-emas yang elegan.

### 4.2 Kanvas Tanda Tangan Adaptif (Retina Ready)
- Ukuran kanvas tidak lagi di-*hardcode* `width="350"`.
- Kanvas menggunakan lebar relatif kontainer (100% max width) dengan kalkulasi `devicePixelRatio` otomatis via JavaScript agar goresan tanda tangan di layar sentuh ponsel tidak pecah atau bergerigi.
- Tombol aksi kanvas:
  - Tombol **Bersihkan**: Merah lembut transparan dengan border jelas.
  - Tombol **TTD Srikandi (BSrE)**: Hijau toska elegan dengan aksen validasi.

### 4.3 Tombol Kirim Form
- Menggunakan teks ringkas sesuai arahan user: **"Kirim SPT"**.
- Menggunakan tombol bersudut melengkung modern (`rounded-2xl`), warna primer Azure Blue (`#0057B7`), efek bayangan lembut, serta status loading/indikator saat proses pengiriman berlangsung.

---

## 5. Panel Admin & Data Submisi Mobile

### 5.1 KPI Cards Responsif
- Kartu statistik (PNS, PPPK, Total Pengirim, Total SPT) disusun dalam grid 2 kolom di mobile dan 4 kolom di desktop untuk memanfaatkan ruang secara optimal tanpa terpotong.

### 5.2 Responsive Table & Card View
- Pada layar desktop/tablet (`>= 768px`), data submisi ditampilkan dalam format tabel data lengkap.
- Pada layar ponsel (`< 768px`), data submisi otomatis disajikan dalam bentuk daftar kartu (*card view*) yang menyajikan informasi penting (Nama Pengirim, OPD, Perihal, Tanggal) beserta tombol aksi cepat (Download PDF & Hapus) yang ramah sentuhan tanpa perlu horizontal scrolling.

---

## 6. Rencana Pengujian & Verifikasi
1. **Verifikasi Responsivitas Layar**:
   - Uji tampilan pada viewport mobile (360px, 390px, 412px, 768px) dan desktop (> 1024px).
2. **Verifikasi Navigasi**:
   - Memastikan peralihan tab lewat Bottom Navigation Bar di mobile dan Top Tab di desktop berjalan sinkron.
   - Memastikan tidak ada konten bawah yang terhalang oleh dok navigasi.
3. **Verifikasi Kanvas Tanda Tangan**:
   - Menguji tanda tangan di layar sentuh pada kanvas responsif serta memastikan export data URI tanda tangan tetap valid saat dikirim ke Apps Script.
4. **Verifikasi Kontras Warna (A11y)**:
   - Memastikan seluruh teks dan kontrol tombol memenuhi rasio kontras warna standar WCAG AA (minimal 4.5:1).
