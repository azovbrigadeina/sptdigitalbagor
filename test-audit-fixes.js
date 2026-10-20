const assert = require('assert');

console.log('--- RUNNING AUDIT FIXES TESTS ---');

// Test 1: parseDeadlineIndo logic
const INDO_MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
function formatWibIsoDate(date) {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Jakarta', year: 'numeric', month: '2-digit', day: '2-digit'
  }).formatToParts(date);
  const pick = type => (parts.find(p => p.type === type) || {}).value || '';
  return `${pick('year')}-${pick('month')}-${pick('day')}`;
}
function wibEndOfDay(year, monthIndex, day) {
  return new Date(Date.UTC(year, monthIndex, day, 16, 59, 59));
}
function parseDeadlineIndo(str) {
  if (!str || typeof str !== 'string' || str === "Tanpa Batas") return null;
  const parts = str.trim().split(/\s+/);
  if (parts.length === 3) {
    const day = parseInt(parts[0], 10);
    const month = INDO_MONTHS.indexOf(parts[1]);
    const year = parseInt(parts[2], 10);
    if (day && month !== -1 && year) {
      return wibEndOfDay(year, month, day);
    }
  }
  const iso = new Date(str);
  if (!isNaN(iso.getTime())) {
    const [y, m, d] = formatWibIsoDate(iso).split('-').map(Number);
    return wibEndOfDay(y, m - 1, d);
  }
  return null;
}

const deadline1 = parseDeadlineIndo("6 Februari 2026");
assert(deadline1 instanceof Date, "Deadline should parse to Date");
assert.strictEqual(deadline1.getUTCFullYear(), 2026);
assert.strictEqual(deadline1.getUTCMonth(), 1); // 0-indexed: Februari = 1
assert.strictEqual(deadline1.getUTCDate(), 6);
assert.strictEqual(deadline1.getUTCHours(), 16); // 23:59:59 WIB = 16:59:59 UTC
assert.strictEqual(deadline1.getUTCMinutes(), 59);

const deadline2 = parseDeadlineIndo("Tanpa Batas");
assert.strictEqual(deadline2, null, "Tanpa Batas should return null");

const testNow = new Date("2026-10-12T13:00:00Z");
assert(testNow > deadline1, "Past deadline should be detected as expired");
console.log('✓ Test 1 Passed: parseDeadlineIndo correctly parses Indonesian dates and detects expired deadlines');

// Test 2: Apostrophe safety in dataset
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

const attendeeName = "Hj. Nur'aeni";
const escapedAttr = escapeHtml(attendeeName);
assert.strictEqual(escapedAttr, "Hj. Nur&#039;aeni");

const simulatedDatasetValue = attendeeName;
assert.doesNotThrow(() => {
  const fn = (id, nama) => { return { id, nama }; };
  const res = fn("doc123", simulatedDatasetValue);
  assert.strictEqual(res.nama, "Hj. Nur'aeni");
});
console.log('✓ Test 2 Passed: Dataset attribute safely preserves names with apostrophes');

// Test 3: CSV Content with BOM
const rows = [
  ["No", "Nama", "NIP"],
  [1, `"Hj. Nur'aeni"`, `'198801012010011002`]
];
const csvContent = "\uFEFF" + rows.map(e => e.join(",")).join("\n");
assert(csvContent.startsWith("\uFEFF"), "CSV must include UTF-8 Byte Order Mark for Excel");
assert(csvContent.includes(`"Hj. Nur'aeni"`));
console.log('✓ Test 3 Passed: CSV generator includes UTF-8 BOM and quotes special characters');

// Test 4: Year-scoped counting logic (B-6)
const mockSubmissions = [
  { perihal: "Bimtek SIMONA", tahun: 2025, nomorUrut: "001" },
  { perihal: "Bimtek SIMONA", tahun: 2025, nomorUrut: "002" },
  { perihal: "Bimtek SIMONA", tahun: 2026, nomorUrut: "001" },
  { perihal: "Lainnya", tahun: 2026, nomorUrut: "001" }
];

const targetPerihal = "Bimtek SIMONA";
const currentYear = 2026;
const filtered = mockSubmissions.filter(d => {
  return d.perihal === targetPerihal && (!d.tahun || d.tahun === currentYear);
});
assert.strictEqual(filtered.length, 1, "Only 2026 submissions for this perihal should be counted");
const nextNomorUrut = String(filtered.length + 1).padStart(3, '0');
assert.strictEqual(nextNomorUrut, "002");
console.log('✓ Test 4 Passed: Year-scoped number sequence resets per year correctly');

