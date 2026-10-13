// ============================================================================
// DEPRECATED / PENSIUN (2026-10-12):
// Backend Google Apps Script (GAS) dan Google Sheets ini resmi DIPENSIUNKAN.
// Arsitektur sistem telah beralih 100% ke Pure Firebase (Firestore & Hosting).
// Berkas ini dipertahankan hanya sebagai arsip riwayat teknis.
// Source of truth runtime berada di: build.js, public/index.html, public/presensi.html.
// ============================================================================

// ==========================================
// CONFIGURATION (HISTORICAL / ARCHIVED)
// ==========================================
var SPREADSHEET_ID = "1hA68rgMDtbX9ySdOI5TF5CUypzO5vJKHHIPAVjTk798";

// Gantilah TEMPLATE_DOC_ID dengan ID Google Doc Template SPT Anda yang sudah diupload ke Google Drive
// Contoh: var TEMPLATE_DOC_ID = "1aBcDeFgHiJkLmNoPqRsTuVwXyZ";
var TEMPLATE_DOC_ID = "1v4wm_94T3TAzeUBrxdnoW2OXLLXe5KCKRRnx6CjcIxw"; 

// Password untuk masuk ke Panel Admin
var ADMIN_PASSWORD = "adminbagor123";

// Function to force prompt the OAuth authorization dialog in the online editor
function triggerAuthorization() {
  Logger.log("Triggering auth dialog...");
  var doc = DocumentApp.create("Dummy Doc for Auth");
  DocumentApp.openById(doc.getId());
  DriveApp.getFileById(doc.getId());
  SpreadsheetApp.getActiveSpreadsheet();
  UrlFetchApp.fetch("https://www.google.com");
  // Clean up
  DriveApp.getFileById(doc.getId()).setTrashed(true);
  Logger.log("Auth success!");
}

// ==========================================
// CORE WEB SERVER
// ==========================================
function doGet(e) {
  // Check if it's an API request to verify SPT status
  if (e && e.parameter && e.parameter.action === "checkSpt") {
    var token = e.parameter.token;
    var nip = e.parameter.nip;
    var email = e.parameter.email;
    var opd = e.parameter.opd;
    var integrasi = e.parameter.integrasi || "SI-PRABU";
    
    // Security check - pre-shared secret token
    var EXPECTED_TOKEN = "sianjab_secure_token_abc123";
    if (token !== EXPECTED_TOKEN) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error",
        message: "Invalid token"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    if (!nip && !email && !opd) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error",
        message: "Parameter 'nip', 'email', or 'opd' is required"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    var ss = getDb();
    var sheet = ss.getSheetByName("Sheet1");
    var values = sheet.getDataRange().getValues();
    var hasSubmitted = false;
    var submissionData = null;
    
    // Helper to normalize OPD name
    function normalize(str) {
      if (!str) return "";
      return String(str)
        .toLowerCase()
        .replace(/[\s\r\n\t]+/g, "")
        .replace(/[^a-z0-9]/g, "")
        .replace(/rumahsakitumumdaerah/g, "rs")
        .replace(/rumahsakit/g, "rs")
        .replace(/rsud/g, "rs")
        .replace(/dan/g, "");
    }
    
    var targetNorm = opd ? normalize(opd) : "";
    
    for (var i = 1; i < values.length; i++) {
      var rowNip = String(values[i][4]).trim();
      var rowEmail = String(values[i][5]).trim();
      var rowOpd = String(values[i][2]).trim();
      var rowIntegrasi = String(values[i][11]).trim();
      
      var match = false;
      if (rowIntegrasi.toUpperCase() === integrasi.toUpperCase()) {
        if (opd) {
          var rowNorm = normalize(rowOpd);
          match = (rowNorm === targetNorm || rowNorm.indexOf(targetNorm) !== -1 || targetNorm.indexOf(rowNorm) !== -1);
        } else if (email) {
          match = (rowEmail.toLowerCase() === email.toLowerCase());
        } else if (nip) {
          match = (rowNip === nip);
        }
      }
      
      if (match) {
        hasSubmitted = true;
        submissionData = {
          waktu: values[i][0] instanceof Date ? Utilities.formatDate(values[i][0], "GMT+7", "yyyy-MM-dd HH:mm:ss") : values[i][0],
          perihal: values[i][1],
          unitKerja: values[i][2],
          namaAdmin: values[i][3],
          nipAdmin: values[i][4],
          email: values[i][5]
        };
        break; // Found the record, stop searching
      }
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      hasSubmitted: hasSubmitted,
      data: submissionData
    })).setMimeType(ContentService.MimeType.JSON);
  }

  var template = HtmlService.createTemplateFromFile('Index');
  template.verifyToken = (e && e.parameter && e.parameter.v) ? e.parameter.v : "";
  try {
    template.webAppUrl = ScriptApp.getService().getUrl();
  } catch(err) {
    template.webAppUrl = "";
  }
  return template.evaluate()
    .setTitle('📝 Kirim Surat Tugas Digital')
    .setSandboxMode(HtmlService.SandboxMode.IFRAME)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

