// ==========================================
// CONFIGURATION
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
    var integrasi = e.parameter.integrasi || "SIANJAB";
    
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
      "NIP Atasan", "TTD", "Integrasi", "Tahun"
    ];
    sheet1.appendRow(headers);
    sheet1.getRange("1:1").setFontWeight("bold").setBackground("#f1f5f9");
  }
  
  // 2. Init Config_Kegiatan
  var configSheet = ss.getSheetByName("Config_Kegiatan");
  if (!configSheet) {
    configSheet = ss.insertSheet("Config_Kegiatan");
    var headers = ["Nama Kegiatan", "Integrasi", "Status", "Batas Tanggal / Deadline", "Dasar SPT"];
    configSheet.appendRow(headers);
    configSheet.getRange("1:1").setFontWeight("bold").setBackground("#f1f5f9");
    
    // Add default values
    var defaults = [
      ["SPT Rekon TPP dan SIMONA", "SITPP", "Aktif", "6 Februari 2026", "Surat Sekretariat Daerah Nomor : 060/   /Org tanggal   2026 perihal SPT Rekon TPP dan SIMONA"],
      ["Lainnya", "None", "Aktif", "Tanpa Batas", ""]
    ];
    for (var i = 0; i < defaults.length; i++) {
      configSheet.appendRow(defaults[i]);
    }
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
    list.push({
      nama: row[0],
      integrasi: row[1],
      status: row[2],
      deadline: row[3],
      dasar: row[4]
    });
  }
  return list;
}

function saveKegiatan(kegiatan) {
  var ss = getDb();
  var sheet = ss.getSheetByName("Config_Kegiatan");
  
  // Append new kegiatan
  sheet.appendRow([
    kegiatan.nama,
    kegiatan.integrasi,
    kegiatan.status,
    kegiatan.deadline,
    kegiatan.dasar
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
  
  // Extract Base64 Signature Content for spreadsheet row
  var ttdB64 = "";
  if (data.signature_data && data.signature_data.indexOf("data:image/png;base64,") === 0) {
    ttdB64 = data.signature_data.split(",")[1];
  }
  
  // Append to spreadsheet row
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
    currentYear
  ]);
  
  // If integration is SIANJAB, register user in SIANJAB automatically
  var registerResult = null;
  if (data.integrasi && data.integrasi.toUpperCase() === "SIANJAB") {
    var sianjabUrl = "https://script.google.com/macros/s/AKfycbycp3NZVvZ4n1X_OmkCVtQVNrja-n7x-TYh1Fx1o4nIkCKakWf_to5AXOiBB8horXMPhg/exec?action=autoRegisterOperator";
    var payload = {
      nip: data.nip,
      nama: data.nama,
      email: data.email,
      opdName: data.unit_kerja,
      token: "sianjab_secure_token_abc123"
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
      Logger.log("SIANJAB Auto-Register Result: " + responseText);
    } catch (e) {
      Logger.log("Failed to register in SIANJAB: " + e.toString());
    }
  }

  // Handle DOCX document generation
  var resBlob = generateDocxBlob(data);
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
