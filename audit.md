# Audit Aplikasi Kirim SPT Digital (GAS)

> [!WARNING]
> **DOKUMEN USANG / DEPRECATED:**
> Audit ini dibuat pada 2026-10-02 pada era Google Apps Script + Google Sheets. Sistem telah dimigrasikan ke Pure Firebase. Laporan audit terkini yang aktif adalah [audit-2026-10-12.md](audit-2026-10-12.md) / [nih.md](nih.md).

Tanggal audit: 2026-10-02
Ruang lingkup: [apps_script/Code.js](apps_script/Code.js), [apps_script/Index.html](apps_script/Index.html), integrasi SIANJAB, Panel Admin, API `checkSpt`.
Metode: penelusuran kode end-to-end + pengujian langsung endpoint SIANJAB yang dipakai aplikasi.

---

## Ringkasan Eksekutif

Aplikasi berfungsi sebagai pengirim Surat Perintah Tugas (SPT) digital untuk Pemerintah Kabupaten Muaro Jambi. Yang paling penting dari audit ini:

> **Integrasi SIANJAB saat ini sudah mati diam-diam.** Daftar unit kerja yang tampil di form bukan dari SIANJAB, melainkan daftar hardcoded 80 unit. Aplikasi *tampak* normal padahal tidak pernah sinkron dengan server SIANJAB.

Di luar itu ditemukan 3 bug pada endpoint `checkSpt` (termasuk satu yang membuat pengecekan NIP selalu gagal), 4 celah keamanan pada Panel Admin, dan beberapa masalah kerapian/data.

| Severity | Jumlah | Ringkasan |
| --- | --- | --- |
| 🔴 Kritis | 4 | Integrasi SIANJAB mati, admin tanpa proteksi, XSS tersimpan, `checkSpt` NIP selalu gagal |
| 🟠 Tinggi | 5 | Match OPD hancur, duplikasi data, TTD bisa melebihi batas sel, password/token plaintext, config kegiatan rusak |
| 🟡 Sedang | 7 | Tanpa validasi deadline, tanpa edit kegiatan, tanpa locking, timestamp string, nama file tidak aman, tanpa monitoring |
| 🔵 Rendah | 4 | Kode mati, hardcoded ID, dokumentasi tidak sinkron, helper tidak terpakai |

---

## 🔴 Temuan Kritis

### K-1 · Integrasi SIANJAB mati — daftar OPD fallbackDiam-diam (PRIORITAS TERTINGGI)