// Helper to get Sheet DB
function getDb() {
  var ss;
  try {
    ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  } catch(e) {
    ss = SpreadsheetApp.getActiveSpreadsheet();
  }
  return ss;
}

// ==========================================
// INITIALIZATION & CONFIG KEGIATAN DATABASE
// ==========================================
function initSheets() {
  var ss = getDb();
  
  // 1. Init Sheet1 (Submisi)
  var sheet1 = ss.getSheetByName("Sheet1");
  if (!sheet1) {
    sheet1 = ss.insertSheet("Sheet1");
    var headers = [
      "Waktu", "Perihal", "Unit Kerja", "Nama Admin", "NIP Admin", 
      "Email", "Nama Atasan", "Jabatan Atasan", "Pangkat Gol Atasan", 
      "NIP Atasan", "TTD", "Integrasi", "Tahun", "Nomor SPT", "Nomor Urut", "Kode OPD"
    ];
    sheet1.appendRow(headers);
    sheet1.getRange("1:1").setFontWeight("bold").setBackground("#f1f5f9");
  } else {
    // Pastikan header baru ada jika sheet sudah dibuat sebelumnya
    var lastCol = sheet1.getLastColumn();
    if (lastCol <= 13) {
      sheet1.getRange(1, 14).setValue("Nomor SPT");
      sheet1.getRange(1, 15).setValue("Nomor Urut");
      sheet1.getRange(1, 16).setValue("Kode OPD");
    }
  }
  
  // 2. Init Config_Kegiatan
  var configSheet = ss.getSheetByName("Config_Kegiatan");
  if (!configSheet) {
    configSheet = ss.insertSheet("Config_Kegiatan");
    var headers = ["Nama Kegiatan", "Integrasi", "Status", "Batas Tanggal / Deadline", "Dasar SPT", "Auto Nomor", "Format Nomor"];
    configSheet.appendRow(headers);
    configSheet.getRange("1:1").setFontWeight("bold").setBackground("#f1f5f9");
    
    // Add default values
    var defaults = [
      ["SPT Rekon TPP dan SIMONA", "Gentala TPP EM-JE", "Aktif", "6 Februari 2026", "Surat Sekretariat Daerah Nomor : 060/   /Org tanggal   2026 perihal SPT Rekon TPP dan SIMONA", "Aktif", "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}"],
      ["Lainnya", "None", "Aktif", "Tanpa Batas", "", "Aktif", "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}"]
    ];
    for (var i = 0; i < defaults.length; i++) {
      configSheet.appendRow(defaults[i]);
    }
  }

  // 3. Init Config_OPD (Hybrid Mapping)
  var opdSheet = ss.getSheetByName("Config_OPD");
  if (!opdSheet) {
    opdSheet = ss.insertSheet("Config_OPD");
    var opdHeaders = ["ID OPD", "Nama OPD", "Kode SIANJAB", "Kode Custom", "Waktu Update"];
    opdSheet.appendRow(opdHeaders);
    opdSheet.getRange("1:1").setFontWeight("bold").setBackground("#f1f5f9");
  }
}

