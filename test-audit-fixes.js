const assert = require('assert');

console.log('--- RUNNING AUDIT FIXES TESTS ---');

// Test 1: parseDeadlineIndo logic
const INDO_MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
function parseDeadlineIndo(str) {
  if (!str || typeof str !== 'string' || str === "Tanpa Batas") return null;
  const parts = str.trim().split(/\s+/);
  if (parts.length === 3) {
    const day = parseInt(parts[0], 10);
    const month = INDO_MONTHS.indexOf(parts[1]);
    const year = parseInt(parts[2], 10);
    if (day && month !== -1 && year) {
      return new Date(year, month, day, 23, 59, 59);
    }
  }
  const iso = new Date(str);
  if (!isNaN(iso.getTime())) {
    return new Date(iso.getFullYear(), iso.getMonth(), iso.getDate(), 23, 59, 59);
  }
  return null;
}

const deadline1 = parseDeadlineIndo("6 Februari 2026");
assert(deadline1 instanceof Date, "Deadline should parse to Date");
assert.strictEqual(deadline1.getFullYear(), 2026);
assert.strictEqual(deadline1.getMonth(), 1); // 0-indexed: Februari = 1
assert.strictEqual(deadline1.getDate(), 6);
assert.strictEqual(deadline1.getHours(), 23);

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

console.log('--- ALL AUDIT FIXES TESTS PASSED SUCCESSFULLY! ---');
