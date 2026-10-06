import PizZip from 'pizzip';
import Docxtemplater from 'docxtemplater';
import ImageModule from 'docxtemplater-image-module-free';
import QRCode from 'qrcode';

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
  { tag: "PANGKAT_GOL_ATASAN", label: "Pangkat / Golongan Atasan", desc: "Pangkat dan golongan ruang atasan", example: "Pembina Tingkat I - IV/b" },
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

  // Fallback to active template cache if set on window, or default template
  if (!arrayBuffer && window.__activeCustomTemplateBase64) {
    const clean = window.__activeCustomTemplateBase64.replace(/^data:[^;]+;base64,/, "");
    arrayBuffer = base64ToUint8Array(clean).buffer;
  }

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
    ttd: qrCodeImageBase64,
    qrcode: qrCodeImageBase64
  });

  const base64 = doc.getZip().generate({
    type: "base64",
    compression: "DEFLATE"
  });

  return {
    fileContent: base64,
    filename: "SPT_" + (data.nama || "Dokumen").replace(/\s+/g, "_") + ".docx"
  };
};

// 3. Sample / Preview Generator for Admin Testing (Generates QR Code preview)
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
    dasar_spt: "1. Peraturan Menteri Pendayagunaan Aparatur Negara dan Reformasi Birokrasi Nomor 1 Tahun 2023 tentang Jabatan Fungsional;\n2. Peraturan Daerah Kabupaten Muaro Jambi Nomor 5 Tahun 2021 tentang Perangkat Daerah.",
    verify_url: "https://tugasku-bagor.web.app/?v=SAMPLE_PREVIEW"
  };

  const res = await window.generateSptDocx(sampleData, customTemplate);
  res.filename = "PREVIEW_SAMPLE_SPT.docx";
  return res;
};

window.SYSTEM_TAG_LIST = SYSTEM_TAG_LIST;
window.generateQrCodeBase64 = generateQrCodeBase64;