// ==========================================
// READ / WRITE KEGIATAN
// ==========================================
function getKegiatanList() {
  initSheets();
  var ss = getDb();
  var sheet = ss.getSheetByName("Config_Kegiatan");
  var data = sheet.getDataRange().getValues();
  
  var list = [];
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var isAuto = (row[5] === undefined || row[5] === "" || row[5] === "Aktif" || row[5] === true || row[5] === "true");
    list.push({
      nama: row[0],
      integrasi: row[1],
      status: row[2],
      deadline: row[3],
      dasar: row[4],
      autoNomor: isAuto,
      formatNomor: row[6] || "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}"
    });
  }
  return list;
}

function saveKegiatan(kegiatan) {
  initSheets();
  var ss = getDb();
  var sheet = ss.getSheetByName("Config_Kegiatan");
  var data = sheet.getDataRange().getValues();
  var autoVal = kegiatan.autoNomor !== false ? "Aktif" : "Nonaktif";
  var formatVal = kegiatan.formatNomor || "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}";
  
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] === kegiatan.nama) {
      sheet.getRange(i + 1, 1, 1, 7).setValues([[
        kegiatan.nama,
        kegiatan.integrasi || "None",
        kegiatan.status || "Aktif",
        kegiatan.deadline || "Tanpa Batas",
        kegiatan.dasar || "",
        autoVal,
        formatVal
      ]]);
      return { status: "success" };
    }
  }

  // Append new kegiatan
  sheet.appendRow([
    kegiatan.nama,
    kegiatan.integrasi || "None",
    kegiatan.status || "Aktif",
    kegiatan.deadline || "Tanpa Batas",
    kegiatan.dasar || "",
    autoVal,
    formatVal
  ]);
  return { status: "success" };
}

function deleteKegiatan(nama) {
  var ss = getDb();
  var sheet = ss.getSheetByName("Config_Kegiatan");
  var data = sheet.getDataRange().getValues();
  
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] === nama) {
      sheet.deleteRow(i + 1);
      return { status: "success" };
    }
  }
  return { status: "error", message: "Kegiatan tidak ditemukan" };
}

// ==========================================
// CONFIG OPD (HYBRID: SIANJAB + OVERRIDE)
// ==========================================
function getOpdConfigList() {
  initSheets();
  var ss = getDb();
  var sheet = ss.getSheetByName("Config_OPD");
  var data = sheet.getDataRange().getValues();
  
  var list = [];
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    list.push({
      id: String(row[0] || ''),
      nama: String(row[1] || ''),
      kodeSianjab: String(row[2] || ''),
      kodeCustom: String(row[3] || ''),
      updatedAt: String(row[4] || '')
    });
  }
  return list;
}

function saveOpdConfig(items) {
  initSheets();
  var ss = getDb();
  var sheet = ss.getSheetByName("Config_OPD");
  var now = Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss");
  
  if (!Array.isArray(items)) {
    items = [items];
  }

  var data = sheet.getDataRange().getValues();
  var mapIndex = {};
  for (var i = 1; i < data.length; i++) {
    var existingId = String(data[i][0] || '').trim();
    var existingName = String(data[i][1] || '').trim();
    if (existingId) mapIndex[existingId] = i + 1;
    if (existingName) mapIndex[existingName] = i + 1;
  }

  items.forEach(function(item) {
    var keyId = String(item.id || '').trim();
    var keyName = String(item.nama || '').trim();
    var rowIndex = (keyId && mapIndex[keyId]) || (keyName && mapIndex[keyName]);

    if (rowIndex) {
      // Update baris yang sudah ada
      sheet.getRange(rowIndex, 1, 1, 5).setValues([[
        item.id || "",
        item.nama || "",
        item.kodeSianjab || "",
        item.kodeCustom || "",
        now
      ]]);
    } else {
      // Baris baru
      sheet.appendRow([
        item.id || "",
        item.nama || "",
        item.kodeSianjab || "",
        item.kodeCustom || "",
        now
      ]);
    }
  });

  return { status: "success" };
}