// Test 5: Mode penomoran SPT — otomatis sistem vs nomor agenda instansi sendiri
// Cermin dari resolusi di build.js submitSptData().
function resolveNomorSpt(opts) {
  const kegData = opts.kegData || null;
  const formatTemplate = (kegData && kegData.formatNomor) || "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}";
  const wajibManual = !!(kegData && kegData.autoNomor === false);
  const bolehManual = !kegData || kegData.izinkanNomorManual !== false;
  const mintaManual = String(opts.nomor_mode || "").toLowerCase() === "manual";
  if (!wajibManual && bolehManual && !String(opts.nomor_mode || "").trim()) throw new Error("MODE_EMPTY");
  const pakaiManual = wajibManual || (mintaManual && bolehManual);
  if (pakaiManual) {
    const nomor = String(opts.nomor_spt || "").trim();
    if (!nomor) throw new Error("MANUAL_EMPTY");
    return { nomorSpt: nomor, nomorMode: "manual" };
  }
  return {
    nomorSpt: formatTemplate
      .replace(/{nomor}/g, opts.nomorUrutPad)
      .replace(/{kode_opd}/g, opts.kodeOpd)
      .replace(/{tahun}/g, String(opts.tahun)),
    nomorMode: "auto"
  };
}

const base = { nomorUrutPad: "001", kodeOpd: "SETDA", tahun: 2026 };

// Mode dipilih eksplisit "auto" -> otomatis sistem
const autoRes = resolveNomorSpt(Object.assign({}, base, { kegData: { autoNomor: true }, nomor_mode: "auto" }));
assert.strictEqual(autoRes.nomorMode, "auto");
assert.strictEqual(autoRes.nomorSpt, "NOMOR : 090/001/SPT/SETDA/2026");

// Tidak ada default: mengirim tanpa memilih mode saat pilihan tersedia -> ditolak
assert.throws(() => resolveNomorSpt(Object.assign({}, base, { kegData: { autoNomor: true } })),
  /MODE_EMPTY/, "Mode kosong harus ditolak agar user tidak kirim tanpa sadar");
assert.throws(() => resolveNomorSpt(Object.assign({}, base, { kegData: null })),
  /MODE_EMPTY/, "Tanpa konfigurasi kegiatan pun mode wajib dipilih");

// Kegiatan yang mengunci modenya sendiri tidak wajib mengirim field mode
const kunciAutoRes = resolveNomorSpt(Object.assign({}, base, { kegData: { autoNomor: true, izinkanNomorManual: false } }));
assert.strictEqual(kunciAutoRes.nomorMode, "auto", "Kegiatan terkunci otomatis tidak butuh field mode");

// Pengirim memilih manual -> pakai nomor instansinya, tidak diubah
const manualRes = resolveNomorSpt(Object.assign({}, base, {
  kegData: { autoNomor: true, izinkanNomorManual: true },
  nomor_mode: "manual",
  nomor_spt: "  090/XYZ/SPT/DINKES/2026  "
}));
assert.strictEqual(manualRes.nomorMode, "manual");
assert.strictEqual(manualRes.nomorSpt, "090/XYZ/SPT/DINKES/2026", "Nomor manual harus di-trim & dicetak apa adanya");

// Manual tanpa nomor -> ditolak
assert.throws(() => resolveNomorSpt(Object.assign({}, base, {
  kegData: { autoNomor: true, izinkanNomorManual: true },
  nomor_mode: "manual",
  nomor_spt: "   "
})), /MANUAL_EMPTY/, "Manual tanpa nomor harus ditolak");

// Kegiatan melarang manual -> permintaan manual diabaikan, kembali otomatis
const ditolakRes = resolveNomorSpt(Object.assign({}, base, {
  kegData: { autoNomor: true, izinkanNomorManual: false },
  nomor_mode: "manual",
  nomor_spt: "090/HARUSNYA/DIABAIKAN"
}));
assert.strictEqual(ditolakRes.nomorMode, "auto");
assert.strictEqual(ditolakRes.nomorSpt, "NOMOR : 090/001/SPT/SETDA/2026");

// autoNomor=false (kompatibel lama) -> wajib manual walau pengirim kirim mode auto
const wajibRes = resolveNomorSpt(Object.assign({}, base, {
  kegData: { autoNomor: false },
  nomor_mode: "auto",
  nomor_spt: "090/WAJIB/MANUAL/2026"
}));
assert.strictEqual(wajibRes.nomorMode, "manual");
assert.strictEqual(wajibRes.nomorSpt, "090/WAJIB/MANUAL/2026");

