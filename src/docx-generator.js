import PizZip from 'pizzip';
import Docxtemplater from 'docxtemplater';
import ImageModule from 'docxtemplater-image-module-free';

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

const imageOpts = {
  getImage(tagValue) {
    if (!tagValue || typeof tagValue !== 'string' || !tagValue.trim()) {
      return emptyPng.buffer;
    }
    const cleanBase64 = tagValue.replace(/^data:image\/\w+;base64,/, "");
    const bytes = base64ToUint8Array(cleanBase64);
    return bytes.buffer;
  },
  getSize(img, tagValue) {
    if (!tagValue || typeof tagValue !== 'string' || !tagValue.trim()) {
      return [1, 1];
    }
    return [160, 115];
  }
};

window.generateSptDocx = async function(data) {
  const resp = await fetch('/template_spt_simona.docx');
  if (!resp.ok) {
    throw new Error('Gagal memuat template Word (.docx): ' + resp.statusText);
  }
  const arrayBuffer = await resp.arrayBuffer();
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
    ttd: data.signature_data || ""
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
