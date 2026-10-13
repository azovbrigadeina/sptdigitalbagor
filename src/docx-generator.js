import PizZip from 'pizzip';
import Docxtemplater from 'docxtemplater';
import ImageModule from 'docxtemplater-image-module-free';
import QRCode from 'qrcode';
import { jsPDF } from 'jspdf';
import { LOGO_MUARO_JAMBI_BASE64 } from './logo-muarojambi.js';

export const SYSTEM_TAG_LIST = [
  { tag: "unitkerja", label: "Unit Kerja / OPD", desc: "Nama Unit Kerja atau Instansi dari SI-PRABU", example: "Bagian Organisasi Setda" },
  { tag: "nama_admin", label: "Nama Admin / Pemohon", desc: "Nama lengkap admin pemohon", example: "Budi Santoso, S.Kom" },
  { tag: "NIP_admin", label: "NIP Admin", desc: "NIP 18 digit pegawai pemohon", example: "199012312015031001" },
  { tag: "pangkat_admin", label: "Pangkat / Golongan Pemohon", desc: "Pangkat dan golongan ruang pegawai", example: "Penata Muda - III/a" },
  { tag: "Jabatanadmin", label: "Jabatan Pemohon", desc: "Nama jabatan admin pemohon", example: "Analis Kebijakan Ahli Pertama" },
  { tag: "no_hpadmin", label: "Nomor WhatsApp / HP", desc: "Nomor kontak aktif pemohon", example: "081234567890" },
  { tag: "email_admin", label: "Email Pemohon", desc: "Alamat email pemohon (@gmail.com)", example: "budi.organisasi@gmail.com" },
  { tag: "perihal", label: "Kegiatan / Perihal", desc: "Nama kegiatan atau perihal SPT", example: "Penyusunan Analisis Jabatan dan Beban Kerja" },
  { tag: "dasar_spt", label: "Dasar Hukum SPT", desc: "Teks dasar hukum yang terhubung dengan kegiatan", example: "Peraturan Menteri Pendayagunaan Aparatur Negara dan Reformasi Birokrasi..." },
  { tag: "TTL", label: "Tanggal Dokumen", desc: "Tanggal terbit dokumen (hari ini dalam format Indo)", example: "5 Oktober 2026" },
  { tag: "NAMA_ATASAN", label: "Nama Atasan", desc: "Nama lengkap atasan penandatangan", example: "Drs. H. Ahmad Fauzi, M.Si" },
  { tag: "NIP_ATASAN", label: "NIP Atasan", desc: "NIP 18 digit atasan penandatangan", example: "197508152000031002" },
  { tag: "JABATAN_ATASAN", label: "Jabatan Atasan", desc: "Nama jabatan atasan penandatangan", example: "Kepala Bagian Organisasi" },
  { tag: "PANGKAT_GOL_ATASAN", label: "Pangkat / Golongan Atasan", desc: "Pangkat dan golongan ruang atasan penandatangan", example: "Pembina Tingkat I - IV/b" },
  { tag: "nomor_spt", label: "Nomor SPT Lengkap", desc: "Nomor registrasi SPT otomatis berdasarkan urutan pendaftaran", example: "NOMOR : 090/001/SPT/SETDA/2026" },
  { tag: "nomor_urut", label: "Nomor Urut Pendaftaran", desc: "Nomor urut 3 digit pendaftaran per kegiatan", example: "001" },
  { tag: "kode_opd", label: "Kode Singkatan OPD", desc: "Kode singkatan resmi OPD pemohon", example: "SETDA" },
  { tag: "tahun", label: "Tahun Dokumen", desc: "Tahun penerbitan dokumen", example: "2026" },
  { tag: "ttd", label: "QR Code Verifikasi Resmi", desc: "Gambar QR Code verifikasi keaslian dokumen otomatis", example: "[QR Code Verifikasi TTE]" }
];

const emptyPngBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";

