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

    const FirebaseService = {
      async getKegiatanList() {
        try {
          const snap = await db.collection('config_kegiatan').get();
          if (snap.empty) {
            const defaults = [
              { nama: "SPT Rekon TPP dan SIMONA", integrasi: "SITPP", status: "Aktif", deadline: "6 Februari 2026", dasar: "Surat Sekretariat Daerah Nomor : 060/   /Org tanggal   2026 perihal SPT Rekon TPP dan SIMONA" }
            ];
            for (const item of defaults) {
              await db.collection('config_kegiatan').doc(item.nama).set(item);
            }
            return defaults;
          }
          const list = [];
          snap.forEach(doc => {
            list.push(doc.data());
          });
          return list;
        } catch(err) {
          console.error("Firestore getKegiatanList error:", err);
          throw err;
        }
      },

      async saveKegiatan(item) {
        await db.collection('config_kegiatan').doc(item.nama).set({
          nama: item.nama,
          integrasi: item.integrasi || "None",
          status: item.status || "Aktif",
          deadline: item.deadline || "Tanpa Batas",
          dasar: item.dasar || "",
          updatedAt: firebase.firestore.FieldValue.serverTimestamp()
        });
        return { success: true };
      },

      async deleteKegiatan(nama) {
        await db.collection('config_kegiatan').doc(nama).delete();
        return { success: true };
      },

      async getSianjabUnitKerja(forceRefresh) {
        const cacheKey = "sianjab_unit_kerja_cache";
        if (!forceRefresh) {
          const cached = localStorage.getItem(cacheKey);
          if (cached) {
            try {
              const parsed = JSON.parse(cached);
              if (parsed && Array.isArray(parsed) && parsed.length > 0) {
                return { success: true, data: parsed, fromCache: true };
              }
            } catch(e) {}
          }
        }
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
          const cached = localStorage.getItem(cacheKey);
          if (cached) {
            return { success: true, data: JSON.parse(cached), fromCache: true };
          }
          return { success: false, error: err.toString() };
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
            "Status Pegawai", "Jabatan Admin", "Pangkat Admin", "No HP Admin", "Unit Kerja ID"
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
              d.unitKerjaId || ""
            ]);
          });
          return rows;
        } catch(err) {
          console.error("Firestore getSubmissionsData error:", err);
          throw err;
        }
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

        // SiTPP RTDB Integration (S-4: hanya jika konfigurasi kegiatan bernilai SITPP)
        let sitppResult = null;
        const isSitpp = data.integrasi === "SITPP";
        if (isSitpp) {
          try {
            const sitppPayload = {
              id: docRef.id,
              waktu: subDoc.waktu,
              tahun: Number(currentYear),
              perihal: subDoc.perihal,
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

        // Pass docId & verification URL to data object so generateSptDocx embeds QR Code verification link
        data.docId = docRef.id;
        data.verify_url = "https://tugasku-bagor.web.app/?v=" + docRef.id;

        // Generate Word DOCX client-side (menggunakan template aktif kustom jika ada)
        if (!window.__activeCustomTemplateBase64) {
          try {
            await FirebaseService.getActiveTemplate();
          } catch(e) {}
        }
        const docxRes = await window.generateSptDocx(data, window.__activeCustomTemplateBase64);

        const result = {
          status: "success",
          docId: docRef.id,
          fileContent: docxRes.fileContent,
          filename: docxRes.filename
        };

        if (sianjabResult && sianjabResult.success) {
          result.sianjabCreated = true;
          result.sianjabStatus = sianjabResult.data ? sianjabResult.data.status : "created";
        }

        if (sitppResult && sitppResult.success) {
          result.sitppEnqueued = true;
        }

        return result;
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