// ==========================================
// SIANJAB INTEGRATION PROXY
// ==========================================
function getSianjabUnitKerja(forceRefresh) {
  var cache = CacheService.getScriptCache();
  if (!forceRefresh) {
    var cached = cache.get("sianjab_unit_kerja");
    if (cached) {
      try {
        return { success: true, data: JSON.parse(cached), fromCache: true };
      } catch(e) {
        // Cache corrupted, continue fetch
      }
    }
  }

  var props = PropertiesService.getScriptProperties();
  var sianjabBaseUrl = props.getProperty("SIANJAB_API_URL") || "https://script.google.com/macros/s/AKfycbxbuHWzaPOMyEemDcUsYCboqWkE5g1Lq-FFKwA5eNyBbamd41686X1a2m7OIFI-h-yLWw/exec";
  
  var url = sianjabBaseUrl + "?action=getBulkData&entities=unitKerja";
  
  try {
    var response = UrlFetchApp.fetch(url, {
      method: "get",
      muteHttpExceptions: true
    });
    var code = response.getResponseCode();
    var text = response.getContentText();
    var json = null;
    try {
      json = JSON.parse(text);
    } catch(pe) {
      return {
        success: false,
        error: "Respon dari SI-PRABU bukan JSON valid (HTTP " + code + "): " + text.substring(0, 100)
      };
    }
    
    if (json && json.success === true && json.data) {
      var unitList = [];
      if (Array.isArray(json.data.unitKerja)) {
        unitList = json.data.unitKerja;
      } else if (Array.isArray(json.data)) {
        unitList = json.data;
      }
      
      // Simpan di cache selama 3600 detik (1 jam)
      try {
        cache.put("sianjab_unit_kerja", JSON.stringify(unitList), 3600);
      } catch(ce) {
        Logger.log("Gagal menyimpan cache SI-PRABU: " + ce);
      }
      return { success: true, data: unitList };
    } else {
      return {
        success: false,
        error: (json && json.error) ? json.error : ("Gagal memuat data dari SI-PRABU (HTTP " + code + ")")
      };
    }
  } catch(err) {
    Logger.log("Koneksi ke SI-PRABU gagal: " + err.toString());
    return {
      success: false,
      error: "Gagal terhubung ke server SI-PRABU: " + err.toString()
    };
  }
}

// ==========================================
// OPD RESOLUTION HELPER
// ==========================================
function resolveOpdCode_(unitKerjaName, unitKerjaId) {
  try {
    var opdConfigs = getOpdConfigList();
    // 1. Cek langsung di custom config berdasarkan ID atau Nama
    for (var i = 0; i < opdConfigs.length; i++) {
      var c = opdConfigs[i];
      if ((unitKerjaId && String(c.id).trim() === String(unitKerjaId).trim()) || 
          (c.nama && String(c.nama).trim() === String(unitKerjaName).trim())) {
        if (c.kodeCustom && c.kodeCustom.trim()) return c.kodeCustom.trim();
        if (c.kodeSianjab && c.kodeSianjab.trim()) return c.kodeSianjab.trim();
      }
    }

    // 2. Cari di daftar SIANJAB unit kerja dan telusuri parent jika merupakan sub unit
    var sianjabRes = getSianjabUnitKerja();
    if (sianjabRes && sianjabRes.success && Array.isArray(sianjabRes.data)) {
      var units = sianjabRes.data;
      var target = null;
      for (var u = 0; u < units.length; u++) {
        var un = units[u];
        if ((unitKerjaId && String(un.id).trim() === String(unitKerjaId).trim()) || 
            (un.nama && String(un.nama).trim() === String(unitKerjaName).trim())) {
          target = un;
          break;
        }
      }

      // Telusuri ke parent root OPD jika ada parentId
      var depth = 0;
      while (target && target.parentId && depth < 5) {
        var foundParent = false;
        for (var p = 0; p < units.length; p++) {
          if (String(units[p].id).trim() === String(target.parentId).trim() || 
              String(units[p].nama).trim() === String(target.parentId).trim()) {
            target = units[p];
            foundParent = true;
            break;
          }
        }
        if (!foundParent) break;
        depth++;
      }

      if (target) {
        // Cek kembali apakah root OPD ini memiliki custom override di Config_OPD
        for (var k = 0; k < opdConfigs.length; k++) {
          var cfg = opdConfigs[k];
          if (String(cfg.id).trim() === String(target.id).trim() || 
              String(cfg.nama).trim() === String(target.nama).trim()) {
            if (cfg.kodeCustom && cfg.kodeCustom.trim()) return cfg.kodeCustom.trim();
          }
        }
        if (target.kode && target.kode.trim()) return target.kode.trim();
      }
    }
  } catch(err) {
    Logger.log("Error resolveOpdCode_: " + err.toString());
  }
  return "OPD";
}

