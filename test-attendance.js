// Automated tests for attendance logic & absent OPD summary
const assert = require('assert');

console.log('--- RUNNING ATTENDANCE LOGIC TESTS ---');

// Test 1: ID generation format
function generatePresensiId(kegiatan, nip) {
  return encodeURIComponent(kegiatan).replace(/%/g, '_') + "_" + String(nip).trim();
}

const id1 = generatePresensiId("SPT Rekon TPP dan SIMONA", "198801012010011002");
assert.strictEqual(id1, "SPT_20Rekon_20TPP_20dan_20SIMONA_198801012010011002");
console.log('✓ Test 1 Passed: Idempotent presensi ID generation');

// Test 2: Absent OPD calculation
const mockSianjabUnits = [
  { id: 1, nama: "Dinas Pendidikan dan Kebudayaan", parentId: null },
  { id: 2, nama: "Dinas Kesehatan", parentId: null },
  { id: 3, nama: "Badan Kepegawaian Daerah", parentId: null },
  { id: 4, nama: "Kecamatan Sekernan", parentId: null },
  { id: 5, nama: "Kecamatan Jaluko", parentId: null },
  { id: 6, nama: "Puskesmas Sengeti", parentId: 2 } // Sub unit - should be ignored in main OPD list
];

const mockAttendance = [
  { nip: "198801012010011002", opd: "Dinas Pendidikan dan Kebudayaan" },
  { nip: "199002022015021001", opd: "Dinas Kesehatan" },
  { nip: "199503032020031002", opd: "Dinas Kesehatan" } // 2 attendees from same OPD
];

// Calculation logic
const mainOpds = mockSianjabUnits.filter(u => !u.parentId).map(u => u.nama).sort((a, b) => a.localeCompare(b));
assert.strictEqual(mainOpds.length, 5);

const attendedOpds = new Set(mockAttendance.map(a => a.opd));
assert.strictEqual(attendedOpds.size, 2);

const absentOpds = mainOpds.filter(opd => !attendedOpds.has(opd));
assert.strictEqual(absentOpds.length, 3);
assert.deepStrictEqual(absentOpds, ["Badan Kepegawaian Daerah", "Kecamatan Jaluko", "Kecamatan Sekernan"]);

const percent = Math.round(((mainOpds.length - absentOpds.length) / mainOpds.length) * 100);
assert.strictEqual(percent, 40); // 2 out of 5 = 40%
console.log('✓ Test 2 Passed: Absent OPD calculation & attendance percentage (40%)');

// Test 3: WhatsApp text formatter
function formatWhatsAppText(kegiatan, stats, absentList) {
  let msg = `*REKAPITULASI PRESENSI KEGIATAN*\n`;
  msg += `📌 Kegiatan: *${kegiatan}*\n`;
  msg += `📊 Tingkat Kehadiran: *${stats.hadir} dari ${stats.total} OPD* (${stats.percent}%)\n`;
  msg += `👥 Total Peserta Hadir: *${stats.totalPeserta} orang*\n\n`;

  if (absentList.length === 0) {
    msg += `✅ *Alhamdulillah, 100% seluruh OPD telah hadir!*\n`;
  } else {
    msg += `⚠️ *DAFTAR OPD YANG BELUM HADIR (${absentList.length} OPD):*\n`;
    absentList.forEach((opd, i) => {
      msg += `${i + 1}. ${opd}\n`;
    });
  }
  return msg;
}

const waMessage = formatWhatsAppText(
  "Bimtek SIMONA",
  { total: 5, hadir: 2, percent: 40, totalPeserta: 3 },
  absentOpds
);
assert(waMessage.includes("*Bimtek SIMONA*"));
assert(waMessage.includes("2 dari 5 OPD"));
assert(waMessage.includes("1. Badan Kepegawaian Daerah"));
assert(waMessage.includes("3. Kecamatan Sekernan"));
console.log('✓ Test 3 Passed: WhatsApp message generator formatting');

// Test 4: CSV formatting & NIP safety
const testRecord = {
  nip: "198801012010011002",
  nama: 'Ahmad "Fauzi", S.Kom',
  opd: "Dinas Pendidikan"
};
const safeCsvRow = [
  1,
  `"${testRecord.nama.replace(/"/g, '""')}"`,
  `'${testRecord.nip}`,
  `"${testRecord.opd.replace(/"/g, '""')}"`
].join(",");

assert.strictEqual(safeCsvRow, '1,"Ahmad ""Fauzi"", S.Kom",\'198801012010011002,"Dinas Pendidikan"');
console.log('✓ Test 4 Passed: CSV quoting and NIP prefix preservation');

console.log('--- ALL TESTS PASSED SUCCESSFULLY! ---');
