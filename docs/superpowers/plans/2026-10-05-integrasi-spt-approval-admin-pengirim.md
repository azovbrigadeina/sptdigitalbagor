# Integrasi SPT Digital ke SiTPP: Modul Approval & Antrean Verifikasi Operator

> **Untuk agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mengintegrasikan data pengirim dari aplikasi Kirim SPT Digital ke dalam sistem SiTPP dan menyediakan antarmuka antrean verifikasi (*approval list*) di Panel Admin SiTPP sebelum hak akses atau status pengiriman dinyatakan sah.

**Architecture:** 
1. Sisi Pengirim (`sptdigitalbagor`): Saat submit SPT dengan integrasi SITPP, sistem mengirimkan payload ke node `spt_approvals/{year}/{id}` di Firebase Realtime Database SiTPP dengan status `PENDING`.
2. Sisi SiTPP (`Proyek SiTPP`): Menambahkan modul `js-admin-spt-approval.html`, konfigurasi path di `js-config.html`, query di `js-db.html`, dan update aturan keamanan di `database.rules.json`.
3. Admin/Evaluator SiTPP dapat meninjau, menyetujui, atau menolak permohonan dengan catatan alasan penolakan.

**Tech Stack:** Firebase Realtime Database (RTDB), Vanilla JavaScript (Modular ES5/ES6), Bootstrap 5 / Tailwind CSS, SweetAlert2.

---

## Rincian File yang Dilibatkan

### Di Workspace SiTPP (`/home/falcon/Documents/Proyek SiTPP`):
- `js-config.html`: Menambahkan konstanta path `DB_PATHS.SPT_APPROVALS = 'spt_approvals'`.
- `js-db.html`: Menambahkan fungsi `getSptApprovals()`, `approveSptSubmission()`, dan `rejectSptSubmission()`.
- `js-admin-spt-approval.html` (BARU): Komponen halaman verifikasi dan daftar approval SPT.
- `index.html`: Menambahkan menu navigasi "Verifikasi SPT Operator" di dashboard Admin SiTPP.
- `database.rules.json`: Menambahkan permission write/read untuk node `spt_approvals`.

### Di Workspace Kirim SPT Digital (`/home/falcon/Documents/ProyekKirimSPTDigital/sptdigitalbagor`):
- `build.js`: Menambahkan handler pengiriman data ke Realtime Database SiTPP saat `data.integrasi === "SITPP"` di dalam fungsi `submitSptData`.
- `apps_script/Index.html`: Update pesan konfirmasi agar operator mengetahui berkas telah masuk ke antrean verifikasi SiTPP.

---

## Tasks

### Task 1: Konfigurasi Database & Security Rules di SiTPP
**Files:**
- Modify: `js-config.html:50-70`
- Modify: `database.rules.json:40-60`
- Modify: `js-db.html:600-650`

- [ ] **Step 1: Daftarkan path `SPT_APPROVALS` di `js-config.html`**
  Tambahkan:
  ```javascript
  SPT_APPROVALS: 'spt_approvals'
  ```
- [ ] **Step 2: Tambahkan fungsi database di `js-db.html`**
  - `getSptApprovals(year, statusFilter)`: Mendengarkan / membaca `spt_approvals/{year}`.
  - `updateSptApprovalStatus(year, submissionId, status, notes, reviewer)`: Melakukan update status `APPROVED` atau `REJECTED`.
- [ ] **Step 3: Update `database.rules.json` di SiTPP**
  Izinkan read bagi user terautentikasi dan write approval bagi admin/evaluator.

---

### Task 2: Modul UI Verifikasi SPT di Admin SiTPP
**Files:**
- Create: `js-admin-spt-approval.html`
- Modify: `index.html` (Navigasi Sidebar/Menu Admin)
- Modify: `js-admin.html` (Routing tab)

- [ ] **Step 1: Buat template `js-admin-spt-approval.html`**
  - Header dengan filter status (Semua, Menunggu, Disetujui, Ditolak).
  - Search box OPD dan tanggal.
  - Tabel responsif data pengirim (Nama, NIP, OPD, Atasan, Tanggal, Status).
  - Modal detail pratinjau tanda tangan digital dan data SPT.
  - Tombol aksi SweetAlert untuk Setujui dan Tolak (dengan prompt alasan).
- [ ] **Step 2: Daftarkan include dan rute di `index.html` dan `js-admin.html`**
  - Sisipkan `<?!= HtmlService.createHtmlOutputFromFile('js-admin-spt-approval').getContent(); ?>`.
  - Tambahkan link menu sidebar "Verifikasi SPT Operator".
  - Buat badge counter untuk menghitung submisi dengan status `PENDING`.

---

### Task 3: Pengiriman Data dari Kirim SPT Digital ke RTDB SiTPP
**Files:**
- Modify: `sptdigitalbagor/build.js`
- Modify: `sptdigitalbagor/apps_script/Index.html`

- [ ] **Step 1: Tambahkan pengiriman ke SiTPP di `build.js`**
  Di dalam `FirebaseService.submitSptData(data)`:
  Jika `data.integrasi === "SITPP"`:
  Kirim payload ke Firebase Realtime Database SiTPP via REST API endpoint:
  `https://sitpp-7b65d-default-rtdb.asia-southeast1.firebasedatabase.app/spt_approvals/${currentYear}/${docRef.id}.json`
- [ ] **Step 2: Perbarui notifikasi sukses di `apps_script/Index.html`**
  Tampilkan keterangan bahwa berkas berhasil diserahkan ke SiTPP dan saat ini berstatus *"Menunggu Verifikasi Admin SiTPP"*.
- [ ] **Step 3: Compile dan build `sptdigitalbagor`**
  Jalankan `npm run build` dan pastikan file `public/index.html` terbarui.

---

### Task 4: Pengujian Lintas Aplikasi (End-to-End)
- [ ] **Step 1: Kirim SPT baru bertema SITPP dari web `sptdigitalbagor`**
- [ ] **Step 2: Buka dashboard Admin SiTPP dan periksa menu Verifikasi SPT**
- [ ] **Step 3: Lakukan uji Setujui (Approve) dan pastikan status terupdate real-time**
- [ ] **Step 4: Lakukan uji Tolak (Reject) dengan alasan catatan**
