---
name: generate-migration
description: Generate a WaveMaker UI migration script for design token changes in the artifacts repo
---

You are generating a WaveMaker UI migration script inside the `migrations/ui-migrations/` directory.

## Context

Migration scripts run inside WaveMaker projects (not this repo) after being bundled. The project runs:

```bash
npx esbuild main.js --bundle --platform=node --outfile=index.js
```

Then the bundled `index.js` is executed in the WaveMaker project root (`process.cwd()`) with an optional `--report-directory=<path>` flag.

### Directory structure

Each migration lives at `migrations/ui-migrations/{VERSION}/{BATCH}/` and follows this layout:

```
migrations/ui-migrations/{VERSION}/{BATCH}/
├── main.js                          ← entry point (ESM, esbuild will bundle it)
└── utils/
    ├── core/
    │   ├── wm-utils.js              ← isPrismProject, ensureFile helpers
    │   └── runTokenMigrations.js    ← orchestrator for upsert/insert/shorthand ops
    └── tokens/
        └── *.js                     ← one file per custom migration operation
```

All token JSON files live in the WaveMaker **project** (not this repo) at:
`src/main/webapp/design-tokens/overrides/components/{component}/{component}.json`

### Platform check

Every migration checks `.wmproject.properties` in the project root.
- WEB Prism projects: `platformType">WEB</entry>` + `template">PRISM</entry>`
- Native Mobile Prism projects: `platformType">NATIVE_MOBILE</entry>` + `template">PRISM</entry>`

---

## Step 1 — Gather requirements

Ask the user for the following if not already clear from $ARGUMENTS or context:

1. **Version and batch** — e.g., `11.16/1`. Increment the batch if a migration already exists for that version.
2. **Platform target** — `WEB` or `NATIVE_MOBILE` (or `BOTH` if the migration applies to both).
3. **What changed in the default JSON(s)** — describe the token path(s) and old/new values.
4. **Migration type(s)** — one or more of:
   - **upsert** — force-set token values (creates or overwrites)
   - **insert** — set tokens only if they don't already exist (safe/non-destructive)
   - **shorthand** — consolidate split `top/right/bottom/left` token nodes into CSS shorthand (for `padding`, `margin`, `borderWidth`, `borderRadius`)
   - **custom** — a bespoke recursive transform (e.g., delete a deprecated node, replace a specific value pattern across a file)
5. **Single or batch** — one file/token or many? For batch, collect all `{file, tokens[]}` entries.

---

## Step 2 — Generate the migration files

Read the existing migrations at `migrations/ui-migrations/11.15/1/` and `migrations/ui-migrations/11.14/1/` as reference before generating.

### `utils/core/wm-utils.js`

Always copy this verbatim, adjusting only the platform check string:

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

export function isPrismProject(projectPath) {
  try {
    const propertiesPath = path.join(projectPath, ".wmproject.properties");
    if (!fs.existsSync(propertiesPath)) {
      console.log(`.wmproject.properties not found at: ${propertiesPath}`);
      return false;
    }
    const propertiesContent = fs.readFileSync(propertiesPath, "utf-8");
    // Change platform string based on target: 'platformType">WEB</entry>' or 'platformType">NATIVE_MOBILE</entry>'
    const hasPlatform = propertiesContent.includes('platformType">{PLATFORM}</entry>');
    const hasPrismTemplate = propertiesContent.includes('template">PRISM</entry>');
    const isPrism = hasPlatform && hasPrismTemplate;
    console.log(`Project analysis:`);
    console.log(`  • Platform Type: ${hasPlatform ? '{PLATFORM}' : 'Not {PLATFORM}'}`);
    console.log(`  • Template: ${hasPrismTemplate ? 'PRISM' : 'Not PRISM'}`);
    console.log(`  • Is Prism Project: ${isPrism ? 'YES' : 'NO'}`);
    return isPrism;
  } catch (err) {
    console.warn(`Failed to read .wmproject.properties: ${err.message}`);
    return false;
  }
}
```

Replace `{PLATFORM}` with `WEB` or `NATIVE_MOBILE`.

---

### `utils/core/runTokenMigrations.js`

#### For **upsert** and/or **insert** (11.14 style):

```js
import path from "path";
import { upsertTokensInFile } from "../tokens/upsertTokensInFile.js";
import { insertTokensIfAbsentInFile } from "../tokens/insertTokensIfAbsentInFile.js";