// ==========================================
// SUBMISSIONS DATA (ADMIN PANEL)
// ==========================================
function getSubmissionsData() {
  initSheets();
  var ss = getDb();
  var sheet = ss.getSheetByName("Sheet1");
  var values = sheet.getDataRange().getValues();
  
  // Convert datetime objects to string format for JSON serialization
  for (var i = 1; i < values.length; i++) {
    if (values[i][0] instanceof Date) {
      values[i][0] = Utilities.formatDate(values[i][0], "GMT+7", "yyyy-MM-dd HH:mm:ss");
    }
  }
  return values;
}

function deleteSubmission(rowIndex) {
  var ss = getDb();
  var sheet = ss.getSheetByName("Sheet1");
  // Index + 1 because of standard headers
  sheet.deleteRow(rowIndex + 1);
  return { status: "success" };
}

// ==========================================
// MAIN FORM SUBMISSION & DOCX GENERATION
// ==========================================
function submitSptData(data) {
  initSheets();
  var ss = getDb();
  var sheet = ss.getSheetByName("Sheet1");
  
  var now = Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss");
  var currentYear = Utilities.formatDate(new Date(), "GMT+7", "yyyy");
  
  // Lock mechanism untuk menjamin nomor urut FCFS tanpa race condition
  var lock = LockService.getScriptLock();
  var hasLock = false;
  try {
    hasLock = lock.tryLock(15000);
  } catch(e) {
    Logger.log("Gagal memperoleh script lock: " + e.toString());
  }

  var nomorUrutPad = "001";
  var kodeOpd = "OPD";
  var nomorSpt = "";

  try {
    // Hitung nomor urut pendaftaran per 1 kegiatan (FCFS)
    var allValues = sheet.getDataRange().getValues();
    var countPerihal = 0;
    for (var r = 1; r < allValues.length; r++) {
      if (String(allValues[r][1]).trim() === String(data.perihal).trim()) {
        countPerihal++;
      }
    }
    var seqNum = countPerihal + 1;
    nomorUrutPad = ("000" + seqNum).slice(-3); // Format 3-digit: 001, 002, dst.

    // Selesaikan Kode OPD (Hybrid SIANJAB + Override)
    kodeOpd = resolveOpdCode_(data.unit_kerja, data.unit_kerja_id);

    // Dapatkan konfigurasi kegiatan terpilih
    var kegiatanList = getKegiatanList();
    var selectedKegiatan = null;
    for (var k = 0; k < kegiatanList.length; k++) {
      if (kegiatanList[k].nama === data.perihal) {
        selectedKegiatan = kegiatanList[k];
        break;
      }
    }

    var isAuto = (!selectedKegiatan || selectedKegiatan.autoNomor !== false);
    var templatePola = (selectedKegiatan && selectedKegiatan.formatNomor) ? selectedKegiatan.formatNomor : "NOMOR : 090/{nomor}/SPT/{kode_opd}/{tahun}";

    if (isAuto) {
      nomorSpt = templatePola
        .replace(/{nomor}/g, nomorUrutPad)
        .replace(/{kode_opd}/g, kodeOpd)
        .replace(/{tahun}/g, currentYear);
    } else {
      nomorSpt = data.nomor_spt || "";
    }

    data.nomor_spt = nomorSpt;
    data.nomor_urut = nomorUrutPad;
    data.kode_opd = kodeOpd;
    data.tahun = currentYear;

    // Extract Base64 Signature Content for spreadsheet row
    var ttdB64 = "";
    if (data.signature_data && data.signature_data.indexOf("data:image/png;base64,") === 0) {
      ttdB64 = data.signature_data.split(",")[1];
    }
    
    // Append to spreadsheet row (termasuk Nomor SPT, Nomor Urut, Kode OPD)
    sheet.appendRow([
      now,
      data.perihal,
      data.unit_kerja,
      "(" + data.status_pegawai + ") " + data.nama,
      "'" + data.nip,
      data.email,
      data.n_atasan,
      data.j_atasan,
      data.p_atasan,
      "'" + data.nip_atasan,
      ttdB64,
      data.integrasi,
      currentYear,
      nomorSpt,
      nomorUrutPad,
      kodeOpd
    ]);
  } finally {
    if (hasLock) {
      try {
        lock.releaseLock();
      } catch(e) {}
    }
  }
  
  // If integration is SI-PRABU or SIANJAB, register user automatically
  var registerResult = null;
  var isSiPrabu = data.integrasi && (
    data.integrasi.toUpperCase() === "SI-PRABU" || 
    data.integrasi.toUpperCase() === "SIPRABU" || 
    data.integrasi.toUpperCase() === "SIANJAB"
  );
  if (isSiPrabu) {
    var props = PropertiesService.getScriptProperties();
    var sianjabBaseUrl = props.getProperty("SIANJAB_API_URL") || "https://script.google.com/macros/s/AKfycbxbuHWzaPOMyEemDcUsYCboqWkE5g1Lq-FFKwA5eNyBbamd41686X1a2m7OIFI-h-yLWw/exec";
    var sianjabToken = props.getProperty("SIANJAB_TOKEN") || "sianjab_secure_token_abc123";
    var sianjabUrl = sianjabBaseUrl + "?action=autoRegisterOperator";
    var payload = {
      nip: data.nip,
      nama: data.nama,
      email: data.email,
      opdName: data.unit_kerja,
      token: sianjabToken
    };
    
    try {
      var response = UrlFetchApp.fetch(sianjabUrl, {
        method: "post",
        contentType: "application/json",
        payload: JSON.stringify(payload),
        muteHttpExceptions: true
      });
      var responseText = response.getContentText();
      registerResult = JSON.parse(responseText);
      Logger.log("SI-PRABU Auto-Register Result: " + responseText);
    } catch (e) {
      Logger.log("Failed to register in SI-PRABU: " + e.toString());
    }
  }

  // Handle DOCX document generation
  var resBlob = generateDocxBlob(data);
  resBlob.nomor_spt = nomorSpt;
  resBlob.nomor_urut = nomorUrutPad;
  resBlob.kode_opd = kodeOpd;

  if (registerResult && registerResult.success) {
    resBlob.sianjabCreated = true;
    resBlob.sianjabStatus = registerResult.data.status; // "created" or "updated"
  }
  return resBlob;
}