**Lokasi**
- [Index.html:834-868](apps_script/Index.html#L834-L868) `loadOpdFromSianjab()`
- [Index.html:836](apps_script/Index.html#L836) endpoint
- [Code.js:39](apps_script/Code.js#L39) & [Code.js:296-302](apps_script/Code.js#L296-L302)

**Bukti (pengujian langsung)**
```
GET .../exec?action=readAll&entity=unitKerja
→ {"success": false, "error": "Token tidak valid atau sudah kadaluarsa. Silakan login ulang."}

GET .../exec?action=readAll&entity=unitKerja&token=sianjab_secure_token_abc123
→ {"success": false, "error": "Token tidak valid atau sudah kadaluarsa. Silakan login ulang."}
```

**Gejala.** Fetch di [Index.html:838](apps_script/Index.html#L838) selalu jatuh ke `.catch()` di [Index.html:866](apps_script/Index.html#L866) yang hanya `console.error`. Select unit kerja diam-diam menampilkan daftar hardcoded. Tidak ada indikator ke user, tidak ada alarm ke admin.

**Dampak.**
- Data unit kerja di form **tidak pernah diverifikasi terhadap SIANJAB**.
- Unit baru/rename di SIANJAB tidak muncul; unit yang sudah dihapus di SIANJAB masih bisa dipilih.
- Admin tampak meyakinkan diri bahwa data sudah sinkron, padahal tidak.

**Perbaikan.**
1. Server-side proxy: `getUnitKerjaList()` di Code.js memakai `UrlFetchApp` → tidak ada CORS, tidak ada token terekspos ke browser, bisa di-cache via `CacheService` (TTL 1 jam) untuk hemat kuota.
2. **Hapus seluruh fallback** (lihat K-2). Bila SIANJAB gagal, form tampilkan state error eksplisit + tombol "Coba Lagi", bukan daftar palsu.
3. `checkAdminAuth` dan `triggerAuthorization` jangan dipakai untuk pemanggilan service-to-service; tambahkan token service khusus (lihat R-4).

---

### K-2 · Tiga sumber data OPD yang tidak sinkron

| # | Sumber | Lokasi | Dipakai untuk |
| --- | --- | --- | --- |
| 1 | `<optgroup>` hardcoded | [Index.html:156-250](apps_script/Index.html#L156-L250) | opsi select operator |
| 2 | `masterUnit` JS object | [Index.html:716-755](apps_script/Index.html#L716-L755) | laporan kepatuhan admin |
| 3 | SIANJAB API | [Index.html:836](apps_script/Index.html#L836) | (mati — lihat K-1) |

**Dampak.** `renderComplianceReport()` di [Index.html:1248-1292](apps_script/Index.html#L1248-L1292) menghitung "unit sudah melapor" dengan mencocokkan `row[2]` ke `masterUnit`. Karena sumber ini terpisah dari SIANJAB, statistik kepatuhan di Panel Admin **secara struktural tidak akan pernah akurat** begitu SIANJAB berubah.

**Perbaikan.** Hilangkan #1 dan #2 sepenuhnya. Bangun laporan kepatuhan dari data SIANJAB: grup = unit bertingkat atas (`parentId` kosong), anggota = sub-unit. Master unit menjadi milik SIANJAB, bukan milik aplikasi ini.

---

### K-3 · Fungsi Admin tanpa autentikasi — data & TTD bisa dikuras siapa pun

**Lokasi**
- [Code.js:236](apps_script/Code.js#L236) `getSubmissionsData()`
- [Code.js:251](apps_script/Code.js#L251) `deleteSubmission()`
- [Code.js:204](apps_script/Code.js#L204) `saveKegiatan()`
- [Code.js:219](apps_script/Code.js#L219) `deleteKegiatan()`
- Bandingkan [Code.js:441](apps_script/Code.js#L441) `checkAdminAuth()`

**Bukti.** `checkAdminAuth(password)` satu-satunya penjaga. UI menyembunyikan panel lewat flag client `authenticated` ([Index.html:1121](apps_script/Index.html#L1121)), tetapi pemanggilan server tetap berjalan tanpa password. Siapa pun yang bisa memuat halaman (deployment `access: "ANYONE"` di [appsscript.json](apps_script/appsscript.json)) dapat menjalankan dari DevTools:

```js
google.script.run.getSubmissionsData();   // semua nama, NIP, email, TTD
google.script.run.deleteSubmission(3);     // hapus baris mana saja
google.script.run.saveKegiatan({...});     // sisip kegiatan
```

**Dampak.** Kebocoran PII (nama, NIP, email, no HP via dokumen), penghapusan data, dan manipulasi konfigurasi kegiatan — tanpa perlu password.

**Perbaikan.**
- Server-side session: `checkAdminAuth` mengembalikan token acak (32 hex) yang disimpan di `CacheService` dengan TTL 8 jam.
- Semua fungsi admin menerima `sessionToken` dan menolak dengan `{status:"error", message:"Sesi tidak valid"}` bila tidak sah.
- `deleteSubmission` WAJIB cek sesi — ini yang paling berbahaya karena destruktif.

---

### K-4 · Stored XSS dari input teks bebas

**Lokasi**
- [Index.html:1305-1327](apps_script/Index.html#L1305-L1327) `renderSubmissionTable()` — `row[3]` (nama), `row[6]` (nama atasan)
- [Index.html:1300-1310](apps_script/Index.html#L1300) `renderComplianceReport()` — `u`, `groupName`
- [Index.html:1412](apps_script/Index.html#L1412) `deleteKegiatanData('${keg.nama...}')` — interpolasi ke inline `onclick`

**Bukti.** Nilai sel disisipkan apa adanya ke `innerHTML`:
```js
<td class="px-6 py-4 font-semibold text-slate-700">${row[3]}</td>
```
`row[3]` berasal dari input `name="nama"` yang berupa teks bebas. Input `<img src=x onerror="...">` akan dieksekusi setiap admin membuka tabel rekap.

**Perbaikan.** Satu helper `esc()` untuk semua interpolasi ke `innerHTML`, dan hapus inline `onclick` → pasang `data-id` + event listener.

---

## 🟠 Temuan Tinggi

### T-1 · Normalisasi nama OPD menghancurkan data (bug di `checkSpt`)

**Lokasi** [Code.js:61-72](apps_script/Code.js#L61-L72)

```js
.replace(/rumahsakitumumdaerah/g, "rs")
.replace(/rumahsakit/g, "rs")
.replace(/rsud/g, "rs")
.replace(/dan/g, "");   // ← baris 72
```

**Dampak.** `.replace(/dan/g, "")` menghapus kemunculan `"dan"` **di mana pun**, termasuk di dalam kata:
- `"Dinas Pendidikan dan Kebudayaan"` → `dinaspendidikanbudaya`
- `"Badan Perencanaan"` → `baperencanaan`
- `"Badan Perencanaan"` → `baperencanaan` — kata `Badan` ikut terpotong

Dikombinasikan dengan pencocokan longgar (`indexOf !== -1` di [Code.js:91](apps_script/Code.js#L91)), ini menyebabkan **false positive maupun false negative**. Endpoint ini dipakai SIANJAB untuk inquiry apakah suatu OPD sudah mengirim SPT, jadi jawaban yang salah berdampak ke keputusan.

**Perbaikan.** Hapus aturan `/dan/`. Normalisasi yang aman: lowercase + collapse whitespace + trim. Kalau perlu toleransi singkatan, buat **peta alias eksplisit** yang bisa dikelola admin (bukan regex yang menebak). Dan wajib: `exact match` dulu, baru `alias`, baru `contains` sebagai fallback terakhir.

---

### T-2 · Pengecekan NIP di `checkSpt` selalu gagal

**Lokasi**
- [Code.js:284](apps_script/Code.js#L284) & [Code.js:287](apps_script/Code.js#L287) — penyimpanan
- [Code.js:62-64](apps_script/Code.js#L62-L64) — pembacaan

```js
// disimpan:
"'" + data.nip,        // baris 284
// dibaca:
var rowNip = String(values[i][4]).trim();   // → "'198501012015031001"
```

**Penjelasan.** Tanda kutip depan `'` adalah konvensi Sheets **ketika diketik manual di UI**, bukan yang terjadi saat menulis via API. `appendRow()` menyimpan karakter tersebut **literal** di dalam sel. Akibatnya perbandingan `rowNip === nip` membandingkan `"'1985…"` dengan `"1985…"` → **selalu false**.

**Dampak.** Integrasi `checkSpt?nip=…` dari SIANJAB selalu melaporkan `hasSubmitted: false` untuk PNS/PPPK yang sebenarnya sudah mengirim SPT.

**Perbaikan.** Tiga bagian: (a) hentikan menulis prefix `'` di [Code.js:284](apps_script/Code.js#L284) dan [Code.js:287](apps_script/Code.js#L287), gunakan format sel teks (`@`) di kolom NIP; (b) normalisasi pembacaan dengan `.replace(/^'/, "")` agar data lama tetap terbaca; (c) NIP selalu dinormalisasi ke digits-only di kedua sisi.

---

### T-3 · Tidak ada proteksi duplikat & tidak ada locking → data kembar

**Lokasi** [Code.js:262-291](apps_script/Code.js#L262-L291)

Tidak ada `LockService`, tidak ada pengecekan NIP + kegiatan sebelum `appendRow`.

**Dampak.** Dua skenario menghasilkan duplikat:
- Operator menekan "Kirim" dua kali / koneksi lambat → klik ulang.
- `handleFormSubmit` [Index.html:1027-1029](apps_script/Index.html#L1027-L1029) hanya memunculkan spinner; tombol submit tidak dinonaktifkan.

Duplikat juga merusak statistik karena `calculateStats()` [Index.html:1218-1246](apps_script/Index.html#L1218-L1246) sudah menghitung via `Set` NIP, tapi tabel rekap dan baris fisik di Sheet tetap ganda.

**Perbaikan.**
- `LockService.getDocumentLock()` mengelilingi read-check-write (butuh <30 detik, aman untuk kuota).
- Cek duplikat: NIP + kegiatan + tahun yang sama sudah ada → tolak dengan pesan jelas.
- Nonaktifkan tombol submit selama proses; aktifkan lagi di `withFailureHandler`.

---

### T-4 · TTD base64 berisiko melampaui batas sel 50.000 karakter

**Lokasi**
- [Code.js:271](apps_script/Code.js#L271) & [Code.js:290](apps_script/Code.js#L290) — TTD masuk ke Sheet
- [Index.html:432](apps_script/Index.html#L432) — canvas 350×250
- [Code.js:236-249](apps_script/Code.js#L236-L249) — seluruh TTD dikirim ke browser

**Masalah.** `sheet.appendRow` gagal keras jika nilai > 50.000 karakter. PNG 350×250 dengan garis tanda tangan yang rapat bisa menghasilkan base64 40–120 KB. Bila gagal, seluruh baris hilang.

**Dampak ganda.**
1. Kehilangan data (row tidak tersimpan sama sekali).
2. `getSubmissionsData()` mengirim seluruh TTD base64 ke browser padahal **tidak pernah ditampilkan** di tabel rekap. 100 baris = ±10 MB payload, lambat dan boros kuota.

**Perbaikan.**
- Simpan TTD ke Google Drive (folder `TTD/`, nama ber-ID), simpan hanya URL di Sheet. Alternatif: kompres ke JPEG sebelum base64 + potong whitespace.
- `getSubmissionsData()` buang kolom TTD sebelum mengirim ke client.

---

### T-5 · Password admin & token API tersimpan plaintext di source

**Lokasi**
- [Code.js:11](apps_script/Code.js#L11) `ADMIN_PASSWORD = "adminbagor123"`
- [Code.js:39](apps_script/Code.js#L39) `EXPECTED_TOKEN = "sianjab_secure_token_abc123"`
- [Code.js:302](apps_script/Code.js#L302) token yang sama, diulang

**Catatan.** Kode server GAS tidak terekspos ke pengunjung, jadi risiko utamanya adalah kebocoran via repository (repo ini = git repo lokal yang bisa dibagikan). Tapi ada dua masalah nyata: (a) **hardcoded password lemah** — `adminbagor123` akan dihitamkan dalam hitungan detik; (b) **token yang sama dipakai dua konteks** (API publik `doGet` + service-to-service), jadi sekali bocor, keduanya terbuka.

**Perbaikan.** Pindah ke Script Properties (`PropertiesService.getScriptProperties()`), dengan fallback ke konstanta agar deploy lama tidak langsung mati. Pisahkan token API publik vs token service-to-service. Naikkan kompleksitas password (min. 12 karakter).

---

## 🟡 Temuan Sedang

### S-1 · `Config_Kegiatan` bisa rusak: duplikat & hapus parsial

**Lokasi** [Code.js:204-234](apps_script/Code.js#L204-L234)

- `saveKegiatan` hanya `appendRow` → nama kegiatan **boleh dobel**. Dengan nama kembar, `handleKegiatanChange` [Index.html:944](apps_script/Index.html#L944) (`kegiatanDb.find`) selalu ambil yang pertama, dan dropdown menampilkan opsi kembar.
- `deleteKegiatan(nama)` hapus **kemunculan pertama saja** (`break` di baris 226) → sisa baris kembar tinggal.
- Tidak ada validasi nama kosong.

**Perbaikan.** Jadikan `nama` sebagai kunci unik logis: `saveKegiatan` melakukan update-bila-ada (upsert) alih-alih append; `deleteKegiatan` menghapus semua baris dengan nama tersebut; tolak nama kosong.

### S-2 · Deadline adalah fitur mati

**Lokasi** [Index.html:942-965](apps_script/Index.html#L942-L965), [Code.js:262](apps_script/Code.js#L262)

`deadline` tersimpan dan ditampilkan di panel admin, tapi **tidak pernah divalidasi** saat submit — operator tetap bisa mengirim SPT setelah batas tanggal. Modalitas "Tanpa Batas" juga tidakfum distinguishes.

**Perbaikan.** Validasi deadline di **server** (`submitSptData`) sebagai sumber kebenaran; kirim error yang jelas ke UI.

### S-3 · Tidak ada fungsi edit kegiatan, padahal README menjanjikan

**Lokasi** [README.md](apps_script/README.md) bagian "Manajemen Kegiatan" — *"Tambah, **edit** dasar hukum, dan hapus"*

Kode hanya punya `saveKegiatan` (tambah) dan `deleteKegiatan` (hapus). Tidak ada `updateKegiatan` maupun UI edit. Dasar hukum yang salah tidak bisa dikoreksi tanpa hapus-tambah (yang justru menghapus urutan/baris).

**Perbaikan.** Tambahkan `updateKegiatan(namaLama, baru)` + tombol edit di tabel admin, atau koreksi README. Saya rekomendasikan **implementasi** — dasar hukum SPT memang perlu dikoreksi berkali-kali.

### S-4 · Guard "Lainnya" hanya di client, tidak di server

**Lokasi**
- [Index.html:1504-1507](apps_script/Index.html#L1504-L1507) `deleteKegiatanData` menolak hapus "Lainnya"
- [Code.js:219](apps_script/Code.js#L219) `deleteKegiatan` tidak punya guard sama sekali

Proteksi hanya berlaku lewat UI.whoever memanggil `deleteKegiatan("Lainnya")` langsung akan menghapus baris fallback kegiatan — dan karena `handleKegiatanChange` bergantung pada nama literal `"Lainnya"` [Index.html:947](apps_script/Index.html#L947), textarea "Dasar SPT" ikut rusak.

**Perbaikan.** Guard di server. Lebih baik lagi: ganti magic string `"Lainnya"` dengan flag boolean `bolehEditDasar` di sheet — agar nama kegiatan boleh diganti bebas.

### S-5 · Race condition pada `deleteSubmission`

**Lokasi** [Index.html:1345-1364](apps_script/Index.html#L1345-L1364) → [Code.js:251-256](apps_script/Code.js#L251-L256)

`deleteSubmission(rowIndex)` menghapus berdasarkan **nomor baris** yang dihitung client. Bila dua admin menghapus bersamaan (atau ada baris yang terhapus di antara load dan klik), baris yang terhapus ≠ baris yang dituju. Tidak ada ID stabil.

**Perbaikan.** Tambah kolom `ID` (UUID) sebagai kunci baris; `deleteSubmission` mencari berdasarkan ID, bukan index.

### S-6 · Timestamp & tahun disimpan sebagai string

**Lokasi** [Code.js:275-290](apps_script/Code.js#L275-L290)

```js
var now = Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss");  // string
var currentYear = Utilities.formatDate(new Date(), "GMT+7", "yyyy");        // string
```

Akibatnya sorting/filter Sheets memperlakukannya sebagai teks (padahal urutan fortuit kebetulan sama), dan kolom Tahun tidak bisa difilter numerik.

**Perbaikan.** Simpan `new Date()` asli (Sheets otomatis jadi timestamptipe) + `setNumberFormat("@")` bila perlu; formatasi display dilakukan di sisi client.

### S-7 · Nama file DOCX & nama file temp tidak aman

**Lokasi**
- [Code.js:346](apps_script/Code.js#L346) `docName = "Temp_SPT_" + data.nama.replace(/\s+/g, "_") ...`
- [Code.js:419](apps_script/Code.js#L419) `filename: "SPT_" + data.nama.replace(/\s+/g, "_") + ".docx"`

`replace(/\s+/g,"_")` saja tidak mencegah karakter ilegal Drive/Windows (`/ \ : * ? " < > |`). Nama berkas berisi `/` akan membuat `DriveApp.makeCopy` gagal → user kehilangan dokumen **setelah** datanya tersimpan.

**Perbaikan.** Satu helper `safeFilename()` yang menyaring karakter ilegal + batasi panjang. Ini persis kasus "error handling yang mencegah data loss".

---

## 🔵 Temuan Rendah / Kebersihan

| ID | Temuan | Lokasi |
| --- | --- | --- |
| R-1 | `triggerAuthorization()` membuat & menghapus dokumen dummy tiap dipanggil — sisa debugging | [Code.js:14-23](apps_script/Code.js#L14-L23) |
| R-2 | `ADMIN_PASSWORD`, `SPREADSHEET_ID`, `TEMPLATE_DOC_ID`, URL SIANJAB di-hardcode; tokenidecoded URL panjang | [Code.js:4-11](apps_script/Code.js#L4-L11) |
| R-3 | Ekstraksi status PNS/PPPK dari string nama `"(" + status + ") " + nama` lalu `.includes("PNS")` — rapuh | [Code.js:281](apps_script/Code.js#L281), [Index.html:1237-1241](apps_script/Index.html#L1237-L1241) |
| R-4 | `include(filename)` tidak pernah dipakai | [Code.js:128](apps_script/Code.js#L128) |
| R-5 | `.clasp.json` memakai `rootDir` absolut (`/home/falcon/...`) — tidak portabel | [.clasp.json](.clasp.json) |

---

## 📋 Konsistensi Data Antar-Tabel

### Catatan: kolom `NIP Admin` & `NIP Atasan` menyimpan prefix `'` (lihat T-2)

| Lokasi kode | Nilai yang ditulis | Nilai yang dibaca |
| --- | --- | --- |
| [Code.js:284](apps_script/Code.js#L284) | `'198501012015031001` | — |
| [Code.js:287](apps_script/Code.js#L287) | `'197001012005031001` | — |
| [Code.js:62-63](apps_script/Code.js#L62-L63) | — | `String(values[i][4]).trim()` → `'19850101…` |

Semua data lama yang sudah tertulis di Sheet **harus dimigrasi** (buang prefix `'`), bukan cukup dihentikan penulisan barunya.

---

## ✅ Checklist Perbaikan (urutan prioritas)

**P0 — Integrasi SIANJAB benar**
1. [ ] `getUnitKerjaList()` server-side proxy di Code.js, token dari Script Properties, cache 1 jam.
2. [ ] Hapus **seluruh** fallback: `<optgroup>` hardcoded [Index.html:156-250](apps_script/Index.html#L156-L250) dan `masterUnit` [Index.html:716](apps_script/Index.html#L716).
3. [ ] Ganti `masterUnit` di `renderComplianceReport()` dengan data berjenjang dari SIANJAB.
4. [ ] State error eksplisit + tombol Coba Lagi bila SIANJAB tak terjangkau (tidak ada daftar palsu).
5. [ ] Pisahkan token: API publik vs service-to-service.

**P1 — Keamanan**
6. [ ] Session token untuk seluruh fungsi admin; `deleteSubmission` dst. wajib cek.
7. [ ] Helper `esc()` untuk semua interpolasi `innerHTML`; hapus inline `onclick`.
8. [ ] Password admin dipindah ke Script Properties + diperkuat.
9. [ ] TTD keluar dari Sheet → Drive; buang kolom TTD dari `getSubmissionsData()`.

**P2 — Integritas data**
10. [ ] Normalisasi `checkSpt` diperbaiki; NIP digits-only; henti prefix `'`.
11. [ ] Upsert kegiatan + hapus semua duplikat + guard "Lainnya" di server.
12. [ ] `LockService` + deteksi duplikat pada submit; nonaktifkan tombol saat proses.
13. [ ] Kolom `ID` (UUID) sebagai kunci hapus baris.
14. [ ] `safeFilename()` untuk nama file DOCX & temp Drive.

**P3 — Fungsi & kerapian**
15. [ ] Validasi deadline di server.
16. [ ] Fungsi + UI edit kegiatan (atau koreksi README).
17. [ ] Waktu/Tahun jadi tipe Date.
18. [ ] Ganti magic string `"Lainnya"` dengan flag `bolehEditDasar`.
19. [ ] Hapus `triggerAuthorization()` & `include()`; `.clasp.json` relatif.

---

## 💡 Ide Lanjutan

1. **Status sinkronisasi di UI.** Tampilkan badge "SIANJAB tersinkron 14:32 (84 unit)" di header form, plus badge merah bila gagal. Membuat K-1 mustahil terjadi diam-diam lagi.
2. **Kunci integrasi di server, bukan dari client.** `data.integrasi` [Index.html:1022](apps_script/Index.html#L1022) dikirim dari browser dan dipercaya server. Nilai ini bisa dipalsukan. Server harus menentukannya dari `Config_Kegiatan` berdasarkan nama kegiatan.
3. **Alur approval.** Sekarang begitu dikirim, SPT langsung jadi. Untuk SPT rekonfigurasi TPP, perlu alur approval Atasan - Kepala Bagian - Kepala dinas sebelum dokumen final.
4. **Penggantian TTD canvas otomatis pada tanggal.** Bila ada kolom "Berlaku s/d" pada profil atasan, terapkan cache TTD per-atasan per-hari agar form lama tidak perlu diisi ulang.
5. **Idempotency key pada submit.** Kirim UUID dari client; server menolak UUID yang sama — menutup gap antara "gagal render" dan "kirim ulang".
6. **Struktur sheet yang lebih baik.** Pisahkan sheet `Submisi`, `Config_Kegiatan`, dan `Log_Audit`; tambah kolom `ID` + `status_approval` + `created_at` native. Luncurkan dengan `getOrCreateSheet` yang aman.
7. **Halaman status publik.** `/status` yang menampilkan rekap kepatuhan real-time tanpa perlu login admin, berguna untuk memacu pencapaian target pelaporan.

---

*Dokumen ini dibuat sebagai hasil audit baca-kode + uji endpoint. Tidak ada perubahan kode yang dilakukan dalam audit ini.*