function base64ToUint8Array(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

const emptyPng = base64ToUint8Array(emptyPngBase64);

export async function generateQrCodeBase64(text) {
  try {
    return await QRCode.toDataURL(text || "https://tugasku-bagor.web.app", {
      width: 200,
      margin: 1,
      color: {
        dark: '#004899',
        light: '#FFFFFF'
      }
    });
  } catch (err) {
    console.warn("Gagal membuat QR code:", err);
    return "data:image/png;base64," + emptyPngBase64;
  }
}

const imageOpts = {
  setParser(tag) {
    if (tag === "ttd" || tag === "%ttd" || tag === "qrcode" || tag === "%qrcode") {
      return {
        type: "placeholder",
        value: tag,
        module: "open-xml-templating/docxtemplater-image-module",
        centered: false
      };
    }
    return null;
  },
  getImage(tagValue) {
    if (!tagValue || typeof tagValue !== 'string' || !tagValue.trim()) {
      return emptyPng.buffer;
    }
    const cleanBase64 = tagValue.replace(/^data:image\/\w+;base64,/, "");
    try {
      const bytes = base64ToUint8Array(cleanBase64);
      return bytes.buffer;
    } catch(e) {
      console.warn("Failed to parse image, fallback to empty:", e);
      return emptyPng.buffer;
    }
  },
  getSize(img, tagValue) {
    if (!tagValue || typeof tagValue !== 'string' || !tagValue.trim()) {
      return [1, 1];
    }
    return [130, 130];
  }
};

function extractTagsFromDocxZip(zip) {
  const tagsFound = new Set();
  const rawTagRegex = /\{\{\s*([%#/^]?[\w\-]+)\s*\}\}/g;
  
  for (const [filename, file] of Object.entries(zip.files)) {
    if (filename.startsWith('word/') && filename.endsWith('.xml')) {
      const xml = file.asText();
      const cleanText = xml.replace(/<[^>]+>/g, '');
      let match;
      while ((match = rawTagRegex.exec(cleanText)) !== null) {
        let tagName = match[1].trim();
        if (tagName.startsWith('%') || tagName.startsWith('#') || tagName.startsWith('/')) {
          tagName = tagName.slice(1);
        }
        if (tagName) {
          tagsFound.add(tagName);
        }
      }
    }
  }
  return Array.from(tagsFound);
}

// 1. Tag Scanner & Analyzer
window.scanDocxTags = function(arrayBufferOrBase64) {
  try {
    let buffer = arrayBufferOrBase64;
    if (typeof arrayBufferOrBase64 === 'string') {
      const clean = arrayBufferOrBase64.replace(/^data:[^;]+;base64,/, "");
      buffer = base64ToUint8Array(clean).buffer;
    }
    const zip = new PizZip(buffer);
    const tagsFound = extractTagsFromDocxZip(zip);
    
    const knownTags = SYSTEM_TAG_LIST.map(t => t.tag);
    const validTags = [];
    const unknownTags = [];
    
    tagsFound.forEach(t => {
      if (knownTags.includes(t) || t === 'qrcode') {
        validTags.push(t);
      } else {
        unknownTags.push(t);
      }
    });
    
    const missingTags = knownTags.filter(t => !tagsFound.includes(t));
    const hasTtd = tagsFound.includes('ttd') || tagsFound.includes('qrcode');
    
    return {
      success: true,
      tagsFound,
      validTags,
      unknownTags,
      missingTags,
      hasTtd,
      totalTags: tagsFound.length
    };
  } catch (err) {
    return {
      success: false,
      error: err.message || err.toString()
    };
  }
};

// 2. Main DOCX Generator (Generates QR Code Verification for output document)
window.generateSptDocx = async function(data, customTemplate) {
  let arrayBuffer = null;

  if (customTemplate) {
    if (typeof customTemplate === 'string') {
      const clean = customTemplate.replace(/^data:[^;]+;base64,/, "");
      arrayBuffer = base64ToUint8Array(clean).buffer;
    } else if (customTemplate instanceof ArrayBuffer) {
      arrayBuffer = customTemplate;
    } else if (customTemplate.buffer instanceof ArrayBuffer) {
      arrayBuffer = customTemplate.buffer;
    }
  }

  // Fallback to active template cache if set on window
  if (!arrayBuffer && window.__activeCustomTemplateBase64) {
    const clean = window.__activeCustomTemplateBase64.replace(/^data:[^;]+;base64,/, "");
    arrayBuffer = base64ToUint8Array(clean).buffer;
  }

  // If not yet loaded in memory, fetch active template from Firestore
  if (!arrayBuffer && typeof window.FirebaseService !== 'undefined' && window.FirebaseService.getActiveTemplate) {
    try {
      const activeTpl = await window.FirebaseService.getActiveTemplate();
      if (activeTpl && activeTpl.contentBase64) {
        window.__activeCustomTemplateBase64 = activeTpl.contentBase64;
        const clean = activeTpl.contentBase64.replace(/^data:[^;]+;base64,/, "");
        arrayBuffer = base64ToUint8Array(clean).buffer;
      }
    } catch(err) {
      console.warn("Gagal memuat active template dari Firestore:", err);
    }
  }

  // Default system template if no custom template in database
  if (!arrayBuffer) {
    const resp = await fetch('/template_spt_simona.docx');
    if (!resp.ok) {
      throw new Error('Gagal memuat template Word (.docx): ' + resp.statusText);
    }
    arrayBuffer = await resp.arrayBuffer();
  }

  const zip = new PizZip(arrayBuffer);
  const imageModule = new ImageModule(imageOpts);

  const doc = new Docxtemplater(zip, {
    modules: [imageModule],
    delimiters: { start: "{{", end: "}}" },
    paragraphLoop: true,
    linebreaks: true
  });

  const months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
  const d = new Date();
  const indoDate = d.getDate() + " " + months[d.getMonth()] + " " + d.getFullYear();

  // Generate QR Code verification URL
  const verifyTargetUrl = data.verify_url || (data.docId ? ("https://tugasku-bagor.web.app/?v=" + data.docId) : "https://tugasku-bagor.web.app");
  const qrCodeImageBase64 = await generateQrCodeBase64(verifyTargetUrl);

  const currentYearStr = String(data.tahun || d.getFullYear());
  const fallbackNomorUrut = data.nomor_urut || "001";
  const fallbackKodeOpd = data.kode_opd || "SETDA";
  const finalNomorSpt = data.nomor_spt || `NOMOR : 090/${fallbackNomorUrut}/SPT/${fallbackKodeOpd}/${currentYearStr}`;

  doc.render({
    unitkerja: data.unit_kerja || "",
    nama_admin: data.nama || "",
    pangkat_admin: data.pangkat || "",
    NIP_admin: data.nip || "",
    Jabatanadmin: data.jabatan || "",
    no_hpadmin: data.no_hp || "",
    email_admin: data.email || "",
    JABATAN_ATASAN: data.j_atasan || "",
    NAMA_ATASAN: data.n_atasan || "",
    NIP_ATASAN: data.nip_atasan || "",
    PANGKAT_GOL_ATASAN: data.p_atasan || "",
    perihal: data.perihal || "",
    TTL: indoDate,
    dasar_spt: data.dasar_spt || "",
    nomor_spt: finalNomorSpt,
    nomor_urut: fallbackNomorUrut,
    kode_opd: fallbackKodeOpd,
    tahun: currentYearStr,
    ttd: qrCodeImageBase64,
    qrcode: qrCodeImageBase64
  });

  const uint8 = doc.getZip().generate({
    type: "uint8array",
    compression: "DEFLATE"
  });

  let binary = "";
  const len = uint8.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(uint8[i]);
  }
  const base64 = btoa(binary);

  return {
    fileContent: base64,
    uint8Array: uint8,
    docZip: doc.getZip(),
    rawZip: zip,
    finalNomorSpt: finalNomorSpt,
    indoDate: indoDate,
    qrCodeImageBase64: qrCodeImageBase64,
    filename: "SPT_" + (data.nama || "Dokumen").replace(/\s+/g, "_") + ".docx"
  };
};

// 3. Official Vector PDF Generator strictly derived from active template & tags
async function renderTemplateDrivenVectorPdf(data, docxRes) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  
  const ml = 20;
  const mr = 20;
  const mt = 13;
  const pageW = 210;
  const contentW = pageW - ml - mr; // 170mm

  // Deteksi judul dokumen langsung dari template XML
  let docTitle = "SURAT TUGAS";
  try {
    const xml = docxRes.rawZip.files["word/document.xml"].asText();
    if (/SURAT\s+PERINTAH\s+TUGAS/i.test(xml)) {
      docTitle = "SURAT PERINTAH TUGAS";
    }
  } catch(e) {}

  // 1. Kop Surat - Disesuaikan secara dinamis dengan Unit Kerja / OPD pengaju
  const logoW = 22;
  const logoH = 27.8; // Rasio presisi lambang resmi Muaro Jambi
  if (LOGO_MUARO_JAMBI_BASE64) {
    try {
      doc.addImage("data:image/png;base64," + LOGO_MUARO_JAMBI_BASE64, "PNG", ml, mt, logoW, logoH);
    } catch(err) {
      console.warn("Logo Muaro Jambi tidak dapat dimuat:", err);
    }
  }

  const headerLeftX = ml + logoW + 4; // 46mm
  const headerCenterX = headerLeftX + (pageW - mr - headerLeftX) / 2; // 118mm
  const headerMaxW = pageW - mr - headerLeftX; // 144mm

  // Tingkat 1: PEMERINTAH KABUPATEN MUARO JAMBI (Font 15)
  doc.setFont("times", "bold");
  doc.setFontSize(15);
  doc.text("PEMERINTAH KABUPATEN MUARO JAMBI", headerCenterX, mt + 6, { align: "center" });

  const rawUnitKerja = (data.unit_kerja || "UNIT KERJA").trim();
  const isSetdaSubUnit = rawUnitKerja.toLowerCase().includes("bagian ") && !rawUnitKerja.toLowerCase().includes("dinas");

  let kopBottomY;
  if (isSetdaSubUnit) {
    // Tingkat 2: SEKRETARIAT DAERAH (Font 20)
    doc.setFontSize(20);
    doc.text("SEKRETARIAT DAERAH", headerCenterX, mt + 14.5, { align: "center" });
    
    // Tingkat 3: Sub-unit / Bagian (Font 15)
    let subUnitText = rawUnitKerja.replace(/sekretariat\s+daerah/gi, "").trim();
    if (!subUnitText) subUnitText = rawUnitKerja;
    doc.setFontSize(15);
    doc.text(subUnitText.toUpperCase(), headerCenterX, mt + 21.5, { align: "center" });
    kopBottomY = mt + 23.5;
  } else {
    // Tingkat 2: OPD / Instansi (Font 20 - lebih besar dan proporsional)
    doc.setFontSize(20);
    
    function getBalancedLines(text, maxW) {
      const fullW = doc.getTextWidth(text);
      if (fullW <= maxW) return [text];
      const words = text.split(/\s+/);
      if (words.length <= 1) return [text];
      let bestSplit = null;
      let minDiff = Infinity;
      for (let i = 1; i < words.length; i++) {
        const line1 = words.slice(0, i).join(" ");
        const line2 = words.slice(i).join(" ");
        const w1 = doc.getTextWidth(line1);
        const w2 = doc.getTextWidth(line2);
        if (w1 <= maxW && w2 <= maxW) {
          const diff = Math.abs(w1 - w2);
          if (diff < minDiff) {
            minDiff = diff;
            bestSplit = [line1, line2];
          }
        }
      }
      return bestSplit || doc.splitTextToSize(text, maxW);
    }

    const unitLines = getBalancedLines(rawUnitKerja.toUpperCase(), headerMaxW);
    let uY = (unitLines.length === 1) ? (mt + 16) : (mt + 14.5);
    unitLines.forEach((line, idx) => {
      doc.text(line, headerCenterX, uY, { align: "center" });
      if (idx < unitLines.length - 1) uY += 7.8;
    });
    kopBottomY = uY + 2;
  }

  // Garis Pembatas Kop Resmi (Garis Ganda Berjarak Presisi)
  const lineY = Math.max(mt + logoH + 2.5, kopBottomY + 3);
  doc.setLineWidth(0.9);
  doc.line(ml, lineY, pageW - mr, lineY);
  doc.setLineWidth(0.25);
  doc.line(ml, lineY + 0.8, pageW - mr, lineY + 0.8);

  // 2. Judul & Nomor Surat - Dinamis sesuai template
  let curY = lineY + 7.5;
  doc.setFont("times", "bold");
  doc.setFontSize(12.5);
  doc.text(docTitle, pageW / 2, curY, { align: "center" });
  const titleW = doc.getTextWidth(docTitle);
  doc.setLineWidth(0.3);
  doc.line(pageW / 2 - titleW / 2, curY + 0.8, pageW / 2 + titleW / 2, curY + 0.8);

  curY += 5.5;
  doc.setFont("times", "normal");
  doc.setFontSize(10.5);

  // Sanitasi nomor agar TIDAK ADA double 'NOMOR : NOMOR :'
  let rawNomor = docxRes.finalNomorSpt || data.nomor_spt || "";
  let cleanNomor = rawNomor.replace(/^(NOMOR\s*:\s*)+/i, "").trim();
  const finalNomor = cleanNomor ? ("NOMOR : " + cleanNomor) : `NOMOR : 090/${data.nomor_urut || "001"}/SPT/${data.kode_opd || "SETDA"}/${data.tahun || "2026"}`;
  doc.text(finalNomor, pageW / 2, curY, { align: "center" });

  const labelX = ml;
  const colonX = ml + 18;
  const bodyX = ml + 22;
  const bodyW = pageW - mr - bodyX;

  // 3. Dasar
  curY += 8;
  doc.setFont("times", "bold");
  doc.text("Dasar", labelX, curY);
  doc.text(":", colonX, curY);

  doc.setFont("times", "normal");
  const dasarText = data.dasar_spt || data.dasar || "Surat Perintah Tugas resmi di lingkungan Pemerintah Kabupaten Muaro Jambi.";
  const dasarLines = doc.splitTextToSize(dasarText, bodyW);
  doc.text(dasarLines, bodyX, curY);
  curY += (dasarLines.length * 4.6) + 4.5;

  // 4. Memerintahkan
  doc.setFont("times", "bold");
  doc.setFontSize(11);
  doc.text("MEMERINTAHKAN :", pageW / 2, curY, { align: "center" });
  curY += 6;

  // 5. Kepada
  doc.setFont("times", "bold");
  doc.setFontSize(10.5);
  doc.text("Kepada", labelX, curY);
  doc.text(":", colonX, curY);

  const pegawai = [
    { num: "1.", label: "Nama", val: data.nama || "-", bold: true },
    { num: "2.", label: "Pangkat / Gol", val: data.pangkat || "-" },
    { num: "3.", label: "NIP", val: data.nip || "-" },
    { num: "4.", label: "Jabatan", val: data.jabatan || "-" },
    { num: "5.", label: "Unit Kerja", val: data.unit_kerja || "-", bold: true }
  ];
  if (data.no_hp) pegawai.push({ num: "6.", label: "Nomor Telepon", val: data.no_hp });
  if (data.email) pegawai.push({ num: String(pegawai.length + 1) + ".", label: "Alamat E-mail", val: data.email });

  const subLabelX = bodyX;       // 42mm
  const subTextX = bodyX + 6;    // 48mm
  const subColonX = bodyX + 34;  // 76mm
  const subValX = bodyX + 37;    // 79mm
  const subValW = pageW - mr - subValX; // 111mm

  let pY = curY;
  pegawai.forEach(item => {
    doc.setFont("times", "normal");
    doc.text(item.num, subLabelX, pY);
    doc.text(item.label, subTextX, pY);
    doc.text(":", subColonX, pY);
    if (item.bold) doc.setFont("times", "bold");
    
    const valLines = doc.splitTextToSize(item.val, subValW);
    doc.text(valLines, subValX, pY);
    pY += Math.max(4.6, valLines.length * 4.4);
  });
  curY = pY + 3.5;

  // 6. Untuk
  doc.setFont("times", "bold");
  doc.text("Untuk", labelX, curY);
  doc.text(":", colonX, curY);
  doc.setFont("times", "normal");
  const untukText = data.perihal ? `Melaksanakan tugas dalam rangka ${data.perihal} di lingkungan Pemerintah Kabupaten Muaro Jambi.` : "Melaksanakan tugas kedinasan sebagaimana ditugaskan.";
  const untukLines = doc.splitTextToSize(untukText, bodyW);
  doc.text(untukLines, bodyX, curY);
  curY += (untukLines.length * 4.6) + 4.5;

  // 7. Penutup
  const penutupText = (docTitle === "SURAT TUGAS")
    ? "Demikian surat tugas ini dibuat untuk dilaksanakan sebagaimana mestinya dengan penuh rasa tanggung jawab."
    : "Demikian surat perintah tugas ini dibuat untuk dilaksanakan sebagaimana mestinya dengan penuh rasa tanggung jawab.";
  const penutupLines = doc.splitTextToSize(penutupText, contentW);
  doc.text(penutupLines, ml, curY);
  curY += (penutupLines.length * 4.6) + 8;

  // 8. Tanda Tangan Atasan & Pure QR Code
  const ttdLeft = pageW - mr - 78;
  doc.text("Ditetapkan di : Sengeti", ttdLeft, curY);
  curY += 4.6;
  const tglIndo = docxRes.indoDate || data.TTL || data.tanggal || "";
  doc.text("Pada tanggal  : " + tglIndo, ttdLeft, curY);
  curY += 5;

  doc.setFont("times", "bold");
  const jabAtasan = (data.j_atasan || "KEPALA OPD").toUpperCase();
  const jabLines = doc.splitTextToSize(jabAtasan, 78);
  doc.text(jabLines, ttdLeft, curY);
  curY += (jabLines.length * 4.4) + 2;

  // Pure QR Code TTE Verification (25x25mm)
  const qrSize = 25;
  const qrX = ttdLeft + 8;
  const targetVerifyUrl = data.verify_url || (data.docId ? ("https://tugasku-bagor.web.app/?v=" + data.docId) : "https://tugasku-bagor.web.app");
  const qrBase64 = docxRes.qrCodeImageBase64 || await generateQrCodeBase64(targetVerifyUrl);
  doc.addImage(qrBase64, "PNG", qrX, curY, qrSize, qrSize);
  // Tambahkan tautan interaktif pada dokumen PDF agar bisa diklik langsung saat dibuka di layar komputer/HP
  doc.link(qrX, curY, qrSize, qrSize, { url: targetVerifyUrl });
  curY += qrSize + 4;

  // Nama Atasan
  doc.setFontSize(10.5);
  doc.setFont("times", "bold");
  const namaAtasan = data.n_atasan || "Nama Atasan";
  doc.text(namaAtasan, ttdLeft, curY);
  const namaAtasanW = doc.getTextWidth(namaAtasan);
  doc.setLineWidth(0.3);
  doc.line(ttdLeft, curY + 0.8, ttdLeft + namaAtasanW, curY + 0.8);

  curY += 4.5;
  doc.setFont("times", "normal");
  if (data.p_atasan) {
    doc.text(data.p_atasan, ttdLeft, curY);
    curY += 4.5;
  }
  const rawNip = data.nip_atasan || "";
  const nipAtasan = rawNip ? (rawNip.startsWith("NIP") ? rawNip : "NIP. " + rawNip) : "-";
  doc.text(nipAtasan, ttdLeft, curY);

  const uri = doc.output("datauristring");
  const base64 = uri.split(",")[1];

  return {
    fileContent: base64,
    filename: "Surat_Tugas_" + (data.nama || "Dokumen").replace(/\s+/g, "_") + ".pdf"
  };
}

// 4. Official PDF Generator for Surat Tugas (strictly from ACTIVE template)
window.generateSptPdf = async function(data, customTemplate) {
  // 1. Dapatkan berkas Word yang sudah diisi seluruh tag template aktif
  const docxRes = await window.generateSptDocx(data, customTemplate);
  
  // 2. Render ke format resmi PDF berbasis vektor berpresisi tinggi
  return await renderTemplateDrivenVectorPdf(data, docxRes);
};

// 4. Sample / Preview Generator for Admin Testing (Generates QR Code preview)
window.generateSampleSptDocx = async function(customTemplate) {
  const sampleData = {
    unit_kerja: "Bagian Organisasi Sekretariat Daerah",
    nama: "Budi Santoso, S.Kom",
    pangkat: "Penata Muda - III/a",
    nip: "199012312015031001",
    jabatan: "Analis Kebijakan Ahli Pertama",
    no_hp: "081234567890",
    email: "budi.organisasi@gmail.com",
    j_atasan: "Kepala Bagian Organisasi",
    n_atasan: "Drs. H. Ahmad Fauzi, M.Si",
    nip_atasan: "197508152000031002",
    p_atasan: "Pembina Tingkat I - IV/b",
    perihal: "Uji Coba Preview Format Template SPT SIMONA",
    nomor_spt: "NOMOR : 090/001/SPT/SETDA/2026",
    nomor_urut: "001",
    kode_opd: "SETDA",
    tahun: "2026",
    dasar_spt: "1. Peraturan Menteri Pendayagunaan Aparatur Negara dan Reformasi Birokrasi Nomor 1 Tahun 2023 tentang Jabatan Fungsional;\n2. Peraturan Daerah Kabupaten Muaro Jambi Nomor 5 Tahun 2021 tentang Perangkat Daerah.",
    verify_url: "https://tugasku-bagor.web.app/?v=SAMPLE_PREVIEW"
  };

  const res = await window.generateSptDocx(sampleData, customTemplate);
  res.filename = "PREVIEW_SAMPLE_SPT.docx";
  return res;
};

window.SYSTEM_TAG_LIST = SYSTEM_TAG_LIST;
window.generateQrCodeBase64 = generateQrCodeBase64;