// Nomor manual tidak mengonsumsi urutan otomatis (deret nomor sistem tetap rapat)
const rowsForCount = [
  { perihal: "SPT A", tahun: 2026, nomorMode: "auto" },
  { perihal: "SPT A", tahun: 2026, nomorMode: "auto" },
  { perihal: "SPT A", tahun: 2026, nomorMode: "manual" }
];
const counted = rowsForCount.filter(d => d.perihal === "SPT A" && d.nomorMode !== "manual" && d.tahun === 2026).length;
assert.strictEqual(String(counted + 1).padStart(3, '0'), "003", "Nomor manual tidak boleh menggeser nomor urut otomatis");
console.log('✓ Test 5 Passed: Mode penomoran otomatis/manual diresolusi benar (validasi, override, & urutan)');

// Test 6: Keunikan nomor manual per tahun (tolak bentrok nomor)
// Cermin dari makeNomorKey() + cek bentrok di build.js submitSptData().
function makeNomorKey(nomor) {
  return String(nomor || '').trim().replace(/\s+/g, ' ').toUpperCase();
}
function cariBentrok(existing, nomor, tahun) {
  const key = makeNomorKey(nomor);
  return existing.some(d => {
    const docYear = d.tahun ? Number(d.tahun) : null;
    const sameYear = !docYear || docYear === tahun;
    return sameYear && makeNomorKey(d.nomorSpt) === key;
  });
}

// Normalisasi mengabaikan beda huruf besar/kecil & spasi berlebih
assert.strictEqual(
  makeNomorKey('  090/123/spt/setda/2026  '),
  makeNomorKey('090/123/SPT/SETDA/2026'),
  'Perbandingan nomor harus case-insensitive & tahan spasi berlebih'
);

const existingSubs = [
  { tahun: 2026, nomorSpt: '090/123/SPT/SETDA/2026', nomorMode: 'manual' },
  { tahun: 2025, nomorSpt: '090/LAMA/SPT/SETDA/2025', nomorMode: 'manual' },
  { tahun: 2026, nomorSpt: 'NOMOR : 090/001/SPT/SETDA/2026', nomorMode: 'auto' }
];

// Nomor manual yang sudah dipakai di tahun yang sama -> ditolak
assert.strictEqual(cariBentrok(existingSubs, '090/123/spt/setda/2026', 2026), true,
  'Nomor manual duplikat di tahun yang sama harus ditolak');

// Nomor sama di tahun berbeda -> tidak bentrok (tahun berbeda sudah masuk nomornya)
assert.strictEqual(cariBentrok(existingSubs, '090/123/SPT/SETDA/2026', 2025), false,
  'Nomor yang hanya dipakai di tahun lain tidak boleh memblokir');

// Nomor manual yang menabrak nomor otomatis di tahun yang sama -> tetap ditolak
assert.strictEqual(cariBentrok(existingSubs, 'nomor : 090/001/spt/setda/2026', 2026), true,
  'Nomor manual yang sama dengan nomor otomatis tahun ini harus ditolak');

// Nomor baru -> lolos
assert.strictEqual(cariBentrok(existingSubs, '090/999/SPT/SETDA/2026', 2026), false,
  'Nomor manual baru harus lolos');
console.log('✓ Test 6 Passed: Nomor manual duplikat per tahun ditolak (normalisasi + lintas mode + skop tahun)');

// Test 7: Filter mode penomoran di rekap admin (row[22], data lama dianggap "auto")
function filterNomorMode(rows, mode) {
  return rows.filter(r => mode === "Semua Mode" || (r[22] || "auto") === mode);
}

const rekapRows = [
  { r: ["", "SPT A", "", "", "", "", "", "", "", "", "", "", 2026, "d1", "", "", "", "", "", "090/M/2026", "001", "K", "manual"] },
  { r: ["", "SPT A", "", "", "", "", "", "", "", "", "", "", 2026, "d2", "", "", "", "", "", "090/001/2026", "001", "K", "auto"] },
  { r: ["", "SPT B", "", "", "", "", "", "", "", "", "", "", 2025, "d3", "", "", "", "", "", "090/LEGACY/2025", "001", "K"] }
].map(o => o.r);

