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
              { nama: "SPT Rekon TPP dan SIMONA", integrasi: "SITPP", status: "Aktif", deadline: "6 Februari 2026", dasar: "Surat Sekretariat Daerah Nomor : 060/   /Org tanggal   2026 perihal SPT Rekon TPP dan SIMONA" },
              { nama: "Lainnya", integrasi: "None", status: "Aktif", deadline: "Tanpa Batas", dasar: "" }
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

      async getSubmissionsData() {
        try {
          const snap = await db.collection('submissions').orderBy('createdAt', 'desc').get();
          const headers = [
            "Waktu", "Perihal", "Unit Kerja", "Nama Admin", "NIP Admin",
            "Email", "Nama Atasan", "Jabatan Atasan", "Pangkat Gol Atasan",
            "NIP Atasan", "TTD", "Integrasi", "Tahun", "DocId"
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
              d.ttd || "",
              d.integrasi || "",
              d.tahun || "",
              doc.id
            ]);
          });
          return rows;
        } catch(err) {
          console.error("Firestore getSubmissionsData error:", err);
          throw err;
        }
      },

      async deleteSubmission(rowIndexOrId) {
        let docId = rowIndexOrId;
        if (typeof rowIndexOrId === 'number' && window.submissionsDb && window.submissionsDb[rowIndexOrId]) {
          docId = window.submissionsDb[rowIndexOrId][13];
        }
        if (docId) {
          await db.collection('submissions').doc(docId).delete();
        }
        return { success: true };
      },

      async submitSptData(data) {
        const now = new Date();
        const subDoc = {
          waktu: formatIndoDateTime(now),
          perihal: data.perihal || "",
          unitKerja: data.unit_kerja || "",
          namaAdmin: data.nama || "",
          nipAdmin: data.nip || "",
          email: data.email || "",
          namaAtasan: data.n_atasan || "",
          jabatanAtasan: data.j_atasan || "",
          pangkatGolAtasan: data.p_atasan || "",
          nipAtasan: data.nip_atasan || "",
          ttd: data.signature_data || "",
          integrasi: data.integrasi || "SITPP",
          tahun: data.tahun || now.getFullYear(),
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

        // Generate Word DOCX client-side
        const docxRes = await window.generateSptDocx(data);

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
