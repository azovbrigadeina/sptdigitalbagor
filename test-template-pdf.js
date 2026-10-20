// Automated tests: PDF wajib tunduk pada tag template aktif.
// Tujuan: perubahan di masa depan tidak boleh membuat PDF diam-diam mencetak
// elemen yang tidak diminta oleh template .docx yang diunggah admin.
const assert = require('assert');
const fs = require('fs');
const path = require('path');

global.window = globalThis;
if (!globalThis.atob) globalThis.atob = (b) => Buffer.from(b, 'base64').toString('binary');
if (!globalThis.btoa) globalThis.btoa = (b) => Buffer.from(b, 'binary').toString('base64');

const PizZip = require('pizzip');

console.log('--- RUNNING TEMPLATE/PDF FIDELITY TESTS ---');

const TEMPLATE_PATH = [
  path.join(__dirname, 'template spt simona.docx'),
  path.join(__dirname, 'public', 'template_spt_simona.docx')
].find((p) => fs.existsSync(p));

if (!TEMPLATE_PATH) {
  console.error('✗ Template .docx tidak ditemukan (root atau public/).');
  process.exit(1);
}
const TEMPLATE_B64 = fs.readFileSync(TEMPLATE_PATH).toString('base64');

// Nilai sentinel unik per tag opsional, supaya mudah dilacak di content stream PDF.
const SENTINEL = {
  nomor_spt: 'ZZNOMORSPTZZ',
  nomor_urut: 'ZZNOMORURUTZZ',
  kode_opd: 'ZZKODEOPDZZ',
  tahun: 'ZZTAHUNZZ'
};

// Tag yang menurut desain layout resmi PDF memang SELALU dicetak (nomor surat wajib
// tampil di surat), sehingga bukan termasuk "divergen" walau template tidak memuatnya.
const ALWAYS_PRINTED_TAGS = ['nomor_spt'];

// Tag yang pencetakannya di PDF dikendalikan oleh template aktif: tanpa {{tag}} di
// template tidak boleh tercetak, dan dengan {{tag}} harus tercetak sesuai nilainya.
const PDF_GATED_TAGS = {
  mode_nomor: [
    { nomor_mode: 'manual', expect: '(Penomoran: Nomor Instansi Sendiri)' },
    { nomor_mode: 'auto', expect: '(Penomoran: Otomatis Sistem)' },
    { nomor_mode: undefined, expect: '(Penomoran: Otomatis Sistem)' }
  ]
};

function baseData() {
  return {
    unit_kerja: 'Bagian Organisasi Sekretariat Daerah',
    nama: 'Budi Santoso, S.Kom',
    pangkat: 'Penata Muda - III/a',
    nip: '199012312015031001',
    jabatan: 'Analis Kebijakan Ahli Pertama',
    no_hp: '081234567890',
    email: 'budi@organisasi.example.id',
    j_atasan: 'Kepala Bagian Organisasi',
    n_atasan: 'Drs. H. Ahmad Fauzi, M.Si',
    nip_atasan: '197508152000031002',
    p_atasan: 'Pembina Tingkat I - IV/b',
    perihal: 'Penyusunan Analisis Jabatan dan Beban Kerja',
    dasar_spt: 'Peraturan Bupati Muaro Jambi Nomor 1 Tahun 2026.',
    nomor_spt: SENTINEL.nomor_spt,
    nomor_urut: SENTINEL.nomor_urut,
    kode_opd: SENTINEL.kode_opd,
    tahun: SENTINEL.tahun,
    verify_url: 'https://tugasku-bagor.web.app/?v=REGRESI'
  };
}

// Sisipkan tag ke template turunan tanpa merusak paragraf: tempel setelah tag pertama
// yang sudah ada sebagai jangkar (cara yang sama dipakai admin saat mengedit template).
function templateWithTags(baseBuffer, tags) {
  const zip = new PizZip(baseBuffer);
  const xml = zip.files['word/document.xml'].asText();
  const firstTag = xml.match(/\{\{[^}]+\}\}/);
  if (!firstTag) throw new Error('Template tidak memuat tag apa pun untuk dijadikan jangkar.');
  const injected = ' ' + tags.map((t) => '{{' + t + '}}').join(' ');
  zip.file('word/document.xml', xml.replace(firstTag[0], firstTag[0] + injected));
  return zip.generate({ type: 'nodebuffer' }).toString('base64');
}

