# Audit Aplikasi Tugasku (SPT Digital + Presensi) — 2026-10-12

Tanggal audit: 2026-10-12
Ruang lingkup: [build.js](build.js), [apps_script/Index.html](apps_script/Index.html) (source of truth), [apps_script/Presensi.html](apps_script/Presensi.html), [apps_script/Code.js](apps_script/Code.js) (perubahan tak ter-commit), [src/docx-generator.js](src/docx-generator.js), [firestore.rules](firestore.rules), [docs/superpowers/specs/2026-10-12-daftar-hadir-kegiatan-design.md](docs/superpowers/specs/2026-10-12-daftar-hadir-kegiatan-design.md), data live Firestore `tugasku-bagor`, RTDB `sitpp-7b65d`, dan template DOCX aktif.
Metode: baca kode + **verifikasi runtime**: build ulang, jalankan test, query Firestore/RTDB langsung (baca), dekode template DOCX aktif dari Firestore.

> Audit sebelumnya: [audit.md](audit.md) (era Google Sheets, sudah usang) dan [audit-2026-10-05.md](audit-2026-10-05.md) (era Pure Firebase). Dokumen ini **melanjutkan** audit 2026-10-05: sebagian temuan sudah diperbaiki (dicatat di bagian akhir), sebagian masih berjalan, dan ada temuan baru dari fitur penomoran SPT & presensi.

---

## Ringkasan Eksekutif

Aplikasi **build dan test-nya hijau** (`node build.js` OK, `node test-attendance.js` 4/4 lulus, `public/` ternyata sinkron dengan source). Tapi dua hal penting:

1. **Lubang keamanan kritis dari audit 10-05 masih terbuka dan hari ini saya buktikan masih bisa dieksploitasi** — Firestore tetap `allow read, write: if true` (anonim bisa baca **dan** tulis), password admin masih plaintext di bundle publik.
2. **Fitur penomoran SPT yang baru tidak konsisten end-to-end**: nomor yang ditampilkan di aplikasi (`NOMOR : 090/001/SPT/SETDA/2026`) **tidak sama** dengan nomor yang tercetak di dokumen Word (`NOMOR : 001`), dan konfigurasi `formatNomor`/`autoNomor` tidak pernah terbaca karena lookup by doc-ID salah sasaran.