// Document Generation Handler
function generateDocxBlob(data) {
  if (!TEMPLATE_DOC_ID || TEMPLATE_DOC_ID === "MASUKKAN_ID_TEMPLATE_GOOGLE_DOC_DISINI" || TEMPLATE_DOC_ID === "") {
    return { 
      status: "warning", 
      message: "Data berhasil disimpan! Namun download dokumen tidak aktif karena TEMPLATE_DOC_ID belum dikonfigurasi di Code.js oleh Admin." 
    };
  }
  
  try {
    var templateFile = DriveApp.getFileById(TEMPLATE_DOC_ID);
    var docName = "Temp_SPT_" + data.nama.replace(/\s+/g, "_") + "_" + new Date().getTime();
    var tempCopy = templateFile.makeCopy(docName);
    var tempId = tempCopy.getId();
    
    var doc = DocumentApp.openById(tempId);
    var body = doc.getBody();
    
    // Replacement Tags
    var replacements = {
      '{{unitkerja}}': data.unit_kerja || "",
      '{{nama_admin}}': data.nama || "",
      '{{pangkat_admin}}': data.pangkat || "",
      '{{NIP_admin}}': data.nip || "",
      '{{Jabatanadmin}}': data.jabatan || "",
      '{{no_hpadmin}}': data.no_hp || "",
      '{{email_admin}}': data.email || "",
      '{{JABATAN_ATASAN}}': data.j_atasan || "",
      '{{NAMA_ATASAN}}': data.n_atasan || "",
      '{{NIP_ATASAN}}': data.nip_atasan || "",
      '{{PANGKAT_GOL_ATASAN}}': data.p_atasan || "",
      '{{perihal}}': data.perihal || "",
      '{{nomor_spt}}': data.nomor_spt || ("NOMOR : 090/" + (data.nomor_urut || "001") + "/SPT/" + (data.kode_opd || "SETDA") + "/2026"),
      '{{nomor_urut}}': data.nomor_urut || "001",
      '{{kode_opd}}': data.kode_opd || "SETDA",
      '{{tahun}}': data.tahun || "2026",
      '{{TTL}}': getIndoDateString(),
      '{{dasar_spt}}': data.dasar_spt || ""
    };
    
    // Apply Text Replacements
    for (var key in replacements) {
      body.replaceText(key, replacements[key]);
    }
    
    // Handle Signature Image Placement
    if (data.signature_data && data.signature_data.indexOf("data:image/png;base64,") === 0) {
      var searchResult = body.findText('{{ttd}}');
      if (searchResult) {
        var element = searchResult.getElement();
        var textElement = element.asText();
        
        // Remove the {{ttd}} placeholder string
        textElement.setText(textElement.getText().replace('{{ttd}}', ''));
        
        // Convert base64 to image blob
        var base64Data = data.signature_data.split(",")[1];
        var decodedImage = Utilities.base64Decode(base64Data);
        var blob = Utilities.newBlob(decodedImage, MimeType.PNG, "signature.png");
        
        // Insert inline image inside parent paragraph
        var parent = element.getParent();
        var inlineImage;
        if (parent.getType() === DocumentApp.ElementType.PARAGRAPH) {
          inlineImage = parent.asParagraph().appendInlineImage(blob);
        } else {
          inlineImage = body.appendImage(blob);
        }
        
        // Clean professional sizing
        inlineImage.setWidth(160);
        inlineImage.setHeight(115);
      }
    } else {
      // Clear placeholder even if no signature
      body.replaceText('{{ttd}}', '');
    }
    
    doc.saveAndClose();
    
    // Fetch as Microsoft Word DOCX
    var docUrl = "https://docs.google.com/document/d/" + tempId + "/export?format=docx";
    var response = UrlFetchApp.fetch(docUrl, {
      headers: {
        Authorization: "Bearer " + ScriptApp.getOAuthToken()
      },
      muteHttpExceptions: true
    });
    
    var fileBytes = response.getContent();
    var base64Docx = Utilities.base64Encode(fileBytes);
    
    // Delete temp copy
    DriveApp.getFileById(tempId).setTrashed(true);
    
    return {
      status: "success",
      fileContent: base64Docx,
      filename: "SPT_" + data.nama.replace(/\s+/g, "_") + ".docx"
    };
  } catch(e) {
    return {
      status: "error",
      message: "Gagal membuat dokumen: " + e.toString()
    };
  }
}

// Date formatter helper in Indonesian locale
function getIndoDateString() {
  var months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
  var d = new Date();
  return d.getDate() + " " + months[d.getMonth()] + " " + d.getFullYear();
}

// Authentication verification helper for admin login
function checkAdminAuth(password) {
  return password === ADMIN_PASSWORD;
}
