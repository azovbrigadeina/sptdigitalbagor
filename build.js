const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('[Build] Starting Firebase build process...');

const SRC_FILE = path.join(__dirname, 'apps_script', 'Index.html');
const PUBLIC_DIR = path.join(__dirname, 'public');
const DIST_FILE = path.join(PUBLIC_DIR, 'index.html');
const TEMPLATE_SRC = path.join(__dirname, 'template spt simona.docx');
const TEMPLATE_DEST = path.join(PUBLIC_DIR, 'template_spt_simona.docx');

if (!fs.existsSync(PUBLIC_DIR)) {
  fs.mkdirSync(PUBLIC_DIR, { recursive: true });
}

// 1. Copy template .docx
if (fs.existsSync(TEMPLATE_SRC)) {
  fs.copyFileSync(TEMPLATE_SRC, TEMPLATE_DEST);
  console.log('[Build] Copied template docx to public/template_spt_simona.docx');
} else {
  console.warn('[Build] Warning: template spt simona.docx not found!');
}

// 2. Build docx generator bundle with esbuild
console.log('[Build] Bundling docx generator...');
execSync('npx esbuild src/docx-generator.js --bundle --minify --outfile=public/docx-generator.js --format=iife', { stdio: 'inherit' });

// 3. Read Index.html
let html = fs.readFileSync(SRC_FILE, 'utf8');

// Read SIANJAB unit kerja seed for instant 0ms load
const SIANJAB_SEED_PATH = path.join(__dirname, 'src', 'sianjab-units-seed.json');
const SIANJAB_SEED_JSON = fs.existsSync(SIANJAB_SEED_PATH) ? fs.readFileSync(SIANJAB_SEED_PATH, 'utf8') : '[]';

// Replace GAS template tags and old labels
html = html.replace(/<\?=\s*verifyToken\s*\?>/g, '');
html = html.replace('Data ini akan dihapus secara permanen dari Google Sheets!', 'Data ini akan dihapus secara permanen dari Firebase Database!');