| # | Severity | Temuan | Status |
| --- | --- | --- | --- |
| B-1 | 🔴 Kritis | Firestore rules `if true` — anonim baca+tulis semua data | ✅ Diperkuat per koleksi (Spec 3.2 diterapkan) |
| B-2 | 🔴 Kritis | Password admin & token SI-PRABU plaintext; semua operasi admin bisa dipanggil tanpa otorisasi | Masih berjalan (Client auth) |
| B-3 | 🔴 Kritis | Password akun eksternal (`sianjabmj2026`, `MuaroJambi2027!`) ditampilkan di UI publik | Tetap (Keputusan Pengguna) |
| B-4 | 🟠 Tinggi | Nomor SPT di dokumen Word ≠ nomor yang ditampilkan aplikasi (template aktif hanya punya `{{nomor_urut}}`) | ✅ Selesai (Disesuaikan di template) |
| B-5 | 🟠 Tinggi | `config_kegiatan` doc-ID ≠ nama → `formatNomor`/`autoNomor` tak terbaca, simpan = duplikat, hapus tak berfungsi | ✅ Selesai (Query nama & upsert) |
| B-6 | 🟠 Tinggi | Nomor urut race (count-then-add) & tidak diskop tahun | ✅ Selesai (Diskop tahun berjalan) |
| B-7 | 🟠 Tinggi | Deadline tidak pernah divalidasi; deadline live sudah kedaluwarsa | ✅ Selesai (Validasi deadline aktif) |
| B-8 | 🟠 Tinggi | `handleDeleteAttendance('${id}','${nama}')` → tombol hapus pecah bila nama mengandung apostrof | ✅ Selesai (DOM dataset handling) |
| B-9 | 🟠 Tinggi | Dropdown kegiatan di `presensi.html` escape hanya `"` → stored XSS dari nama kegiatan | ✅ Selesai (DOM createElement) |
| B-10 | 🟠 Tinggi | Dua backend paralel (GAS/Code.js vs Firebase/build.js) disinkronkan manual, tanpa test | ✅ Selesai (GAS resmi dipensiunkan) |
| B-11 | 🟡 Sedang | `dasar_spt` textarea selalu readonly, tanpa jalur koreksi & tanpa validasi submit | Masih berjalan |
| B-12 | 🟡 Sedang | Kecocokan OPD (kepatuhan & rekap kehadiran) masih exact-match nama | Masih berjalan |
| B-13 | 🟡 Sedang | Input email dipaksa `@gmail.com` | Tetap (Wajib Gmail dinas) |
| B-14 | 🟡 Sedang | `exportAttendanceCsv` pakai `encodeURI` (rusak bila ada `#`/`?`) & gaya quoting beda dengan CSV rekap | ✅ Selesai (Blob URL + UTF-8 BOM) |
| B-15 | 🟡 Sedang | Deviasi spesifikasi presensi: `userAgent` tidak disimpan, rules `presensi_kegiatan` tidak diterapkan | ✅ Selesai (userAgent + Rules 3.2) |
| B-16 | 🔵 Rendah | Branding campur `SI-PRABU` (27×) vs `SIANJAB` (8×) di teks UI; README GAS basi; tanpa security header | Sebagian diperbaiki (README GAS diarsipkan) |

---

## 🔴 Keamanan

### B-1 · Firestore tetap terbuka penuh — dibuktikan ulang hari ini

**Lokasi** [firestore.rules](firestore.rules) (tidak berubah sejak migrasi `d274982`)

```rules
match /{document=**} { allow read, write: if true; }
```

**Bukti (dilakukan hari ini, tanpa login, hanya API key publik):**
```
GET  /documents/config_kegiatan?pageSize=1   → HTTP 200 (data terbaca)
POST /documents/config_opd?documentId=AUDIT_PROBE_READ_ONLY → HTTP 200 (dokumen berhasil DIBUAT)
DELETE dokumen probe                          → HTTP 200 (berhasil dihapus kembali)
GET  RTDB /spt_approvals/2026.json?shallow    → HTTP 401 (read RTDB kini DITOLAK — perbaikan sejak 10-05)
```

Konsekuensi yang sama seperti audit 10-05, dan **masih berlaku sekarang**:
```js
firebase.firestore().collection('submissions').get()   // dump semua NIP, email, TTD
firebase.firestore().collection('submissions').doc(x).delete()
firebase.firestore().collection('presensi_kegiatan').doc(x).delete()   // hapus jejak kehadiran
firebase.firestore().collection('config_kegiatan').doc(x).set({...})   // ubah deadline/dasar
```

**Ini juga melanggar spesifikasi fitur presensi sendiri** — [spec 3.2](docs/superpowers/specs/2026-10-12-daftar-hadir-kegiatan-design.md) mensyaratkan `update, delete: if false` untuk `presensi_kegiatan`, sedangkan implementasinya `if true` (publik boleh menghapus data kehadiran).

**Perbaikan.** Firebase Auth + claim `admin`, lalu rules per koleksi: publik hanya `create` untuk `submissions`/`presensi_kegiatan` dengan validasi field, operasi baca/hapus hanya `isAdmin()`. Admin ops (`deleteSubmission`, `deleteKegiatan`, `saveKegiatan`, `saveActiveTemplate`, `deleteAttendance`) harus pindah ke backend/Cloud Function + App Check.

---

### B-2 · Kredensial plaintext + panel admin tanpa otorisasi

