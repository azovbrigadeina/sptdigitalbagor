# Daftar Hadir Kegiatan & Rekap Kehadiran OPD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membangun fitur konfirmasi presensi kegiatan mandiri (`presensi.html`) berbasis verifikasi SPT dan NIP, serta sub-tab monitoring di Dashboard Admin untuk merekap daftar OPD yang belum/sudah hadir beserta fitur ekspor/cetak.

**Architecture:** 
- Web mandiri `presensi.html` (dibangun dari `apps_script/Presensi.html` melalui `build.js`) terhubung langsung ke Cloud Firestore.
- Validasi kehadiran secara instan memeriksa koleksi `submissions` berdasarkan `perihal` dan `nip`.
- Presensi sah dicatat secara idempoten di koleksi baru `presensi_kegiatan` dengan ID `{kegiatanSlug}_{nip}`.
- Dashboard Admin (`apps_script/Index.html` -> `public/index.html`) dilengkapi sub-tab baru `kehadiran-panel` yang membandingkan daftar master OPD SI-PRABU (`sianjabUnits`) dengan data `presensi_kegiatan`.

**Tech Stack:** 
- Vanilla JavaScript (ES6+), HTML5, Tailwind CSS CDN
- Firebase SDK v10 (Firestore compat)
- Node.js build script (`build.js`)

## Global Constraints
- Tema desain konsisten dengan palet Ukraine Theme / Modern Official (`#0057B7` Biru Utama, `#FFD700` Kuning Aksen, `#0F172A` Slate).
- Wajib kompatibel dengan alur build `build.js` dan deployment Firebase Hosting (`npm run build`).
- Wajib menerapkan sanitasi HTML (`escapeHtml`) pada seluruh rendering dinamis untuk mencegah XSS.

---

### Task 1: Pipeline Build untuk `presensi.html`

**Files:**
- Modify: `build.js`
- Create: `apps_script/Presensi.html` (skaleton awal)

**Interfaces:**
- Produces: `public/presensi.html` yang terinjeksi script Firebase SDK dan Firestore initialization.

- [ ] **Step 1: Modifikasi `build.js` agar memproses `Presensi.html`**
Tambahkan target build untuk `apps_script/Presensi.html` -> `public/presensi.html` dengan injeksi `firebaseSnippet`.

- [ ] **Step 2: Jalankan build untuk verifikasi**
Run: `node build.js`
Expected: File `public/presensi.html` terbentuk dengan ukuran valid dan berisi konfigurasi Firebase.

- [ ] **Step 3: Commit**
```bash
git add build.js apps_script/Presensi.html
git commit -m "chore: setup build pipeline for presensi.html"
```

---

### Task 2: Halaman Antarmuka Publik Presensi Mandiri (`apps_script/Presensi.html`)

**Files:**
- Modify: `apps_script/Presensi.html`
- Modify: `build.js` (jika ada token/placeholder tambahan)

**Interfaces:**
- Consumes: Firestore collection `config_kegiatan`, `submissions`
- Produces: Firestore collection `presensi_kegiatan` (docId: `{kegiatanSlug}_{nip}`)

- [ ] **Step 1: Rancang layout UI responsif mobile-first di `apps_script/Presensi.html`**
Header dengan logo, dropdown pilihan kegiatan (memuat realtime dari `config_kegiatan`), input NIP numerik 18 digit, dan tombol `Konfirmasi Hadir`.

- [ ] **Step 2: Implementasikan logika validasi NIP & SPT**
Kueri `submissions` where `perihal == selectedKegiatan` and `nip == inputNip`.
Jika ditemukan:
  - Cek `presensi_kegiatan.doc(docId)`.
  - Jika belum ada, `set()` data presensi baru.
  - Tampilkan kartu bukti kehadiran hijau (Nama, NIP, OPD, Jabatan, Nomor SPT, Waktu Hadir).
  - Jika sudah ada, tampilkan kartu info biru (sudah check-in sebelumnya).
