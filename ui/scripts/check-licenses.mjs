// Lists the licence of every installed npm package (runtime and dev) and fails if any is not permissive.
// Run: npm run licenses   (no extra dependency; reads node_modules/**/package.json)
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const ALLOWED = new Set(["MIT", "ISC", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "0BSD", "BlueOak-1.0.0", "Python-2.0", "CC-BY-4.0", "MIT-0", "Zlib"]);
const lock = JSON.parse(readFileSync("package-lock.json", "utf8"));
const rows = [];
for (const [path, info] of Object.entries(lock.packages)) {
  if (!path) continue;
  const pj = join(path, "package.json");
  let lic = info.license;
  if (!lic && existsSync(pj)) {
    const p = JSON.parse(readFileSync(pj, "utf8"));
    lic = p.license || (p.licenses || []).map((l) => l.type).join(" OR ");
  }
  rows.push({ name: path.replace(/^.*node_modules\//, ""), version: info.version, license: lic || "UNKNOWN", dev: !!info.dev, optional: !!info.optional });
}
const ok = (l) => l.replace(/[()]/g, "").split(/ OR | AND /).some((x) => ALLOWED.has(x.trim()));
const bad = rows.filter((r) => !ok(r.license));
const by = {};
for (const r of rows) by[r.license] = (by[r.license] || 0) + 1;
console.log(`${rows.length} packages (${rows.filter((r) => !r.dev).length} runtime). Licences:`, by);
for (const r of rows.filter((r) => !r.dev)) console.log(`  runtime  ${r.name}@${r.version}  ${r.license}`);
// Self-hosted assets that are not npm packages (served from public/): each must carry its licence file.
const ASSETS = [
  { path: "public/fonts/open-sans-semibold", what: "Open Sans Semibold map glyphs (openmaptiles/fonts)", license: "Apache-2.0", marker: "Apache License" },
];
for (const a of ASSETS) {
  const lf = join(a.path, "LICENSE.txt");
  const okA = existsSync(lf) && readFileSync(lf, "utf8").includes(a.marker) && ALLOWED.has(a.license);
  console.log(`  asset    ${a.what}  ${a.license}${okA ? "" : "  (LICENCE FILE MISSING OR NOT PERMISSIVE)"}`);
  if (!okA) bad.push({ name: a.path, version: "-", license: a.license, dev: false, optional: false });
}
if (bad.length) {
  console.error("Not on the permissive list:");
  for (const r of bad) console.error(`  ${r.name}@${r.version} ${r.license}${r.dev ? " (dev)" : ""}${r.optional ? " (optional)" : ""}`);
  process.exit(1);
}
console.log("All licences permissive.");