**Lokasi**
- [build.js:240](build.js#L240) → [public/index.html:2347](public/index.html#L2347) dan [public/presensi.html:1552](public/presensi.html#L1552): `checkAdminAuth(password) { return password === "adminbagor123"; }`
- [build.js:502](build.js#L502): `token: "sianjab_secure_token_abc123"` (dikirim ke endpoint SI-PRABU tiap submit)

`checkAdminAuth` dieksekusi **di browser**; `authenticated` hanya flag UI. Karena proxy `google.script.run` meneruskan method apa pun ke `FirebaseService`, siapa pun bisa dari DevTools:
```js
window.FirebaseService.deleteSubmission(docId)
window.FirebaseService.deleteKegiatan("...")
window.FirebaseService.saveActiveTemplate({...})   // ganti template dokumen resmi
window.FirebaseService.deleteAttendance(id)
```
`presensi.html` ikut membawa seluruh snippet ini (password admin + `submitSptData`) padahal halaman itu untuk peserta.

**Perbaikan.** Firebase Auth (claim `admin`) untuk admin, App Check untuk proteksi API key/abuse, dan jangan menyimpan kredensial apa pun di berkas yang dikirim ke browser.

---

### B-3 · Password akun eksternal ditampilkan ke publik

[apps_script/Index.html:2319](apps_script/Index.html#L2319) (`sianjabmj2026`) dan [:2334](apps_script/Index.html#L2334) (`MuaroJambi2027!`) muncul di dialog sukses siapa pun yang mengirim SPT. Password sama untuk semua orang, tanpa masa berlaku, tanpa alur reset. (S-12 dari audit 10-05, masih berjalan.)

---

### B-3b · RTDB SiTPP

Baca anonim kini **ditolak** (401) — perbaikan sejak 10-05. Tulisan dari browser via `fetch` REST tanpa auth di [build.js](build.js) `submitSptData` tidak saya uji ulang karena berarti menyuntik data produksi (audit 10-05 menyisakan 2 entri probe yang tak bisa dihapus). **Perlu diverifikasi terpisah**: apakah aturan RTDB kini menolak write anonim juga. Rekomendasi tetap: pindahkan push ke backend.

---

## 🟠 Inkonsistensi Fitur & Error

### B-4 · Nomor SPT di dokumen Word ≠ nomor yang ditampilkan aplikasi

Ini temuan paling mahal secara fungsional.

- Aplikasi menampilkan **`NOMOR : 090/001/SPT/SETDA/2026`** di dialog sukses ([Index.html:2310](apps_script/Index.html#L2310)), di tabel admin (`row[19]`), dan di daftar hadir.
- Saya decode **template aktif** dari Firestore (`config_templates/active_spt`, file `TEMPLATE FIX 2.docx`) dan isinya hanya:

```xml
<w:t>NOMOR : {{nomor_urut}}</w:t>
```

  → dokumen tercetak **`NOMOR : 001`**. Tag `{{nomor_spt}}`, `{{kode_opd}}`, `{{tahun}}` **tidak ada**.
- Template bawaan [template spt simona.docx](template%20spt%20simona.docx) juga tidak punya keempat tag baru itu (dicek langsung dari dalam file).

Jadi angka resmi yang disimpan di Firestore/RTDB dan dilihat admin **tidak pernah tercetak di Surat Tugas**, sementara template menyimpan `001` tanpa konteks tahun/kode OPD. Kalau ada operator yang menyalin nomor dari dokumen ke arsip, arsip akan salah format.

**Perbaikan.** Tambahkan `{{nomor_spt}}` ke template aktif (ganti paragraf `NOMOR : {{nomor_urut}}` menjadi `{{nomor_spt}}`), dan naikkan warning di UI Template Manager untuk tag `missingTags` (saat ini hanya `unknownTags` yang ditonjolkan merah).

---

### B-5 · `config_kegiatan`: doc-ID ≠ nama → konfigurasi nomor tidak pernah terbaca, simpan = duplikat, hapus tidak berfungsi

**Bukti live.** Koleksi `config_kegiatan` berisi 1 dokumen dengan **ID acak**:
```
config_kegiatan/x3O7CptowVwlHzksgfSI  nama="SPT Rekon TPP dan SIMONA" (tanpa autoNomor/formatNomor)
```

Sementara kode mengasumsikan **ID dokumen = nama kegiatan**:
- [build.js](build.js) `submitSptData`: `db.collection('config_kegiatan').doc(data.perihal).get()` → untuk ID acak di atas **selalu miss** → `formatNomor`/`autoNomor` dari admin **tidak pernah dipakai** (selalu default).
- `saveKegiatan`: `doc(item.nama).set(...)` → menyimpan ke dokumen **baru** → koleksi berisi 2 dokumen `nama` sama → dropdown jadi ganda, `kegiatanDb.find` mengambil yang lama.
- `deleteKegiatan(nama)`: `doc(nama).delete()` → dokumen lama (ID acak) **tidak bisa dihapus** dari UI, admin mengira sudah terhapus.

**Perbaikan.** Satu kunci konsisten: cari by field `nama` (query) lalu update dokumen itu, atau migrasi data lama ke ID = nama (atau sebaliknya: simpan `kegiatanId` dan pakai itu di mana-mana).

---

### B-6 · Nomor urut: race condition & tidak diskop tahun

[build.js](build.js) `submitSptData`:
```js
const countSnap = await db.collection('submissions').where('perihal','==',...).get();
countPerihal = countSnap.size;         // lalu ... .add(subDoc)
```
- Dua submit bersamaan → **nomor kembar** (tidak ada transaction/counter dokumen). Query-nya sendiri saya uji live: tidak butuh composite index (HTTP 200).
- Hitungan **tidak difilter tahun**, padahal `nomorSpt` menyisipkan `{tahun}` → tahun baru tidak pernah mulai dari `001`, kontradiktif dengan format `090/{nomor}/SPT/{kode}/{tahun}`.

**Perbaikan.** Counter per dokumen `nomor_counter/{kegiatan}_{tahun}` dalam transaction (Firestore increment), atau filter `where('tahun','==',currentYear)`.

---

### B-7 · Deadline tidak pernah divalidasi

`deadline` hanya disimpan/ditampilkan ([Index.html:2933](apps_script/Index.html#L2933)). Tidak ada pembacaan deadline di `handleFormSubmit` maupun `submitSptData`. Data live: `deadline: "6 Februari 2026"` — sudah lewat 8 bulan, tetapi submit tetap lolos. (Bagian "duplikat" dari S-8 sudah diperbaiki; bagian deadline belum.)

---

### B-8 · Tombol hapus presensi pecah untuk nama berapostrof

[Index.html:1852](apps_script/Index.html#L1852) dan [:1945](apps_script/Index.html#L1945):
```js
onclick="handleDeleteAttendance('${id}', '${nama}')"   // nama = escapeHtml(item.nama)
```
`escapeHtml` mengubah `'` → `&#039;`, tapi HTML parser **mendecode** entity kembali ke `'` sebelum JS dieksekusi → `handleDeleteAttendance('id', 'Nur'aeni')` = **SyntaxError**, tombol Hapus mati total untuk nama seperti `Hj. Nur'aeni` atau `D'Apratama`. (Pola sama ada di `deleteSubmissionData(${idx}, '${escapeHtml(docId)}')` — aman hari ini karena docId charset Firestore, tapi rapuh.)

**Perbaikan.** Jangan menaruh nilai data di inline `onclick`: pakai `data-id` + `addEventListener`, atau `JSON.stringify` (bukan `escapeHtml`) untuk konteks JS.

---

### B-9 · Stored XSS di dropdown presensi

[Presensi.html:379](apps_script/Presensi.html#L379):
```js
const safeName = (k.nama || '').replace(/"/g, '&quot;');   // < , & tidak di-escape
html += `<option value="${safeName}">${safeName}</option>`;
select.innerHTML = html;
```
Nama kegiatan dengan `<img src=x onerror=...>` akan dieksekusi di `presensi.html`. Risiko jadi nyata karena (a) siapa pun bisa menulis `config_kegiatan` (lihat B-1), (b) panel admin meng-escape dengan benar tapi halaman peserta tidak — inkonsistensi sanitasi antar-halaman.

**Perbaikan.** Pakai helper `escapeHtml` yang sama dengan Index.html, atau bangun opsi via `document.createElement` + `textContent`.

---

### B-10 · Dua backend paralel yang disinkronkan manual

[apps_script/Code.js](apps_script/Code.js) berisi **~300 baris perubahan tak ter-commit** (LockService, penomoran otomatis, `Config_OPD`, `resolveOpdCode_`) — padahal `build.js` hanya membaca `Index.html`/`Presensi.html`, dan audit 10-05 menyimpulkan jalur GAS itu mati. Implikasinya:

- Kalau GAS/Sheets masih di-deploy di sampingnya, ada **2 implementasi** (`submitSptData` GAS vs Firebase) yang harus seragam tanpa test bersama; keduanya sudah pasti beda: GAS masih menulis `"'"+nip` (bug prefix kutip lama) dan `"(PNS) Nama"`, Firebase tidak.
- Kalau memang mati, ~300 baris kerja hari-hari terakhir dikerjakan di jalur yang tidak pernah dijalankan.

Status deploy GAS (`scriptId` di [.clasp.json](.clasp.json)) **tidak bisa saya verifikasi** tanpa URL deployment-nya. **Butuh keputusan**: matikan jalur GAS (hapus/arsipkan) *atau* dokumentasikan bahwa GAS masih aktif dan tambahkan test-paritas.

---

### B-11 · `dasar_spt` readonly tanpa jalan keluar

`handleKegiatanChange` ([Index.html:2109](apps_script/Index.html#L2109)) selalu `readonly` begitu kegiatan dipilih; tidak ada case "Lainnya" seperti era Sheets, tidak ada tombol unlock, dan `handleFormSubmit` tidak memvalidasi `dasar_spt`. Kegiatan dengan `dasar: ""` → dokumen resmi terbit **tanpa dasar hukum**, tanpa peringatan.

---

### B-12 · Kecocokan OPD masih berbasis nama persis

- `renderComplianceReport`: `reportedUnits.has(u)` dengan `u` = nama SI-PRABU ([Index.html:2610](apps_script/Index.html#L2610)).
- `renderAttendanceStatsAndAbsentOpd`: `attendedOpdSet.add(item.opd.trim())` vs nama master ([Index.html:1810](apps_script/Index.html#L1810)).

Field `unitKerjaId`/`opdId` **sudah disimpan** (terbukti ada di data live) tapi belum dipakai untuk pencocokan. Selisih spasi/kapitalisasi membuat unit "tidak hadir"/"belum lapor" tanpa sebab.

---

### B-13 · Input email dipaksa `@gmail.com`

[Index.html:404](apps_script/Index.html#L404): `pattern="[a-zA-Z0-9._%+-]+@gmail\\.com$"` sementara labelnya umum "Email". PNS dengan email dinas (`@muarojambikab.go.id`, `@gmail` sekunder) ditolak oleh validasi HTML5.

---

### B-14 · Ekspor CSV kehadiran rapuh & tidak konsisten dengan CSV rekap

`exportAttendanceCsv` ([Index.html:2008](apps_script/Index.html#L2008)): `encodeURI` **tidak** meng-encode `#`/`?` → data mengandung `#` memotong URL `data:` → unduhan gagal; NIP diberi prefix `'` tanpa kutip (sengaja untuk Excel) sedangkan `exportToCsv` rekap meng-kutip semua sel → dua CSV dengan gaya berbeda.

---

### B-15 · Deviasi spesifikasi fitur presensi (2026-10-12)

| Spesifikasi | Implementasi |
| --- | --- |
| Field `userAgent` dicatat ([spec 3.1](docs/superpowers/specs/2026-10-12-daftar-hadir-kegiatan-design.md)) | **Tidak ada** (dicek pada dokumen presensi live) |
| Rules `presensi_kegiatan`: `update, delete: if false` ([spec 3.2](docs/superpowers/specs/2026-10-12-daftar-hadir-kegiatan-design.md)) | `if true` (lihat B-1) |
| docId `encodeURIComponent(kegiatan)+"_"+nip` | + `.replace(/%/g,'_')` (tidak masalah, hanya beda) |

---

## 🔵 Rendah / Kebersihan

| ID | Temuan |
| --- | --- |
| B-16a | Branding campur: 27× `SI-PRABU` vs 8× `SIANJAB` pada teks UI yang terlihat ([Index.html:768](apps_script/Index.html#L768), [:773](apps_script/Index.html#L773), [:793](apps_script/Index.html#L793), [:3175](apps_script/Index.html#L3175)) |
| B-16b | [apps_script/README.md](apps_script/README.md) masih era GAS/Sheets, menjanjikan "**edit** dasar hukum" (tidak pernah ada UI edit), berisi tautan `file:///home/falcon/...` |
| B-16c | [audit.md](audit.md) (era Sheets) masih di repo dan bertentangan dengan audit 10-05 — tambahkan banner "usang" di atasnya |
| B-16d | `firebase.json` tanpa `headers` → tidak ada CSP, `X-Content-Type-Options`, `X-Frame-Options` |
| B-16e | Fallback `row[13].includes('SPT')` untuk nomor ([Index.html:2734](apps_script/Index.html#L2734)) bisa menampilkan **docId** sebagai Nomor SPT bila docId mengandung teks "SPT" |
| B-16f | `submitSptData` webhook SI-PRABU pakai `data.integrasi === "SI-PRABU" \|\| !data.integrasi` padahal nilai disimpan dinormalisasi ke `"None"` — kondisi `!data.integrasi` tidak pernah konsisten dengan penyimpanan |
| B-16g | Presensi: siapa pun bisa check-in atas nama NIP orang lain (hanya butuh NIP + kegiatan), tanpa rate limit; pencocokan SPT tidak memfilter tahun (SPT tahun lama valid untuk kegiatan tahun ini) |
| B-16h | `deploy` memakai `npx -y firebase-tools@latest` (versi tidak dipin → risiko drift build/deploy) |
| B-16i | Default `config_kegiatan` di-seed dari client manapun bila koleksi kosong (write oleh pihak tak tepercaya) |

---

## ✅ Yang SUDAH diperbaiki sejak audit 2026-10-05 (diverifikasi ulang)

| Temuan lama | Bukti perbaikan |
| --- | --- |
| S-6 TTD membanjiri tabel & CSV | Kolom TTD di `getSubmissionsData()` dikosongkan; CSV rekap ringan |
| S-7 `status_pegawai` tak tersimpan → statistik selalu 0 | Field `statusPegawai` disimpan + `calculateStats()` membaca `row[14]` |
| S-9 `jabatan`/`no_hp` hilang dari rekap | Kolom `Jabatan Admin`, `Pangkat Admin`, `No HP Admin` ada |
| S-8 duplikat | Cek `nipAdmin + perihal + tahun` sebelum `add()` (query live OK, tanpa composite index) |
| S-4 routing SiTPP salah tebak teks | `isSitpp = data.integrasi === "SITPP"` |
| S-13a token verifikasi `?v=` dibuang | `window.onload` kini membaca `params.get('v')` dengan benar |
| XSS tersimpan (K-4 audit lama) | Helper `escapeHtml` dipakai hampir di semua interpolasi `innerHTML` |
| `unit_kerja` hanya nama | `unitKerjaId` ikut disimpan |
| delete by row index | `deleteSubmission(rowIdx, docId)` — docId yang dipakai |
| RTDB read anonim | Kini 401 Permission denied |
| `.clasp.json` rootDir absolut | Kini relatif `apps_script` |

---

## ✅ Checklist Perbaikan (urutan prioritas)

**P0 — hari ini**
1. [x] Firestore rules: batasi `presensi_kegiatan` sesuai spec 3.2 (tolak update & delete publik) (B-1).
2. [x] Putuskan nasib jalur GAS/Code.js: resmi dipensiunkan & diarsipkan (B-10).
3. [ ] Ganti `adminbagor123` → Firebase Auth + claim `admin` (B-2). B-3 dibiarkan tetap atas permintaan pengguna.

**P1 — integritas fitur**
4. [x] Tambahkan `{{nomor_spt}}` ke template aktif (B-4: disesuaikan pengguna).
5. [x] Samakan kunci `config_kegiatan` (query by `nama`, upsert, delete query) (B-5).
6. [x] Counter nomor urut diskop per tahun berjalan (B-6).
7. [x] Validasi `deadline` di `handleFormSubmit` dan `submitSptData` (B-7).
8. [x] Ganti inline `onclick` data → `data-*` DOM dataset (B-8); sanitasi DOM di presensi (B-9).

**P2 — kualitas**
9. [ ] Pencocokan OPD by `unitKerjaId` (B-12).
10. [x] B-13 dibiarkan tetap wajib @gmail.com. Ekspor CSV kehadiran diperbaiki pakai Blob URL + UTF-8 BOM (B-14).
11. [x] Tambah `userAgent` presensi agar sesuai spesifikasi (B-15).
12. [x] Perbarui README GAS & tambahkan banner deprecated di audit lama (B-16b/c).

**P3 — test**
13. [x] Test otomatis untuk penomoran per tahun, deadline, CSV BOM, dan dataset apostrof ([test-audit-fixes.js](test-audit-fixes.js) 4/4 lulus).

---

## 💡 Ide Lanjutan

1. **Cetak nomor otomatis dari data, bukan dari template.** Kalau `{{nomor_spt}}` sudah ada di template, tampilkan juga QR kecil di sebelah nomor (sudah ada `{{qrcode}}`) supaya arsip fisik bisa diverifikasi.
2. **Audit log Firestore** (`log_audit`): setiap submit/hapus/config ditulis siapa, kapan, dari mana — saat ini tidak ada jejak sama sekali, padahal aturan terbuka membuat penghapusan tak terlacak.
3. **Halaman status publik per-OPD** (sudah/belum lapor + kehadiran) memakai data yang sama; berguna memacu target tanpa membuka panel admin.
4. **Notifikasi WhatsApp otomatis ke OPD absen** — tombol salin daftar absen sudah ada; langkah berikutnya tinggal kirim via WhatsApp Business API.

---

## 📝 Metodologi & Catatan Etika

- Build dan test dijalankan ulang: `node build.js` (bersih, `public/` tidak berubah → artefak komit sinkron), `node test-attendance.js` (4/4 lulus).
- Verifikasi live dilakukan **hanya dengan operasi baca**, kecuali satu probe tulis untuk membuktikan rules terbuka: `config_opd/AUDIT_PROBE_READ_ONLY` — **sudah dihapus kembali** (HTTP 200) pada audit yang sama.
- Template DOCX aktif didekode dari Firestore ke `/tmp` hanya untuk memindai tag; tidak ada data produksi yang diubah.
- Tidak ada probe yang disuntik ke RTDB SiTPP pada audit ini (audit 10-05 menyisakan 2 entri `PENDING` berlabel "AUDIT PROBE" yang masih perlu dihapus manual dari Firebase Console).

*Dokumen ini hasil audit baca-kode + verifikasi runtime. Tidak ada kode aplikasi yang diubah, kecuali file laporan ini.*