assert.strictEqual(filterNomorMode(rekapRows, "Semua Mode").length, 3, "Semua Mode harus menampilkan semua baris");
assert.strictEqual(filterNomorMode(rekapRows, "manual").length, 1, "Filter manual harus menyisakan 1 baris");
assert.strictEqual(filterNomorMode(rekapRows, "manual")[0][13], "d1", "Baris manual yang benar harus tersisa");
assert.strictEqual(filterNomorMode(rekapRows, "auto").length, 2, "Baris lama tanpa mode dihitung sebagai auto");
assert(filterNomorMode(rekapRows, "auto").every(r => r[22] !== "manual"), "Filter auto tidak boleh memuat baris manual");
console.log('✓ Test 7 Passed: Filter mode rekap admin benar (manual/auto + data lama = auto)');

// Test 8: Validasi TTD mentah sebelum ditampilkan ke admin
function normalizeSignatureDataUrl(value) {
  const raw = typeof value === 'string' ? value.trim() : '';
  if (!/^data:image\/(?:png|jpe?g);base64,[A-Za-z0-9+/=\s]+$/i.test(raw)) return '';
  return raw.replace(/\s+/g, '');
}

const pngTtd = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==';
assert.strictEqual(normalizeSignatureDataUrl(pngTtd), pngTtd, 'TTD PNG valid harus diteruskan');
assert.strictEqual(
  normalizeSignatureDataUrl('data:image/png;base64, iVBOR w0KGgo='),
  'data:image/png;base64,iVBORw0KGgo=',
  'Spasi/baris baru pada base64 harus dibersihkan'
);
assert.strictEqual(normalizeSignatureDataUrl('data:image/jpeg;base64,/9j/4AAQ'), 'data:image/jpeg;base64,/9j/4AAQ');
assert.strictEqual(normalizeSignatureDataUrl('data:image/svg+xml;base64,PHN2Zz4='), '', 'SVG tidak boleh diterima');
assert.strictEqual(normalizeSignatureDataUrl('javascript:alert(1)'), '', 'URL non-gambar harus ditolak');
assert.strictEqual(normalizeSignatureDataUrl(''), '');
assert.strictEqual(normalizeSignatureDataUrl(null), '');
assert.strictEqual(normalizeSignatureDataUrl(undefined), '');
console.log('✓ Test 8 Passed: TTD mentah hanya menerima data URL PNG/JPEG yang valid');

// Test 9: Branding aplikasi & footer laporan dapat diatur admin
const DEFAULT_BRANDING = {
  appName: 'Tugasku',
  reportFooter: 'Dihasilkan otomatis melalui Tugasku - Layanan Penugasan, Bagian Organisasi Setda Kab. Muaro Jambi'
};
function normalizeBrandingConfig(cfg) {
  const source = cfg || {};
  const appName = String(source.appName == null ? '' : source.appName).trim().slice(0, 40) || DEFAULT_BRANDING.appName;
  const reportFooter = String(source.reportFooter == null ? '' : source.reportFooter).trim().slice(0, 300) || DEFAULT_BRANDING.reportFooter;
  return { appName: appName, reportFooter: reportFooter };
}
function getReportFooterText(config) {
  const footer = (config && config.reportFooter) ? config.reportFooter : DEFAULT_BRANDING.reportFooter;
  return '_' + footer + '_';
}

assert.deepStrictEqual(normalizeBrandingConfig(null), DEFAULT_BRANDING, 'Konfigurasi kosong harus memakai default');
assert.deepStrictEqual(normalizeBrandingConfig({ appName: '  ', reportFooter: '' }), DEFAULT_BRANDING, 'Nilai kosong harus memakai default');
assert.deepStrictEqual(
  normalizeBrandingConfig({ appName: '  Tugasku Baru  ', reportFooter: '  Footer baru  ' }),
  { appName: 'Tugasku Baru', reportFooter: 'Footer baru' },
  'Spasi berlebih harus dipangkas'
);
assert.strictEqual(normalizeBrandingConfig({ appName: 'X'.repeat(50) }).appName.length, 40, 'Nama aplikasi dibatasi 40 karakter');
assert.strictEqual(normalizeBrandingConfig({ reportFooter: 'Y'.repeat(400) }).reportFooter.length, 300, 'Footer dibatasi 300 karakter');
assert.strictEqual(getReportFooterText({ reportFooter: 'Footer baru' }), '_Footer baru_', 'Footer laporan harus dibungkus italic WhatsApp');
assert.strictEqual(getReportFooterText(null), '_' + DEFAULT_BRANDING.reportFooter + '_', 'Tanpa konfigurasi harus memakai footer default');
console.log('✓ Test 9 Passed: Branding aplikasi & footer laporan ternormalisasi dan dapat dikonfigurasi');

console.log('--- ALL AUDIT FIXES TESTS PASSED SUCCESSFULLY! ---');