export function runTokenMigrations({ tokenUpserts, tokenInserts }, inputFolder = process.cwd(), migrationMessages = []) {
  let totalTokensChanged = 0;
  let filesProcessed = 0;
  const baseComponentTokensPath = path.join(inputFolder, "src/main/webapp/design-tokens/overrides/components");

  for (const entry of tokenUpserts || []) {
    filesProcessed++;
    const filePath = path.join(baseComponentTokensPath, entry.file);
    try {
      const result = upsertTokensInFile(filePath, entry.tokens);
      totalTokensChanged += result.total;
      migrationMessages.push({ msg: "Upserted {} tokens in {}", args: [result.total, path.join("src/main/webapp/design-tokens/overrides/components", entry.file)] });
    } catch (err) {
      console.error(`[Token Upsert] Failed for ${entry.file}: ${err.message}`);
    }
  }

  for (const entry of tokenInserts || []) {
    filesProcessed++;
    const filePath = path.join(baseComponentTokensPath, entry.file);
    try {
      const result = insertTokensIfAbsentInFile(filePath, entry.tokens);
      const createdCount = result.tokens.filter(t => t.action === "created").length;
      totalTokensChanged += createdCount;
      createdCount > 0 && migrationMessages.push({ msg: "Inserted {} new tokens in {}", args: [createdCount, path.join("src/main/webapp/design-tokens/overrides/components", entry.file)] });
    } catch (err) {
      console.error(`[Token Insert] Failed for ${entry.file}: ${err.message}`);
    }
  }

  return { totalTokensChanged, filesProcessed };
}
```

Include `upsertTokensInFile.js` and `insertTokensIfAbsentInFile.js` verbatim from `migrations/ui-migrations/11.14/1/utils/tokens/`.

#### For **shorthand** (11.15 style):

Copy `runTokenMigrations.js` and `migrateTokensToShorthand.js` verbatim from `migrations/ui-migrations/11.15/1/utils/`.

The `tokenMigrations` array entries support these keys: `padding`, `margin`, `borderWidth`, `borderRadius`. Each key holds an array of `{ name, value }` objects where `name` is the dot-path of the split token (e.g., `padding.top.value`).

---

### `utils/tokens/*.js` — Custom migrations

For custom recursive transforms, follow this exact template:

```js
import fs from "fs";
import path from "path";

function transform(obj, stats) {
  if (!obj || typeof obj !== "object") return;
  // YOUR TRANSFORM LOGIC HERE
  // e.g.: if (obj.someKey && obj.someKey.value === "oldValue") { obj.someKey.value = "newValue"; stats.updated++; }
  for (const key of Object.keys(obj)) {
    transform(obj[key], stats);
  }
}

export function migrateXxx(inputFolder, migrationMessages) {
  const basePath = path.join(inputFolder, "src/main/webapp/design-tokens/overrides/components");
  const filePath = path.join(basePath, "component/component.json");

  if (!fs.existsSync(filePath)) {
    console.log("[Migration] component.json not found — skipping");
    return { updated: 0, filesProcessed: 0 };
  }

  const json = JSON.parse(fs.readFileSync(filePath, "utf-8"));

  if (!json.rootKey || typeof json.rootKey !== "object") {
    console.log("[Migration] rootKey missing — skipping");
    return { updated: 0, filesProcessed: 1 };
  }

  const stats = { updated: 0 };
  transform(json.rootKey, stats);

  if (stats.updated > 0) {
    fs.writeFileSync(filePath, JSON.stringify(json, null, 2));
    migrationMessages.push({
      msg: "Description of what was changed: {} occurrences in {}",
      args: [stats.updated, "src/main/webapp/design-tokens/overrides/components/component/component.json"]
    });
    console.log(`[Migration] ${stats.updated} changes applied`);
  } else {
    console.log("[Migration] No changes needed");
  }

  return { updated: stats.updated, filesProcessed: 1 };
}
```

---

### `main.js`

This is the entry point. It must:
1. Parse `--report-directory` CLI arg
2. Detect platform via `isPrismProject`
3. Run all migration operations
4. Aggregate `totalTokensChanged` and `filesProcessed`
5. Write `migration-info.json` to the report directory if any changes were made

Follow this structure exactly (adapting imports and calls based on migration type):

```js
import path from "path";
import fs from "fs";
import { isPrismProject } from "./utils/core/wm-utils.js";
// import { runTokenMigrations } from "./utils/core/runTokenMigrations.js";
// import { migrateXxx } from "./utils/tokens/migrateXxx.js";

/** ------------------ CLI Args ------------------ */
const args = process.argv.slice(2);
let reportDirectory = null;
for (let i = 0; i < args.length; i++) {
  if (args[i].startsWith('--report-directory=')) {
    reportDirectory = args[i].split('=')[1].replace(/^["']|["']$/g, '');
  } else if (args[i] === '--report-directory' && i + 1 < args.length) {
    reportDirectory = args[i + 1];
    i++;
  }
}

/** ------------------ Input Folder ------------------ */
const inputFolder = process.cwd();
if (reportDirectory === null) {
  reportDirectory = inputFolder;
}

/** ------------------ Migration Report ------------------ */
const migrationMessages = [];
let totalTokensChanged = 0;
let filesProcessed = 0;

/** ------------------ Token Operations ------------------ */
// Define tokenUpserts / tokenInserts / tokenMigrations here based on what changed

/** ------------------ Prism Project Check ------------------ */
const isPrism = isPrismProject(inputFolder);
if (!isPrism) {
  console.log("\n==========================================");
  console.log("MIGRATION SKIPPED");
  console.log("Reason: Not a Prism project");
  console.log("==========================================\n");
  process.exit(0);
}

/** ------------------ Run Migration ------------------ */
console.log("\n==========================================");
console.log("MIGRATION STARTED");
console.log("==========================================\n");

// Call runTokenMigrations and/or custom migration functions here
// Aggregate results into totalTokensChanged and filesProcessed

/** ------------------ Write migration-info.json ------------------ */
if (totalTokensChanged > 0) {
  fs.mkdirSync(reportDirectory, { recursive: true });
  const reportPath = path.join(reportDirectory, "migration-info.json");
  fs.writeFileSync(reportPath, JSON.stringify(migrationMessages, null, 2));
  console.log(`Migration report written to: ${reportPath}`);
} else {
  console.log("No changes detected — skipping report generation");
}
```

---

## Step 3 — Handle single vs batch

- **Single change**: One entry in `tokenUpserts`, `tokenInserts`, or `tokenMigrations`, or one custom file.
- **Batch of changes**: Multiple entries in the arrays. All entries for the same operation type go in the same array. Different operation types (e.g., some upserts + one custom recursive transform) are composed in `main.js` by calling multiple functions and summing their results.
- **Mixed types**: Generate both a `runTokenMigrations.js` (for upsert/insert/shorthand) and separate `utils/tokens/*.js` files (for custom logic), and import/call all of them in `main.js`.

---

## Step 4 — Remind the user to bundle

After generating all files, output this reminder:

```
Files generated at: migrations/ui-migrations/{VERSION}/{BATCH}/

To bundle for deployment, run from the migration directory:

  cd migrations/ui-migrations/{VERSION}/{BATCH}
  npx esbuild main.js \
    --bundle \
    --platform=node \
    --outfile=index.js

Then commit both main.js and index.js.
```

---

## Rules and patterns to always follow

- Use ESM (`import`/`export`) — esbuild handles the bundling to CommonJS
- Token `name` fields use dot-notation without a trailing `.value` — normalizers add `.value` automatically
- Token `value` fields for references use `path.to.token.value` format (without `{}` braces) — normalizers wrap in `{}`
- Literal values (like `10px`, `none`) are used as-is in `value` fields
- Always check if the file exists before reading; return `{ updated: 0, filesProcessed: 0 }` if missing
- Always write `JSON.stringify(json, null, 2)` (2-space indent) when writing JSON files
- Migration messages use `{}` as placeholder in `msg`, with corresponding `args` array
- Never hardcode the project path — always derive from `process.cwd()` at runtime
- If the migration touches multiple files, loop — do not duplicate the transform function
- If the user's change doesn't fit upsert/insert/shorthand, write a custom recursive transform