// Firebase SDK & Service Adapter snippet
const firebaseSnippet = `
  <!-- Firebase SDK (v10 compat) -->
  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore-compat.js"></script>
  <script src="/docx-generator.js"></script>

  <script>
  (function() {
    console.log('[Firebase] Initializing Firebase Firestore Client...');
    const firebaseConfig = {
      apiKey: "AIzaSyC5Vxe7wB0Ovvy9YMDnqCRwLwJQzXinpCk",
      authDomain: "tugasku-bagor.firebaseapp.com",
      projectId: "tugasku-bagor",
      storageBucket: "tugasku-bagor.firebasestorage.app",
      messagingSenderId: "259358647157",
      appId: "1:259358647157:web:d76b8822200e5f2f06a93c",
      measurementId: "G-JPS0PR59BH"
    };

    if (!firebase.apps.length) {
      firebase.initializeApp(firebaseConfig);
    }
    const db = firebase.firestore();

    function formatIndoDateTime(d) {
      const pad = n => String(n).padStart(2, '0');
      return \`\${d.getFullYear()}-\${pad(d.getMonth() + 1)}-\${pad(d.getDate())} \${pad(d.getHours())}:\${pad(d.getMinutes())}:\${pad(d.getSeconds())}\`;
    }

    // Kunci normalisasi nomor SPT untuk cek keunikan (abaikan beda huruf besar/kecil & spasi ganda)
    function makeNomorKey(nomor) {
      return String(nomor || '').trim().replace(/\\s+/g, ' ').toUpperCase();
    }

    function parseDeadlineIndo(str) {
      if (!str || typeof str !== 'string' || str === "Tanpa Batas") return null;
      const INDO_MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
      const parts = str.trim().split(/\\s+/);
      if (parts.length === 3) {
        const day = parseInt(parts[0], 10);
        const month = INDO_MONTHS.indexOf(parts[1]);
        const year = parseInt(parts[2], 10);
        if (day && month !== -1 && year) {
          return new Date(year, month, day, 23, 59, 59);
        }
      }
      const iso = new Date(str);
      if (!isNaN(iso.getTime())) {
        return new Date(iso.getFullYear(), iso.getMonth(), iso.getDate(), 23, 59, 59);
      }
      return null;
    }

    const FirebaseService = {
      async getKegiatanList() {
        try {
          const snap = await db.collection('config_kegiatan').get();
          if (snap.empty) {
            const defaults = [
              { 
                nama: "SPT Rekon TPP dan SIMONA", 
                integrasi: "SITPP", 
                status: "Aktif", 
                wajibSpt: true,
                deadline: "6 Februari 2026", 
                dasar: "Surat Sekretariat Daerah Nomor : 060/   /Org tanggal   2026 perihal SPT Rekon TPP dan SIMONA",
                autoNomor: true,
                izinkanNomorManual: true,
                formatNomor: "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}"
              }
            ];
            for (const item of defaults) {
              await db.collection('config_kegiatan').doc(item.nama).set(item);
            }
            return defaults;
          }
          const list = [];
          snap.forEach(doc => {
            const d = doc.data();
            list.push({
              id: doc.id,
              nama: d.nama,
              integrasi: d.integrasi || "None",
              status: d.status || "Aktif",
              wajibSpt: d.wajibSpt !== false,
              deadline: d.deadline || "Tanpa Batas",
              dasar: d.dasar || "",
              autoNomor: d.autoNomor !== false,
              izinkanNomorManual: d.izinkanNomorManual !== false,
              formatNomor: d.formatNomor || "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}"
            });
          });
          return list;
        } catch(err) {
          console.error("Firestore getKegiatanList error:", err);
          throw err;
        }
      },

      async saveKegiatan(item) {
        let targetDocRef = null;
        if (item.id) {
          targetDocRef = db.collection('config_kegiatan').doc(item.id);
        } else {
          const existingSnap = await db.collection('config_kegiatan').where('nama', '==', item.nama).get();
          if (!existingSnap.empty) {
            targetDocRef = existingSnap.docs[0].ref;
          } else {
            targetDocRef = db.collection('config_kegiatan').doc(item.nama);
          }
        }
        await targetDocRef.set({
          nama: item.nama,
          integrasi: item.integrasi || "None",
          status: item.status || "Aktif",
          wajibSpt: item.wajibSpt !== false,
          deadline: item.deadline || "Tanpa Batas",
          dasar: item.dasar || "",
          autoNomor: item.autoNomor !== false,
          izinkanNomorManual: item.izinkanNomorManual !== false,
          formatNomor: item.formatNomor || "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}",
          updatedAt: firebase.firestore.FieldValue.serverTimestamp()
        }, { merge: true });
        return { success: true };
      },

      async deleteKegiatan(nama) {
        const snap = await db.collection('config_kegiatan').where('nama', '==', nama).get();
        const deletePromises = [];
        snap.forEach(d => deletePromises.push(d.ref.delete()));
        deletePromises.push(db.collection('config_kegiatan').doc(nama).delete().catch(() => {}));
        await Promise.all(deletePromises);
        return { success: true };
      },

      async getBrandingConfig() {
        const defaults = {
          appName: "Tugasku",
          reportFooter: "Dihasilkan otomatis melalui Tugasku - Layanan Penugasan, Bagian Organisasi Setda Kab. Muaro Jambi"
        };
        try {
          const snap = await db.collection('config_branding').doc('app').get();
          if (!snap.exists) return defaults;
          const d = snap.data() || {};
          return {
            appName: String(d.appName || '').trim() || defaults.appName,
            reportFooter: String(d.reportFooter || '').trim() || defaults.reportFooter
          };
        } catch(err) {
          console.error("Firestore getBrandingConfig error:", err);
          return defaults;
        }
      },

      async saveBrandingConfig(config) {
        const appName = String((config && config.appName) || '').trim().slice(0, 40);
        const reportFooter = String((config && config.reportFooter) || '').trim().slice(0, 300);
        if (!appName) throw new Error("Nama aplikasi wajib diisi.");
        if (!reportFooter) throw new Error("Teks footer laporan wajib diisi.");
        await db.collection('config_branding').doc('app').set({
          appName: appName,
          reportFooter: reportFooter,
          updatedAt: firebase.firestore.FieldValue.serverTimestamp()
        }, { merge: true });
        return { success: true, appName: appName, reportFooter: reportFooter };
      },

      async getOpdConfigList() {
        try {
          const snap = await db.collection('config_opd').get();
          const list = [];
          snap.forEach(doc => {
            const d = doc.data();
            list.push({
              id: doc.id,
              nama: d.nama || "",
              kodeSianjab: d.kodeSianjab || "",
              kodeCustom: d.kodeCustom || "",
              updatedAt: d.updatedAt ? d.updatedAt.toDate().toLocaleString('id-ID') : ""
            });
          });
          return list;
        } catch(err) {
          console.error("Firestore getOpdConfigList error:", err);
          return [];
        }
      },

      async saveOpdConfig(items) {
        try {
          const arr = Array.isArray(items) ? items : [items];
          const batch = db.batch();
          arr.forEach(item => {
            const docId = String(item.id || item.nama || '').trim();
            if (!docId) return;
            const ref = db.collection('config_opd').doc(docId);
            batch.set(ref, {
              id: item.id || docId,
              nama: item.nama || "",
              kodeSianjab: item.kodeSianjab || "",
              kodeCustom: item.kodeCustom || "",
              updatedAt: firebase.firestore.FieldValue.serverTimestamp()
            }, { merge: true });
          });
          await batch.commit();
          return { success: true };
        } catch(err) {
          console.error("Firestore saveOpdConfig error:", err);
          throw err;
        }
      },

      async getSianjabUnitKerja(forceRefresh) {
        const cacheKey = "sianjab_unit_kerja_cache";
        const seedUnits = ${SIANJAB_SEED_JSON};

        if (!forceRefresh) {
          const cached = localStorage.getItem(cacheKey);
          if (cached) {
            try {
              const parsed = JSON.parse(cached);
              if (parsed && Array.isArray(parsed) && parsed.length > 0) {
                // Return cache immediately (0ms!) & update in background
                this.syncSianjabInBackground(cacheKey);
                return { success: true, data: parsed, fromCache: true };
              }
            } catch(e) {}
          } else if (seedUnits && seedUnits.length > 0) {
            // No cache yet: use seed data immediately (0ms!)
            localStorage.setItem(cacheKey, JSON.stringify(seedUnits));
            this.syncSianjabInBackground(cacheKey);
            return { success: true, data: seedUnits, fromCache: true, fromSeed: true };
          }
        }
        return this.fetchSianjabDirect(cacheKey, seedUnits);
      },

      async syncSianjabInBackground(cacheKey) {
        try {
          const resp = await fetch("https://script.google.com/macros/s/AKfycbxbuHWzaPOMyEemDcUsYCboqWkE5g1Lq-FFKwA5eNyBbamd41686X1a2m7OIFI-h-yLWw/exec?action=getBulkData&entities=unitKerja");
          const json = await resp.json();
          if (json && json.success && json.data) {
            const list = Array.isArray(json.data.unitKerja) ? json.data.unitKerja : (Array.isArray(json.data) ? json.data : []);
            if (list.length > 0) {
              localStorage.setItem(cacheKey, JSON.stringify(list));
              if (window.sianjabUnits && window.sianjabUnits.length !== list.length) {
                window.sianjabUnits = list;
                if (typeof renderAttendanceStatsAndAbsentOpd === 'function') renderAttendanceStatsAndAbsentOpd();
                if (typeof renderComplianceReport === 'function') renderComplianceReport();
                if (typeof renderSptComplianceReport === 'function') renderSptComplianceReport();
              }
            }
          }
        } catch(e) {
          console.warn("Background SI-PRABU sync note:", e);
        }
      },

      async fetchSianjabDirect(cacheKey, seedUnits) {
        try {
          const resp = await fetch("https://script.google.com/macros/s/AKfycbxbuHWzaPOMyEemDcUsYCboqWkE5g1Lq-FFKwA5eNyBbamd41686X1a2m7OIFI-h-yLWw/exec?action=getBulkData&entities=unitKerja");
          const json = await resp.json();
          if (json && json.success && json.data) {
            const list = Array.isArray(json.data.unitKerja) ? json.data.unitKerja : (Array.isArray(json.data) ? json.data : []);
            localStorage.setItem(cacheKey, JSON.stringify(list));
            return { success: true, data: list };
          }
          throw new Error((json && json.error) || "Gagal memuat data SI-PRABU");
        } catch(err) {
          console.warn("Direct SI-PRABU fetch warning:", err);
          if (seedUnits && seedUnits.length > 0) {
            return { success: true, data: seedUnits, fromSeed: true };
          }
          return { success: false, error: err.toString() };
        }
      },

      async getMonitoringExclusions() {
        try {
          const doc = await db.collection('config_monitoring').doc('excluded_units').get();
          if (!doc.exists) return [];
          const data = doc.data() || {};
          return Array.isArray(data.keys) ? data.keys : [];
        } catch (err) {
          console.warn("Firestore getMonitoringExclusions error:", err);
          throw err;
        }
      },

      async saveMonitoringExclusions(keys) {
        try {
          await db.collection('config_monitoring').doc('excluded_units').set({
            keys: Array.isArray(keys) ? keys : [],
            updatedAt: firebase.firestore.FieldValue.serverTimestamp()
          }, { merge: true });
          return { success: true };
        } catch (err) {
          console.error("Firestore saveMonitoringExclusions error:", err);
          throw err;
        }
      },

      async checkAdminAuth(password) {
        return password === "adminbagor123";
      },

      async getActiveTemplate() {
        try {
          const doc = await db.collection('config_templates').doc('active_spt').get();
          if (doc.exists) {
            const data = doc.data();
            if (data && data.contentBase64) {
              window.__activeCustomTemplateBase64 = data.contentBase64;
              return {
                exists: true,
                filename: data.filename || "template_custom.docx",
                fileSize: data.fileSize || 0,
                updatedAt: data.updatedAt ? data.updatedAt.toDate().toLocaleString('id-ID') : "",
                contentBase64: data.contentBase64
              };
            }
          }
          window.__activeCustomTemplateBase64 = null;
          return { exists: false };
        } catch(err) {
          console.warn("Firestore getActiveTemplate error:", err);
          return { exists: false, error: err.toString() };
        }
      },

      async saveActiveTemplate(templateData) {
        try {
          if (!templateData || !templateData.contentBase64) {
            throw new Error("Data template tidak valid atau kosong.");
          }
          await db.collection('config_templates').doc('active_spt').set({
            filename: templateData.filename || "template_spt.docx",
            fileSize: templateData.fileSize || 0,
            contentBase64: templateData.contentBase64,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp()
          });
          window.__activeCustomTemplateBase64 = templateData.contentBase64;
          return { success: true };
        } catch(err) {
          console.error("Firestore saveActiveTemplate error:", err);
          throw err;
        }
      },

      async resetActiveTemplate() {
        try {
          await db.collection('config_templates').doc('active_spt').delete();
          window.__activeCustomTemplateBase64 = null;
          return { success: true };
        } catch(err) {
          console.error("Firestore resetActiveTemplate error:", err);
          throw err;
        }
      },

      async getSubmissionsData() {
        try {
          const snap = await db.collection('submissions').orderBy('createdAt', 'desc').get();
          const headers = [
            "Waktu", "Perihal", "Unit Kerja", "Nama Admin", "NIP Admin",
            "Email", "Nama Atasan", "Jabatan Atasan", "Pangkat Gol Atasan",
            "NIP Atasan", "TTD", "Integrasi", "Tahun", "DocId",
            "Status Pegawai", "Jabatan Admin", "Pangkat Admin", "No HP Admin", "Unit Kerja ID",
            "Nomor SPT", "Nomor Urut", "Kode OPD", "Mode Nomor"
          ];
          const rows = [headers];
          snap.forEach(doc => {
            const d = doc.data();
            rows.push([
              d.waktu || "",
              d.perihal || "",
              d.unitKerja || "",
              d.namaAdmin || "",
              d.nipAdmin || "",
              d.email || "",
              d.namaAtasan || "",
              d.jabatanAtasan || "",
              d.pangkatGolAtasan || "",
              d.nipAtasan || "",
              "", // S-6: TTD dikosongkan dari payload tabel & CSV agar ringan & tidak merusak file
              d.integrasi || "",
              d.tahun || "",
              doc.id,
              d.statusPegawai || "",
              d.jabatanAdmin || d.jabatan || "",
              d.pangkatAdmin || d.pangkat || "",
              d.noHpAdmin || d.no_hp || "",
              d.unitKerjaId || "",
              d.nomorSpt || d.nomor_spt || "",
              d.nomorUrut || d.nomor_urut || "",
              d.kodeOpd || d.kode_opd || "",
              d.nomorMode || "auto"
            ]);
          });
          return rows;
        } catch(err) {
          console.error("Firestore getSubmissionsData error:", err);
          throw err;
        }
      },

      // Perbaikan unit kerja yang salah input pada submisi.
      // Hanya dua field unit yang diubah; data presensi yang tertaut ikut disinkronkan.
      async updateSubmissionUnit(docId, unitKerja, unitKerjaId) {
        const targetDocId = String(docId || '').trim();
        const newUnit = String(unitKerja || '').trim();
        const newUnitId = String(unitKerjaId || '').trim();

        if (!targetDocId) {
          throw new Error('ID dokumen submisi tidak ditemukan. Silakan refresh halaman dan coba lagi.');
        }
        if (!newUnit) {
          throw new Error('Unit kerja baru wajib dipilih.');
        }

        await db.collection('submissions').doc(targetDocId).update({
          unitKerja: newUnit,
          unitKerjaId: newUnitId
        });

        let presensiUpdated = 0;
        let presensiWarning = '';
        try {
          const presensiSnap = await db.collection('presensi_kegiatan')
            .where('submissionId', '==', targetDocId)
            .get();
          if (!presensiSnap.empty) {
            const batch = db.batch();
            presensiSnap.forEach(doc => {
              batch.update(doc.ref, { opd: newUnit, opdId: newUnitId });
            });
            await batch.commit();
            presensiUpdated = presensiSnap.size;
          }
        } catch (presensiErr) {
          console.warn('[Firebase] Unit submisi tersimpan, tetapi presensi tertaut gagal diperbarui:', presensiErr);
          presensiWarning = 'Data presensi tertaut belum ikut diperbarui. Periksa izin Firestore lalu coba lagi.';
        }

        return { success: true, presensiUpdated: presensiUpdated, presensiWarning: presensiWarning };
      },

      async deleteSubmission(rowIndexOrId, docId) {
        let targetDocId = null;

        if (typeof docId === 'string' && docId.trim()) {
          targetDocId = docId.trim();
        } else if (typeof rowIndexOrId === 'string' && isNaN(Number(rowIndexOrId)) && rowIndexOrId.trim()) {
          targetDocId = rowIndexOrId.trim();
        } else {
          const idx = Number(rowIndexOrId);
          const list = window.submissionsDb || (typeof submissionsDb !== 'undefined' ? submissionsDb : null);
          if (list && list[idx] && list[idx][13]) {
            targetDocId = list[idx][13];
          }
        }

        if (!targetDocId) {
          console.error("Gagal menghapus submisi: ID dokumen tidak ditemukan", { rowIndexOrId, docId });
          throw new Error("ID dokumen submisi tidak ditemukan. Silakan refresh halaman dan coba lagi.");
        }

        console.log('[Firebase] Deleting submission document:', targetDocId);
        await db.collection('submissions').doc(targetDocId).delete();
        return { success: true };
      },

      async submitSptData(data) {
        const now = new Date();
        const currentYear = Number(data.tahun || now.getFullYear());

        // Ambil konfigurasi kegiatan (B-5: support doc-ID acak via query nama)
        let kegData = null;
        if (data.perihal) {
          try {
            const kegSnap = await db.collection('config_kegiatan')
              .where('nama', '==', String(data.perihal).trim())
              .get();
            if (!kegSnap.empty) {
              kegData = kegSnap.docs[0].data();
            } else {
              const fallbackDoc = await db.collection('config_kegiatan').doc(data.perihal).get();
              if (fallbackDoc.exists) kegData = fallbackDoc.data();
            }
          } catch(e) {
            console.warn("Gagal mengambil config_kegiatan:", e);
          }
        }

        // B-7: Validasi deadline kegiatan
        if (kegData && kegData.deadline && kegData.deadline !== "Tanpa Batas") {
          const deadlineDate = parseDeadlineIndo(kegData.deadline);
          if (deadlineDate && now > deadlineDate) {
            throw new Error("Batas waktu (deadline) pengiriman SPT untuk kegiatan \\"" + (data.perihal || "") + "\\" telah berakhir pada " + kegData.deadline + ".");
          }
        }

        // S-8: Cek duplikasi pengajuan berdasarkan NIP + Perihal/Kegiatan di tahun berjalan
        if (data.nip && data.perihal) {
          try {
            const dupSnap = await db.collection('submissions')
              .where('nipAdmin', '==', String(data.nip).trim())
              .where('perihal', '==', String(data.perihal).trim())
              .get();
            
            if (!dupSnap.empty) {
              const alreadyExists = dupSnap.docs.some(d => {
                const docYear = d.data().tahun ? Number(d.data().tahun) : null;
                return !docYear || docYear === currentYear;
              });
              if (alreadyExists) {
                throw new Error("Data SPT untuk NIP " + data.nip + ' dengan kegiatan "' + data.perihal + '" sudah pernah dikirim.');
              }
            }
          } catch(dupErr) {
            if (dupErr.message && dupErr.message.includes("sudah pernah dikirim")) {
              throw dupErr;
            }
            console.warn("Pemeriksaan duplikasi dilewati karena error kueri:", dupErr);
          }
        }

        // 1. Hitung nomor urut pendaftaran per kegiatan (FCFS) diskop tahun
        let countPerihal = 0;
        try {
          const countSnap = await db.collection('submissions')
            .where('perihal', '==', String(data.perihal).trim())
            .get();
          const sameYearDocs = countSnap.docs.filter(d => {
            const docYear = d.data().tahun ? Number(d.data().tahun) : null;
            const isManual = d.data().nomorMode === 'manual';
            // Nomor manual tidak mengonsumsi urutan otomatis agar deret nomor sistem tetap rapat
            return !isManual && (!docYear || docYear === currentYear);
          });
          countPerihal = sameYearDocs.length;
        } catch(e) {
          console.warn("Gagal menghitung nomor urut pendaftaran:", e);
        }
        const nomorUrutPad = String(countPerihal + 1).padStart(3, '0');

        // 2. Tentukan Kode OPD (Hybrid: Config_OPD custom override -> SIANJAB)
        let kodeOpd = data.kode_opd || "";
        if (!kodeOpd) {
          try {
            const opdSnap = await db.collection('config_opd').get();
            opdSnap.forEach(doc => {
              const d = doc.data();
              if ((data.unit_kerja_id && d.id === data.unit_kerja_id) || 
                  (data.unit_kerja && (d.nama === data.unit_kerja || d.id === data.unit_kerja))) {
                if (d.kodeCustom && d.kodeCustom.trim()) kodeOpd = d.kodeCustom.trim();
                else if (d.kodeSianjab && d.kodeSianjab.trim()) kodeOpd = d.kodeSianjab.trim();
              }
            });
          } catch(e) {}
        }
        if (!kodeOpd && window.sianjabUnits && Array.isArray(window.sianjabUnits)) {
          let target = window.sianjabUnits.find(u => u.nama === data.unit_kerja || u.id === data.unit_kerja_id);
          let depth = 0;
          while (target && target.parentId && depth < 5) {
            const parent = window.sianjabUnits.find(u => u.id === target.parentId || u.nama === target.parentId);
            if (!parent) break;
            target = parent;
            depth++;
          }
          if (target && target.kode) kodeOpd = target.kode;
        }
        if (!kodeOpd) kodeOpd = "OPD";

        // 3. Konfigurasi Penomoran Kegiatan (dari kegData yang sudah diambil di awal)
        //    - kegData.autoNomor === false           -> WAJIB manual (nomor dari pengirim)
        //    - kegData.izinkanNomorManual === false  -> WAJIB otomatis sistem (permintaan manual diabaikan)
        //    - selain itu pengirim boleh memilih lewat field "nomor_mode" (default otomatis)
        let formatTemplate = "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}";
        if (kegData && kegData.formatNomor) formatTemplate = kegData.formatNomor;

        const wajibManual = !!(kegData && kegData.autoNomor === false);
        const bolehManual = !kegData || kegData.izinkanNomorManual !== false;
        const mintaManual = String(data.nomor_mode || "").toLowerCase() === "manual";
        // Mode wajib dipilih eksplisit saat pengirim punya pilihan (cegah kirim tanpa sadar).
        // Kegiatan yang mengunci modenya sendiri tidak diwajibkan mengirim field ini.
        if (!wajibManual && bolehManual && !String(data.nomor_mode || "").trim()) {
          throw new Error("Mode penomoran SPT wajib dipilih: Otomatis (Sistem) atau Nomor Instansi Sendiri.");
        }
        const pakaiManual = wajibManual || (mintaManual && bolehManual);

        let nomorSpt = "";
        if (pakaiManual) {
          nomorSpt = String(data.nomor_spt || "").trim();
          if (!nomorSpt) {
            throw new Error("Nomor SPT/agenda wajib diisi karena penomoran manual dipilih. Isi nomor instansi Anda atau pilih mode Otomatis (Sistem).");
          }
        } else {
          nomorSpt = formatTemplate
            .replace(/{nomor}/g, nomorUrutPad)
            .replace(/{kode_opd}/g, kodeOpd)
            .replace(/{tahun}/g, String(currentYear));
        }

        const nomorSptKey = makeNomorKey(nomorSpt);

        // Nomor manual wajib unik per tahun agar tidak bentrok nomor resmi antar pengajuan.
        // ponytail: cek ini read-then-write, bukan transaction — dua kiriman paralel dengan nomor
        // identik masih bisa lolos. Ceiling: volume SPT manual per tahun rendah.
        // Upgrade path: registry {tahun}_{nomorSptKey} + db.runTransaction.
        if (pakaiManual) {
          let usedSnap;
          try {
            usedSnap = await db.collection('submissions').where('nomorSptKey', '==', nomorSptKey).get();
          } catch (cekErr) {
            console.warn("Gagal memeriksa keunikan nomor manual:", cekErr);
            throw new Error("Gagal memverifikasi keunikan nomor SPT manual. Silakan coba kirim ulang.");
          }
          const bentrok = usedSnap.docs.some(d => {
            const dd = d.data();
            const docYear = dd.tahun ? Number(dd.tahun) : null;
            return !docYear || docYear === currentYear;
          });
          if (bentrok) {
            throw new Error('Nomor SPT "' + nomorSpt + '" sudah dipakai pada pengajuan lain tahun ' + currentYear + '. Gunakan nomor agenda lain atau pilih mode Otomatis (Sistem).');
          }
        }

        data.nomor_spt = nomorSpt;
        data.nomor_mode = pakaiManual ? "manual" : "auto";
        data.nomor_urut = nomorUrutPad;
        data.kode_opd = kodeOpd;
        data.tahun = currentYear;

        const subDoc = {
          waktu: formatIndoDateTime(now),
          perihal: data.perihal || "",
          unitKerja: data.unit_kerja || "",
          unitKerjaId: data.unit_kerja_id || "",
          namaAdmin: data.nama || "",
          nipAdmin: data.nip || "",
          statusPegawai: data.status_pegawai || "",
          pangkatAdmin: data.pangkat || "",
          jabatanAdmin: data.jabatan || "",
          noHpAdmin: data.no_hp || "",
          email: data.email || "",
          namaAtasan: data.n_atasan || "",
          jabatanAtasan: data.j_atasan || "",
          pangkatGolAtasan: data.p_atasan || "",
          nipAtasan: data.nip_atasan || "",
          ttd: data.signature_data || "",
          integrasi: data.integrasi || "None",
          tahun: currentYear,
          nomorSpt: nomorSpt,
          nomorSptKey: nomorSptKey,
          nomorUrut: nomorUrutPad,
          nomorMode: data.nomor_mode,
          kodeOpd: kodeOpd,
          createdAt: firebase.firestore.FieldValue.serverTimestamp()
        };

        const docRef = await db.collection('submissions').add(subDoc);

        // SI-PRABU webhook
        let sianjabResult = null;
        if (data.integrasi === "SI-PRABU" || !data.integrasi) {
          try {
            const resp = await fetch("https://script.google.com/macros/s/AKfycbxbuHWzaPOMyEemDcUsYCboqWkE5g1Lq-FFKwA5eNyBbamd41686X1a2m7OIFI-h-yLWw/exec?action=autoRegisterOperator", {
              method: "POST",
              headers: { "Content-Type": "text/plain" },
              body: JSON.stringify({
                nip: data.nip,
                nama: data.nama,
                email: data.email,
                opdName: data.unit_kerja,
                token: "sianjab_secure_token_abc123"
              })
            });
            sianjabResult = await resp.json();
          } catch(err) {
            console.warn("SI-PRABU auto-register warning:", err);
          }
        }

        // Gentala TPP EM-JE (SiTPP) RTDB Integration (S-4: jika konfigurasi kegiatan bernilai SITPP atau Gentala TPP EM-JE)
        let sitppResult = null;
        const isSitpp = data.integrasi === "SITPP" || data.integrasi === "Gentala TPP EM-JE";
        if (isSitpp) {
          try {
            const sitppPayload = {
              id: docRef.id,
              waktu: subDoc.waktu,
              tahun: Number(currentYear),
              perihal: subDoc.perihal,
              nomorSpt: nomorSpt,
              opdId: data.unit_kerja_id || data.opd_id || subDoc.unitKerja || "",
              unitKerja: subDoc.unitKerja,
              namaAdmin: subDoc.namaAdmin,
              nipAdmin: subDoc.nipAdmin,
              statusPegawai: subDoc.statusPegawai,
              email: subDoc.email,
              namaAtasan: subDoc.namaAtasan,
              jabatanAtasan: subDoc.jabatanAtasan,
              pangkatGolAtasan: subDoc.pangkatGolAtasan,
              nipAtasan: subDoc.nipAtasan,
              ttd: subDoc.ttd,
              statusApproval: "PENDING",
              approvalHistory: {
                submittedAt: Date.now(),
                reviewedAt: null,
                reviewedBy: null,
                reviewNotes: ""
              },
              source: "sptdigitalbagor"
            };

            const rtdbUrl = "https://sitpp-7b65d-default-rtdb.asia-southeast1.firebasedatabase.app/spt_approvals/" + currentYear + "/" + docRef.id + ".json";
            const rtdbResp = await fetch(rtdbUrl, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(sitppPayload)
            });
            if (rtdbResp.ok) {
              sitppResult = { success: true };
              console.log("[SiTPP] Successfully pushed submission to SiTPP RTDB:", docRef.id);
            } else {
              const rtdbErr = await rtdbResp.text();
              console.warn("[SiTPP] RTDB push warning:", rtdbResp.status, rtdbErr);
            }
          } catch(err) {
            console.warn("SiTPP RTDB integration error:", err);
          }
        }

        // Pass docId & verification URL to data object so generator embeds QR Code verification link
        data.docId = docRef.id;
        data.verify_url = "https://tugasku-bagor.web.app/?v=" + docRef.id;

        // Pastikan active template dari Firestore termuat
        if (!window.__activeCustomTemplateBase64 && typeof FirebaseService !== 'undefined' && FirebaseService.getActiveTemplate) {
          try {
            await FirebaseService.getActiveTemplate();
          } catch(e) {}
        }

        // Generate PDF client-side strictly dari template aktif
        let fileContent = "";
        let filename = "Surat_Tugas_" + (data.nama || "Dokumen").replace(/\s+/g, "_") + ".pdf";

        if (typeof window.generateSptPdf === 'function') {
          const pdfRes = await window.generateSptPdf(data, window.__activeCustomTemplateBase64);
          fileContent = pdfRes.fileContent;
          filename = pdfRes.filename;
        } else {
          const docxRes = await window.generateSptDocx(data, window.__activeCustomTemplateBase64);
          fileContent = docxRes.fileContent;
          filename = docxRes.filename;
        }

        const result = {
          status: "success",
          docId: docRef.id,
          nomor_spt: nomorSpt,
          nomor_mode: data.nomor_mode,
          nomor_urut: nomorUrutPad,
          kode_opd: kodeOpd,
          fileContent: fileContent,
          filename: filename
        };

        if (sianjabResult && sianjabResult.success) {
          result.sianjabCreated = true;
          result.sianjabStatus = sianjabResult.data ? sianjabResult.data.status : "created";
        }

        if (sitppResult && sitppResult.success) {
          result.sitppEnqueued = true;
        }

        return result;
      },

      async checkAttendance(kegiatan, nip) {
        try {
          if (!kegiatan || !nip) {
            return { success: false, reason: "INVALID_INPUT", message: "Kegiatan dan NIP wajib diisi." };
          }
          const cleanNip = String(nip).trim();
          const cleanKegiatan = String(kegiatan).trim();

          // 1. Cek keberadaan SPT di koleksi submissions
          const snap = await db.collection('submissions')
            .where('perihal', '==', cleanKegiatan)
            .get();

          let matchedSub = null;
          snap.forEach(doc => {
            const d = doc.data();
            const subNip = String(d.nipAdmin || d.nip || '').trim();
            if (subNip === cleanNip) {
              matchedSub = { id: doc.id, ...d };
            }
          });

          if (!matchedSub) {
            return { 
              success: false, 
              reason: "SPT_NOT_FOUND", 
              message: "NIP " + cleanNip + ' belum terdaftar mengirimkan Surat Perintah Tugas (SPT) untuk kegiatan "' + cleanKegiatan + '".' 
            };
          }

          // 2. Cek apakah sudah pernah presensi di presensi_kegiatan
          const presensiId = encodeURIComponent(cleanKegiatan).replace(/%/g, '_') + "_" + cleanNip;
          const presensiRef = db.collection('presensi_kegiatan').doc(presensiId);
          const presensiSnap = await presensiRef.get();

          if (presensiSnap.exists) {
            return {
              success: true,
              alreadyCheckedIn: true,
              data: presensiSnap.data(),
              message: "Peserta sudah tercatat hadir sebelumnya."
            };
          }

          // 3. Simpan presensi baru
          const newPresensi = {
            id: presensiId,
            kegiatan: cleanKegiatan,
            nip: cleanNip,
            nama: matchedSub.namaAdmin || matchedSub.nama || "",
            opd: matchedSub.unitKerja || matchedSub.unit_kerja || "",
            opdId: matchedSub.unitKerjaId || matchedSub.opdId || "",
            jabatan: matchedSub.jabatanAdmin || matchedSub.jabatan || "",
            statusPegawai: matchedSub.statusPegawai || "",
            submissionId: matchedSub.id,
            nomorSpt: matchedSub.nomorSpt || matchedSub.nomor_spt || "-",
            statusKehadiran: "sah",
            waktuCheckIn: formatIndoDateTime(new Date()),
            createdAt: firebase.firestore.FieldValue.serverTimestamp(),
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
            source: "web_presensi"
          };

          await presensiRef.set(newPresensi);

          return {
            success: true,
            alreadyCheckedIn: false,
            data: newPresensi,
            message: "Presensi berhasil dikonfirmasi!"
          };
        } catch(err) {
          console.error("Firebase checkAttendance error:", err);
          return { success: false, reason: "ERROR", message: err.message || err.toString() };
        }
      },

      // Presensi mandiri untuk kegiatan non SPT (tanpa prasyarat SPT).
      // Data diisi sendiri oleh peserta, sehingga tidak ada pembacaan ke koleksi submissions.
      async checkAttendanceMandiri(data) {
        try {
          const payload = data || {};
          const cleanKegiatan = String(payload.kegiatan || '').trim();
          const cleanNip = String(payload.nip || '').replace(/[^0-9]/g, '');
          const nama = String(payload.nama || '').trim();
          const opd = String(payload.opd || '').trim();
          const jabatan = String(payload.jabatan || '').trim();

          if (!cleanKegiatan || !nama || !opd || !jabatan || cleanNip.length !== 18) {
            return {
              success: false,
              reason: "INVALID_INPUT",
              message: "Data kehadiran belum lengkap atau NIP bukan 18 digit."
            };
          }

          const presensiId = encodeURIComponent(cleanKegiatan).replace(/%/g, '_') + "_" + cleanNip;
          const presensiRef = db.collection('presensi_kegiatan').doc(presensiId);
          const presensiSnap = await presensiRef.get();

          if (presensiSnap.exists) {
            return {
              success: true,
              alreadyCheckedIn: true,
              data: presensiSnap.data(),
              message: "Peserta sudah tercatat hadir sebelumnya."
            };
          }

          const newPresensi = {
            id: presensiId,
            kegiatan: cleanKegiatan,
            jenisKehadiran: "mandiri",
            nip: cleanNip,
            nama: nama,
            opd: opd,
            opdId: String(payload.opdId || "").trim(),
            jabatan: jabatan,
            pangkat: String(payload.pangkat || "").trim(),
            statusPegawai: String(payload.statusPegawai || "").trim(),
            noHp: String(payload.noHp || "").trim(),
            email: String(payload.email || "").trim(),
            submissionId: null,
            nomorSpt: "-",
            statusKehadiran: "sah",
            waktuCheckIn: formatIndoDateTime(new Date()),
            createdAt: firebase.firestore.FieldValue.serverTimestamp(),
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
            source: "web_presensi_mandiri"
          };

          await presensiRef.set(newPresensi);

          return {
            success: true,
            alreadyCheckedIn: false,
            data: newPresensi,
            message: "Kehadiran berhasil dicatat."
          };
        } catch(err) {
          console.error("Firebase checkAttendanceMandiri error:", err);
          return { success: false, reason: "ERROR", message: err.message || err.toString() };
        }
      },

      async getAttendanceList(kegiatan) {
        try {
          let ref = db.collection('presensi_kegiatan');
          if (kegiatan && kegiatan !== "Semua Kegiatan") {
            ref = ref.where('kegiatan', '==', String(kegiatan).trim());
          }
          const snap = await ref.get();
          const list = [];
          snap.forEach(doc => {
            list.push(doc.data());
          });
          // Sort by waktuCheckIn descending
          list.sort((a, b) => (b.waktuCheckIn || '').localeCompare(a.waktuCheckIn || ''));
          return list;
        } catch(err) {
          console.error("Firebase getAttendanceList error:", err);
          return [];
        }
      },

      async deleteAttendance(id) {
        try {
          await db.collection('presensi_kegiatan').doc(id).delete();
          return { success: true };
        } catch(err) {
          console.error("Firebase deleteAttendance error:", err);
          return { success: false, error: err.toString() };
        }
      },

      // Koreksi/pembatalan catatan kehadiran. Dokumen tidak dihapus agar jejak tetap ada.
      async updateAttendance(id, changes) {
        try {
          if (!id) return { success: false, message: "ID kehadiran tidak valid." };
          const data = changes || {};
          const patch = {
            updatedAt: firebase.firestore.FieldValue.serverTimestamp()
          };
          ["nama", "pangkat", "jabatan", "opd", "opdId", "noHp", "email"].forEach(function(field) {
            if (data[field] !== undefined && data[field] !== null) {
              patch[field] = String(data[field]).trim();
            }
          });
          if (data.statusKehadiran === "sah" || data.statusKehadiran === "dibatalkan") {
            patch.statusKehadiran = data.statusKehadiran;
          }
          await db.collection('presensi_kegiatan').doc(id).update(patch);
          return { success: true };
        } catch(err) {
          console.error("Firebase updateAttendance error:", err);
          return { success: false, message: err.message || err.toString() };
        }
      }
    };

    window.google = window.google || {};
    window.google.script = window.google.script || {};
    window.google.script.run = (function createRunner(succ, fail) {
      return new Proxy({}, {
        get(target, prop) {
          if (prop === 'withSuccessHandler') {
            return function(h) { return createRunner(h, fail); };
          }
          if (prop === 'withFailureHandler') {
            return function(h) { return createRunner(succ, h); };
          }
          return async function(...args) {
            try {
              if (typeof FirebaseService[prop] === 'function') {
                const res = await FirebaseService[prop](...args);
                if (succ) succ(res);
                return res;
              } else {
                throw new Error('Metode ' + prop + ' tidak ditemukan di FirebaseService.');
              }
            } catch(err) {
              console.error('Firebase error on ' + prop + ':', err);
              if (fail) fail(err);
            }
          };
        }
      });
    })(null, null);

    window.db = db;
    window.FirebaseService = FirebaseService;
  })();
  </script>
`;