Jika tidak ditemukan:
  - Tampilkan kartu penolakan amber/merah dengan tombol tautan CTA "📝 Isi Formulir SPT Sekarang" ke `index.html`.

- [ ] **Step 3: Build & Uji render `public/presensi.html`**
Run: `node build.js`
Expected: Build sukses tanpa error sintaks.

- [ ] **Step 4: Commit**
```bash
git add apps_script/Presensi.html public/presensi.html
git commit -m "feat: implement standalone presensi.html with SPT validation"
```

---

### Task 3: Sub-Tab Rekap Kehadiran di Dashboard Admin (`apps_script/Index.html`)

**Files:**
- Modify: `apps_script/Index.html`
- Modify: `public/index.html` (via build)

**Interfaces:**
- Consumes: `sianjabUnits` (Master OPD SI-PRABU), Firestore `presensi_kegiatan`, `config_kegiatan`
- Produces: UI `kehadiran-panel`, metrik kehadiran OPD, tabel OPD belum hadir, tabel peserta hadir.

- [ ] **Step 1: Tambahkan tombol sub-tab dan kontainer `kehadiran-panel`**
Tambahkan tab pill `📋 Rekap Kehadiran` (`btn-kehadiran-panel`) di switcher admin panel dan perbarui fungsi `switchAdminTab()`.

- [ ] **Step 2: Buat komponen Filter & Metrik Statistik Ringkasan**
Dropdown pilihan kegiatan presensi, 5 kartu metrik: Total OPD Utama, OPD Hadir, OPD Belum Hadir, % Kehadiran, Total Peserta.

- [ ] **Step 3: Buat Panel Pemantauan OPD Belum Hadir**
Bandingkan master OPD SI-PRABU (`sianjabUnits` kategori Unit Kerja Utama) dengan daftar OPD di `presensi_kegiatan`.
Tampilkan OPD yang belum hadir dengan kartu merah/amber, lengkapi dengan tombol "📋 Salin Daftar Absen (WhatsApp)".

- [ ] **Step 4: Buat Tabel Rincian Peserta Hadir & Fitur Ekspor/Cetak**
Tabel interaktif dengan pencarian cepat nama/NIP/OPD, tombol "🖨️ Cetak Lembar Hadir" (CSS `@media print`), dan tombol "📥 Ekspor CSV/Excel".

- [ ] **Step 5: Hubungkan tombol navigasi Presensi di header/footer `apps_script/Index.html`**
Tambahkan tombol pintas di navigasi utama atau floating banner yang mengarah ke `presensi.html`.

- [ ] **Step 6: Build & Verifikasi**
Run: `npm run build`
Expected: Build berhasil dan `public/index.html` terbarui.

- [ ] **Step 7: Commit**
```bash
git add apps_script/Index.html public/index.html
git commit -m "feat: add admin attendance recap panel with absent OPD summary"
```

---

### Task 4: Verifikasi Menyeluruh & Testing Alur End-to-End

**Files:**
- Create: `test-attendance.js` (skrip uji simulasi logika validasi dan komparasi OPD)

- [ ] **Step 1: Buat skrip verifikasi otomatis `test-attendance.js`**
Uji:
1. Validasi pembuatan ID unik presensi (`kegiatanSlug_nip`).
2. Logika pencocokan OPD yang belum hadir vs master SI-PRABU.
3. Sanitasi teks ekspor CSV dan format WhatsApp generator.

- [ ] **Step 2: Jalankan skrip verifikasi**
Run: `node test-attendance.js`
Expected: Seluruh uji assertion bernilai PASS (100%).

- [ ] **Step 3: Cleanup skrip uji temporary & Final Build**
Run: `npm run build`
Expected: Build sukses, git tree bersih.

- [ ] **Step 4: Commit**
```bash
git add test-attendance.js
git commit -m "test: add verification tests for attendance logic"
```
