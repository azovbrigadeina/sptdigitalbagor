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

// Test 5: Daftar OPD/unit kerja belum mengirim SPT (termasuk sub unit & exclusion)
function normalizeUnitName(name) {
  return String(name || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

function calculateSptCompliance(units, submissions, kegiatan, excludedKeys) {
  const excluded = new Set(Array.isArray(excludedKeys) ? excludedKeys : []);
  const allUnits = units
    .map(u => ({ opd: u.nama.trim(), key: normalizeUnitName(u.nama), sub: !!u.parentId }))
    .filter(u => !excluded.has(u.key))
    .sort((a, b) => a.opd.localeCompare(b.opd));
  const submissionsForKeg = submissions.filter(s => s.perihal === kegiatan);
  const countByKey = new Map();
  submissionsForKeg.forEach(s => {
    const key = normalizeUnitName(s.unitKerja);
    if (key) countByKey.set(key, (countByKey.get(key) || 0) + 1);
  });
  const monitoredKeys = new Set(allUnits.map(u => u.key));
  const sudah = [];
  const belum = [];
  allUnits.forEach(u => {
    const jumlah = countByKey.get(u.key) || 0;
    if (jumlah > 0) sudah.push({ opd: u.opd, sub: u.sub, jumlah });
    else belum.push({ opd: u.opd, sub: u.sub });
  });
  return {
    total: allUnits.length,
    sudah: sudah,
    belum: belum,
    percent: allUnits.length > 0 ? Math.round((sudah.length / allUnits.length) * 100) : 0,
    totalSpt: submissionsForKeg.filter(s => monitoredKeys.has(normalizeUnitName(s.unitKerja))).length
  };
}

const sptSubmissions = [
  { perihal: "Bimtek SIMONA", unitKerja: "Dinas Pendidikan dan Kebudayaan" },
  { perihal: "Bimtek SIMONA", unitKerja: "  dinas kesehatan  " }, // beda spasi & huruf besar/kecil
  { perihal: "Bimtek SIMONA", unitKerja: "Puskesmas Sengeti" }, // sub unit, ikut dipantau
  { perihal: "Kegiatan Lain", unitKerja: "Badan Kepegawaian Daerah" } // kegiatan berbeda
];

const sptCompliance = calculateSptCompliance(mockSianjabUnits, sptSubmissions, "Bimtek SIMONA");
assert.strictEqual(sptCompliance.total, 6);
assert.strictEqual(sptCompliance.totalSpt, 3);
assert.deepStrictEqual(sptCompliance.sudah.map(x => x.opd), ["Dinas Kesehatan", "Dinas Pendidikan dan Kebudayaan", "Puskesmas Sengeti"]);
assert.deepStrictEqual(sptCompliance.sudah.map(x => x.sub), [false, false, true]);
assert.deepStrictEqual(sptCompliance.belum.map(x => x.opd), ["Badan Kepegawaian Daerah", "Kecamatan Jaluko", "Kecamatan Sekernan"]);
assert.strictEqual(sptCompliance.percent, 50);

const excludedCompliance = calculateSptCompliance(
  mockSianjabUnits,
  sptSubmissions,
  "Bimtek SIMONA",
  [normalizeUnitName("Puskesmas Sengeti")]
);
assert.strictEqual(excludedCompliance.total, 5);
assert.strictEqual(excludedCompliance.totalSpt, 2);
assert.strictEqual(excludedCompliance.percent, 40);
assert(!excludedCompliance.sudah.some(x => x.opd === "Puskesmas Sengeti"));
assert(!excludedCompliance.belum.some(x => x.opd === "Puskesmas Sengeti"));
console.log('✓ Test 5 Passed: Kepatuhan SPT mencakup sub unit dan menghormati exclusion (50% -> 40%)');

// Test 6: Formatter laporan WhatsApp untuk pimpinan
function formatSptWhatsAppText(kegiatan, deadline, stats, belumList) {
  let msg = `*LAPORAN KEPATUHAN PENGIRIMAN SPT*\n`;
  msg += `📌 Kegiatan: *${kegiatan}*\n`;
  if (deadline && deadline !== 'Tanpa Batas') msg += `🗓️ Batas Waktu: *${deadline}*\n`;
  msg += `📊 Kepatuhan Unit Kerja: *${stats.sudah} dari ${stats.total} unit* (${stats.percent}%)\n`;
  msg += `📨 Total SPT Masuk: *${stats.totalSpt} dokumen*\n\n`;
  if (belumList.length === 0) {
    msg += `✅ *Seluruh unit kerja telah mengirimkan SPT untuk kegiatan ini.*\n`;
  } else {
    msg += `⚠️ *DAFTAR OPD / UNIT KERJA YANG BELUM MENGIRIM SPT (${belumList.length} unit):*\n`;
    belumList.forEach((item, i) => { msg += `${i + 1}. ${item.opd}\n`; });
    msg += `\nMohon unit kerja tersebut segera menindaklanjuti pengiriman SPT.\n`;
  }
  return msg;
}

const sptWaMessage = formatSptWhatsAppText(
  "Bimtek SIMONA",
  "6 Februari 2026",
  { total: 6, sudah: 3, percent: 50, totalSpt: 3 },
  sptCompliance.belum
);
assert(sptWaMessage.includes("*LAPORAN KEPATUHAN PENGIRIMAN SPT*"));
assert(sptWaMessage.includes("*Bimtek SIMONA*"));
assert(sptWaMessage.includes("*6 Februari 2026*"));
assert(sptWaMessage.includes("3 dari 6 unit"));
assert(sptWaMessage.includes("*3 dokumen*"));
assert(sptWaMessage.includes("1. Badan Kepegawaian Daerah"));
assert(sptWaMessage.includes("3. Kecamatan Sekernan"));
assert(sptWaMessage.includes("Mohon unit kerja tersebut segera menindaklanjuti"));

const sptWaComplete = formatSptWhatsAppText("Bimtek SIMONA", "Tanpa Batas", { total: 6, sudah: 6, percent: 100, totalSpt: 6 }, []);
assert(sptWaComplete.includes("Seluruh unit kerja telah mengirimkan SPT"));
assert(!sptWaComplete.includes("Batas Waktu"));
console.log('✓ Test 6 Passed: Format laporan WhatsApp daftar unit belum kirim SPT');

// Test 7: Formatter laporan WhatsApp unit yang sudah mengirim SPT (dengan jumlah dokumen)
function formatSudahSptWhatsAppText(kegiatan, stats, sudahList) {
  let msg = `*LAPORAN OPD / UNIT KERJA YANG SUDAH MENGIRIM SPT*\n`;
  msg += `📌 Kegiatan: *${kegiatan}*\n`;
  msg += `📊 Kepatuhan Unit Kerja: *${stats.sudah} dari ${stats.total} unit* (${stats.percent}%)\n`;
  msg += `📨 Total SPT Masuk: *${stats.totalSpt} dokumen*\n\n`;
  if (sudahList.length === 0) {
    msg += `ℹ️ *Belum ada unit kerja yang mengirimkan SPT untuk kegiatan ini.*\n`;
  } else {
    msg += `✅ *DAFTAR OPD / UNIT KERJA YANG SUDAH MENGIRIM SPT (${sudahList.length} unit):*\n`;
    sudahList.forEach((item, i) => { msg += `${i + 1}. ${item.opd} — ${item.jumlah} SPT\n`; });
  }
  return msg;
}

const sudahWaMessage = formatSudahSptWhatsAppText(
  "Bimtek SIMONA",
  { total: 6, sudah: 3, percent: 50, totalSpt: 3 },
  sptCompliance.sudah
);
assert(sudahWaMessage.includes("*LAPORAN OPD / UNIT KERJA YANG SUDAH MENGIRIM SPT*"));
assert(sudahWaMessage.includes("1. Dinas Kesehatan — 1 SPT"));
assert(sudahWaMessage.includes("2. Dinas Pendidikan dan Kebudayaan — 1 SPT"));
assert(sudahWaMessage.includes("3. Puskesmas Sengeti — 1 SPT"));
assert(sudahWaMessage.includes("3 dari 6 unit"));
const sudahWaKosong = formatSudahSptWhatsAppText("Bimtek SIMONA", { total: 6, sudah: 0, percent: 0, totalSpt: 0 }, []);
assert(sudahWaKosong.includes("Belum ada unit kerja yang mengirimkan SPT"));
console.log('✓ Test 7 Passed: Format laporan WhatsApp daftar unit sudah kirim SPT');

// Test 8: Formatter laporan lengkap (sudah + belum) dengan pengelompokan utama/sub unit
function formatLaporanLengkapSpt(kegiatan, stats, sudahList, belumList) {
  const formatUnitSection = (list, withCount) => {
    const utama = list.filter(item => !item.sub);
    const sub = list.filter(item => item.sub);
    let section = '';
    let n = 0;
    if (utama.length > 0) {
      if (sub.length > 0) section += `*Unit Kerja Utama (${utama.length}):*\n`;
      utama.forEach(item => {
        n++;
        section += withCount ? `${n}. ${item.opd} — ${item.jumlah} SPT\n` : `${n}. ${item.opd}\n`;
      });
    }
    if (sub.length > 0) {
      if (utama.length > 0) section += `\n*Sub Unit Kerja (${sub.length}):*\n`;
      sub.forEach(item => {
        n++;
        section += withCount ? `${n}. ${item.opd} — ${item.jumlah} SPT\n` : `${n}. ${item.opd}\n`;
      });
    }
    return section;
  };

  let msg = `*LAPORAN LENGKAP PENGIRIMAN SPT PER OPD / UNIT KERJA*\n`;
  msg += `📌 Kegiatan: *${kegiatan}*\n`;
  msg += `📊 Kepatuhan Unit Kerja: *${stats.sudah} dari ${stats.total} unit* (${stats.percent}%)\n`;
  msg += `📨 Total SPT Masuk: *${stats.totalSpt} dokumen*\n\n`;
  msg += `✅ *OPD / UNIT KERJA YANG SUDAH MENGIRIM SPT (${sudahList.length} unit):*\n`;
  msg += sudahList.length === 0 ? `_Belum ada unit kerja yang mengirimkan SPT._\n` : formatUnitSection(sudahList, true);
  msg += `\n⚠️ *OPD / UNIT KERJA YANG BELUM MENGIRIM SPT (${belumList.length} unit):*\n`;
  if (belumList.length === 0) {
    msg += `✅ _Seluruh unit kerja telah mengirimkan SPT untuk kegiatan ini._\n`;
  } else {
    msg += formatUnitSection(belumList, false);
    msg += `\nMohon unit kerja tersebut segera menindaklanjuti pengiriman SPT.\n`;
  }
  return msg;
}

const lengkapWa = formatLaporanLengkapSpt(
  "Bimtek SIMONA",
  { total: 6, sudah: 3, percent: 50, totalSpt: 3 },
  sptCompliance.sudah,
  sptCompliance.belum
);
assert(lengkapWa.includes("*LAPORAN LENGKAP PENGIRIMAN SPT PER OPD / UNIT KERJA*"));
assert(lengkapWa.includes("*OPD / UNIT KERJA YANG SUDAH MENGIRIM SPT (3 unit):*"));
assert(lengkapWa.includes("*Unit Kerja Utama (2):*"));
assert(lengkapWa.includes("*Sub Unit Kerja (1):*"));
assert(lengkapWa.includes("3. Puskesmas Sengeti — 1 SPT"));
assert(lengkapWa.includes("*OPD / UNIT KERJA YANG BELUM MENGIRIM SPT (3 unit):*"));
assert(lengkapWa.includes("1. Badan Kepegawaian Daerah"));
assert(lengkapWa.includes("3. Kecamatan Sekernan"));
assert.strictEqual(lengkapWa.indexOf("SUDAH MENGIRIM") < lengkapWa.indexOf("BELUM MENGIRIM"), true);

const lengkapWaTanpaSub = formatLaporanLengkapSpt(
  "Bimtek SIMONA",
  { total: 5, sudah: 2, percent: 40, totalSpt: 2 },
  excludedCompliance.sudah,
  excludedCompliance.belum
);
assert(lengkapWaTanpaSub.includes("*OPD / UNIT KERJA YANG SUDAH MENGIRIM SPT (2 unit):*"));
assert(!lengkapWaTanpaSub.includes("Sub Unit Kerja"));
assert(!lengkapWaTanpaSub.includes("Puskesmas Sengeti"));

const lengkapWaKosong = formatLaporanLengkapSpt("Bimtek SIMONA", { total: 1, sudah: 0, percent: 0, totalSpt: 0 }, [], [{ opd: "Dinas Kesehatan", sub: false }]);
assert(lengkapWaKosong.includes("Belum ada unit kerja yang mengirimkan SPT"));
assert(lengkapWaKosong.includes("1. Dinas Kesehatan"));
console.log('✓ Test 8 Passed: Format laporan lengkap (utama & sub unit, sudah & belum)');

// Test 9: Waktu "Data per" memakai jam server, bukan jam komputer yang meleset
function formatWibDate(date) {
  return date.toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Asia/Jakarta' });
}
function formatWibTimestamp(date) {
  const jam = date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Jakarta' });
  return `${formatWibDate(date)}, ${jam} WIB`;
}
function resolveReportNow(clientNowMs, serverDateHeader) {
  const serverMs = Date.parse(serverDateHeader);
  const offset = isNaN(serverMs) ? 0 : serverMs - clientNowMs;
  return new Date(clientNowMs + offset);
}

// Komputer admin meleset +1 hari (20 Okt 11.58 WIB), server benar 19 Okt 11.58 WIB
const skewedClientMs = Date.parse('2026-10-20T04:58:00Z');
const serverHeader = 'Mon, 19 Oct 2026 04:58:00 GMT';
assert.strictEqual(formatWibTimestamp(resolveReportNow(skewedClientMs, serverHeader)), '19 Oktober 2026, 11.58 WIB');

// Jam server tidak tersedia -> jatuh ke jam perangkat
assert.strictEqual(formatWibTimestamp(resolveReportNow(skewedClientMs, 'bukan-tanggal')), '20 Oktober 2026, 11.58 WIB');

// Format jam selalu WIB walau perangkat memakai zona waktu lain
const utcMorning = new Date('2026-10-19T00:05:00Z');
assert.strictEqual(formatWibTimestamp(utcMorning), '19 Oktober 2026, 07.05 WIB');

// Tanggal ISO untuk nama file ekspor & input tanggal juga mengikuti WIB
function formatWibIsoDate(date) {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Jakarta', year: 'numeric', month: '2-digit', day: '2-digit'
  }).formatToParts(date);
  const pick = type => (parts.find(p => p.type === type) || {}).value || '';
  return `${pick('year')}-${pick('month')}-${pick('day')}`;
}
assert.strictEqual(formatWibIsoDate(resolveReportNow(skewedClientMs, serverHeader)), '2026-10-19');
assert.strictEqual(formatWibIsoDate(utcMorning), '2026-10-19');
// 18:30 UTC sudah 01:30 WIB tanggal berikutnya
assert.strictEqual(formatWibIsoDate(new Date('2026-10-18T18:30:00Z')), '2026-10-19');
console.log('✓ Test 9 Passed: Waktu laporan, nama file ekspor, dan input tanggal mengikuti jam server WIB');

console.log('--- ALL TESTS PASSED SUCCESSFULLY! ---');
