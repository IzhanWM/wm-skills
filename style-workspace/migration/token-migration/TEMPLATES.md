# File Templates

## `utils/core/file-utils.js`

Always emit verbatim:

```js
import path from "path";
import fs from "fs";

export function ensureFile(filePath, initContent = "") {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, initContent, "utf-8");
  }
}
```

---

## `utils/tokens/upsertTokensInFile.js`

Include when upsert or insert operations are present:

```js
import fs from "fs";
import { ensureFile } from "../core/file-utils.js";

function normalizeToken(token) {
  const value = token.value.startsWith("{") ? token.value : `{${token.value}}`;
  return { tokenPath: `${token.name}.value`, value };
}

function upsertByPath(json, tokenPath, value) {
  const keys = tokenPath.split(".");
  let current = json;
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    if (i === keys.length - 1) {
      const existed = Object.prototype.hasOwnProperty.call(current, key);
      current[key] = value;
      return existed ? "updated" : "created";
    }
    if (!current[key] || typeof current[key] !== "object") current[key] = {};
    current = current[key];
  }
}

export function upsertTokensInFile(filePath, tokens) {
  ensureFile(filePath, "{}");
  const json = JSON.parse(fs.readFileSync(filePath, "utf-8"));
  const results = [];
  for (const token of tokens) {
    const { tokenPath, value } = normalizeToken(token);
    const action = upsertByPath(json, tokenPath, value);
    results.push({ token: tokenPath, action, value });
  }
  fs.writeFileSync(filePath, JSON.stringify(json, null, 2));
  return { filePath, total: results.length, tokens: results };
}
```

---

## `utils/tokens/insertTokensIfAbsentInFile.js`

Include when insert operations are present:

```js
import fs from "fs";
import { ensureFile } from "../core/file-utils.js";

function normalizeToken(token) {
  const value = token.value.startsWith("{") ? token.value : `{${token.value}}`;
  return { tokenPath: `${token.name}.value`, value };
}

function insertIfAbsentByPath(json, tokenPath, value) {
  const keys = tokenPath.split(".");
  let current = json;
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    if (i === keys.length - 1) {
      if (Object.prototype.hasOwnProperty.call(current, key)) return "ignored";
      current[key] = value;
      return "created";
    }
    if (!current[key] || typeof current[key] !== "object") current[key] = {};
    current = current[key];
  }
}

export function insertTokensIfAbsentInFile(filePath, tokens) {
  ensureFile(filePath, "{}");
  const json = JSON.parse(fs.readFileSync(filePath, "utf-8"));
  const results = [];
  for (const token of tokens) {
    const { tokenPath, value } = normalizeToken(token);
    const action = insertIfAbsentByPath(json, tokenPath, value);
    results.push({ token: tokenPath, action, value });
  }
  fs.writeFileSync(filePath, JSON.stringify(json, null, 2));
  return { filePath, total: results.length, tokens: results };
}
```

---

## `utils/tokens/migrateTokensToShorthand.js`

Include when shorthand operations are present:

```js
import fs from "fs";

export function migrateTokensToShorthand(basePath, entries, migrationMessages) {
  let totalChanged = 0;

  for (const entry of entries) {
    const filePath = `${basePath}/${entry.file}`;
    if (!fs.existsSync(filePath)) {
      console.log(`[Shorthand] File not found — skipping: ${filePath}`);
      continue;
    }

    const json = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    let fileChanged = 0;

    for (const prop of ["padding", "margin", "borderWidth", "borderRadius"]) {
      if (!entry[prop]) continue;
      const sides = { top: null, right: null, bottom: null, left: null };

      for (const token of entry[prop]) {
        const keys = token.name.split(".");
        const side = keys[keys.length - 2];
        if (side in sides) sides[side] = token.value;
      }

      if (Object.values(sides).every(v => v !== null)) {
        const shorthand = `${sides.top} ${sides.right} ${sides.bottom} ${sides.left}`;
        const parentPath = entry[prop][0].name.split(".").slice(0, -2);
        let node = json;
        for (const key of parentPath) {
          if (!node[key]) { node = null; break; }
          node = node[key];
        }
        if (node) {
          delete node.top; delete node.right; delete node.bottom; delete node.left;
          node.value = shorthand;
          fileChanged++;
          migrationMessages.push({
            msg: "Consolidated {}.{} into shorthand '{}' in {}",
            args: [parentPath.join("."), prop, shorthand, entry.file]
          });
        }
      }
    }

    if (fileChanged > 0) {
      fs.writeFileSync(filePath, JSON.stringify(json, null, 2));
      totalChanged += fileChanged;
    }
  }

  return { totalChanged };
}
```

---

## `utils/tokens/{customMigration}.js`

Template for custom recursive transforms. Replace `{Name}` and the transform logic:

```js
import fs from "fs";

function transform(obj, stats) {
  if (!obj || typeof obj !== "object") return;
  // YOUR TRANSFORM LOGIC HERE
  // Delete a key:           if (key === "deprecated") { delete obj[key]; stats.updated++; continue; }
  // Replace a value:        if (obj.value === "oldValue") { obj.value = "newValue"; stats.updated++; }
  for (const key of Object.keys(obj)) {
    transform(obj[key], stats);
  }
}

export function migrate{Name}(basePath, migrationMessages) {
  const filePath = `${basePath}/{relative/path/to/tokens.json}`;

  if (!fs.existsSync(filePath)) {
    console.log("[Migration] File not found — skipping");
    return { updated: 0, filesProcessed: 0 };
  }

  const json = JSON.parse(fs.readFileSync(filePath, "utf-8"));
  const stats = { updated: 0 };
  transform(json, stats);

  if (stats.updated > 0) {
    fs.writeFileSync(filePath, JSON.stringify(json, null, 2));
    migrationMessages.push({
      msg: "{Description}: {} occurrence(s) in {}",
      args: [stats.updated, "{relative/path/to/tokens.json}"]
    });
  }

  return { updated: stats.updated, filesProcessed: 1 };
}
```

If the transform touches multiple files, loop over them — do not duplicate the `transform` function.

---

## `utils/core/runTokenMigrations.js`

Include when upsert, insert, or shorthand operations are present. Remove unused imports:

```js
import path from "path";
import { upsertTokensInFile } from "../tokens/upsertTokensInFile.js";
import { insertTokensIfAbsentInFile } from "../tokens/insertTokensIfAbsentInFile.js";
import { migrateTokensToShorthand } from "../tokens/migrateTokensToShorthand.js";

export function runTokenMigrations(
  { tokenUpserts, tokenInserts, tokenShorthands },
  basePath,
  migrationMessages = []
) {
  let totalTokensChanged = 0;
  let filesProcessed = 0;

  for (const entry of tokenUpserts || []) {
    filesProcessed++;
    const filePath = path.join(basePath, entry.file);
    try {
      const result = upsertTokensInFile(filePath, entry.tokens);
      totalTokensChanged += result.total;
      migrationMessages.push({ msg: "Upserted {} token(s) in {}", args: [result.total, entry.file] });
    } catch (err) {
      console.error(`[Upsert] Failed for ${entry.file}: ${err.message}`);
    }
  }

  for (const entry of tokenInserts || []) {
    filesProcessed++;
    const filePath = path.join(basePath, entry.file);
    try {
      const result = insertTokensIfAbsentInFile(filePath, entry.tokens);
      const created = result.tokens.filter(t => t.action === "created").length;
      totalTokensChanged += created;
      if (created > 0) migrationMessages.push({ msg: "Inserted {} new token(s) in {}", args: [created, entry.file] });
    } catch (err) {
      console.error(`[Insert] Failed for ${entry.file}: ${err.message}`);
    }
  }

  if (tokenShorthands?.length) {
    const result = migrateTokensToShorthand(basePath, tokenShorthands, migrationMessages);
    totalTokensChanged += result.totalChanged;
    filesProcessed += tokenShorthands.length;
  }

  return { totalTokensChanged, filesProcessed };
}
```

---

## `main.js`

Adapt imports and calls to match the operations in use:

```js
import path from "path";
import fs from "fs";
// import { runTokenMigrations } from "./utils/core/runTokenMigrations.js";
// import { migrate{Name} } from "./utils/tokens/migrate{Name}.js";

/** ── CLI args ── */
const args = process.argv.slice(2);
let reportDirectory = null;
for (let i = 0; i < args.length; i++) {
  if (args[i].startsWith("--report-directory=")) {
    reportDirectory = args[i].split("=")[1].replace(/^["']|["']$/g, "");
  } else if (args[i] === "--report-directory" && i + 1 < args.length) {
    reportDirectory = args[++i];
  }
}

/** ── Paths ── */
const basePath = process.cwd();
const tokenBasePath = path.join(basePath, "tokens"); // adjust to match the project's token directory
if (!reportDirectory) reportDirectory = basePath;

/** ── State ── */
const migrationMessages = [];
let totalTokensChanged = 0;
let filesProcessed = 0;

/** ── Token data ── */
// Define tokenUpserts / tokenInserts / tokenShorthands here
// Example:
// const tokenUpserts = [
//   { file: "components/button/button.json", tokens: [{ name: "button.bg", value: "color.primary.500" }] }
// ];

/** ── Run ── */
console.log("\n==========================================");
console.log("MIGRATION STARTED");
console.log("==========================================\n");

// const result = runTokenMigrations({ tokenUpserts, tokenInserts, tokenShorthands }, tokenBasePath, migrationMessages);
// totalTokensChanged += result.totalTokensChanged;
// filesProcessed += result.filesProcessed;

// const customResult = migrate{Name}(tokenBasePath, migrationMessages);
// totalTokensChanged += customResult.updated;
// filesProcessed += customResult.filesProcessed;

/** ── Report ── */
console.log(`\nFiles processed : ${filesProcessed}`);
console.log(`Tokens changed  : ${totalTokensChanged}`);

if (totalTokensChanged > 0) {
  fs.mkdirSync(reportDirectory, { recursive: true });
  const reportPath = path.join(reportDirectory, "migration-report.json");
  fs.writeFileSync(reportPath, JSON.stringify(migrationMessages, null, 2));
  console.log(`\nReport written to: ${reportPath}`);
} else {
  console.log("\nNo changes detected — skipping report.");
}
```