const insertTarget = '<!-- ========================================================= -->\n  <!-- CLIENT JS SCRIPT LOGIC';
if (html.includes(insertTarget)) {
  html = html.replace(insertTarget, `${firebaseSnippet}\n  ${insertTarget}`);
} else {
  html = html.replace('</body>', `${firebaseSnippet}\n</body>`);
}

fs.writeFileSync(DIST_FILE, html, 'utf8');
console.log(`[Build] Successfully compiled to ${DIST_FILE}! (${fs.statSync(DIST_FILE).size} bytes)`);

// 4. Compile Presensi.html
const PRESENSI_SRC = path.join(__dirname, 'apps_script', 'Presensi.html');
const PRESENSI_DIST = path.join(PUBLIC_DIR, 'presensi.html');

if (fs.existsSync(PRESENSI_SRC)) {
  let presensiHtml = fs.readFileSync(PRESENSI_SRC, 'utf8');
  if (presensiHtml.includes('<!-- FIREBASE_SNIPPET -->')) {
    presensiHtml = presensiHtml.replace('<!-- FIREBASE_SNIPPET -->', firebaseSnippet);
  } else if (presensiHtml.includes('</body>')) {
    presensiHtml = presensiHtml.replace('</body>', `${firebaseSnippet}\n</body>`);
  }
  fs.writeFileSync(PRESENSI_DIST, presensiHtml, 'utf8');
  console.log(`[Build] Successfully compiled to ${PRESENSI_DIST}! (${fs.statSync(PRESENSI_DIST).size} bytes)`);
}