(async () => {
  await import('./src/docx-generator.js');

  const { generateSptPdf, scanDocxTags, SYSTEM_TAG_LIST } = globalThis.window;
  assert.strictEqual(typeof generateSptPdf, 'function', 'generateSptPdf harus tersedia');
  assert.strictEqual(typeof scanDocxTags, 'function', 'scanDocxTags harus tersedia');

  const scan = scanDocxTags(TEMPLATE_B64);
  assert.strictEqual(scan.success, true, 'Template bawaan harus terbaca');
  assert.strictEqual(scan.hasTtd, true, 'Template bawaan harus memuat QR/TTD');

  const allTags = SYSTEM_TAG_LIST.map((t) => t.tag);
  const optionalTags = allTags.filter((t) => !scan.tagsFound.includes(t));
  assert(optionalTags.includes('mode_nomor'),
    'Template bawaan diharapkan tidak memuat {{mode_nomor}} agar test ini bermakna');

  // jsPDF meng-escape tanda kurung pada string PDF (\( dan \)), jadi normalkan dulu
  // supaya ekspektasi bisa ditulis persis seperti label aslinya.
  function pdfText(raw) {
    return raw.replace(/\\([()\\])/g, '$1');
  }

  async function renderPdf(templateB64, overrides) {
    const res = await generateSptPdf(Object.assign(baseData(), overrides || {}), templateB64);
    const raw = String(res.fileContent).replace(/^data:[^;]+;base64,/, '');
    return pdfText(atob(raw));
  }

  // --- Arah 1: template TANPA tag opsional -> nilainya tidak boleh tercetak ---
  const basePdf = await renderPdf(TEMPLATE_B64);

  const leaked = optionalTags.filter((tag) => {
    const sentinel = SENTINEL[tag];
    return sentinel && basePdf.includes(sentinel) && !ALWAYS_PRINTED_TAGS.includes(tag);
  });
  assert.deepStrictEqual(leaked, [],
    'PDF mencetak nilai tag yang tidak diminta template: ' + leaked.join(', '));

  assert(!basePdf.includes('Penomoran:'),
    'Label mode tidak boleh tercetak bila template tidak memuat {{mode_nomor}}');

  // Guard arah sebaliknya: konten wajib tidak boleh ikut hilang
  ALWAYS_PRINTED_TAGS.forEach((tag) => {
    const sentinel = SENTINEL[tag];
    if (sentinel) {
      assert(basePdf.includes(sentinel), 'Tag wajib ' + tag + ' harus selalu tercetak di PDF');
    }
  });
  console.log('✓ Test 1 Passed: template tanpa tag opsional -> PDF tidak mencetak konten tambahan');

  // --- Arah 2: template DENGAN tag -> nilainya harus tercetak ---
  const gatedNames = Object.keys(PDF_GATED_TAGS);
  const gatedTemplate = templateWithTags(fs.readFileSync(TEMPLATE_PATH), gatedNames);
  const gatedScan = scanDocxTags(gatedTemplate);
  gatedNames.forEach((tag) => {
    assert(gatedScan.tagsFound.includes(tag),
      'Tag ' + tag + ' harus terbaca pada template turunan');
  });

  for (const tag of gatedNames) {
    for (const c of PDF_GATED_TAGS[tag]) {
      const pdf = await renderPdf(gatedTemplate, { nomor_mode: c.nomor_mode });
      assert(pdf.includes(c.expect),
        'Template memuat {{' + tag + '}} dengan mode ' + String(c.nomor_mode) +
        ' -> PDF harus memuat "' + c.expect + '"');
      assert(pdf.includes(SENTINEL.nomor_spt), 'Nomor surat tetap harus tercetak bersama label mode');
    }
  }
  console.log('✓ Test 2 Passed: template dengan {{' + gatedNames.join('}}, {{') + '}} -> label mode tercetak sesuai mode');

  console.log('--- ALL TEMPLATE/PDF FIDELITY TESTS PASSED SUCCESSFULLY! ---');
})().catch((err) => {
  console.error('✗ TEST GAGAL:', err && err.message ? err.message : err);
  process.exit(1);
});
