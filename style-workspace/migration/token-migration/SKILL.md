---
name: token-migration
description: Generate design token migration scripts that apply structured JSON changes (upsert, insert, shorthand consolidation, or custom transforms) to token files. Use when asked to create a migration for design token changes, token file updates, or token system versioning.
---

# Design Token Migration Generator

## Quick start

1. Gather requirements (see [REQUIREMENTS.md](REQUIREMENTS.md))
2. Identify migration type(s) from the before/after JSON
3. Generate files using the templates in [TEMPLATES.md](TEMPLATES.md)
4. Remind the user to bundle (see below)

---

## Migration types

Infer from before/after JSON. Multiple types can be composed.

| Type | When to use |
|---|---|
| **upsert** | A token must be set to a specific value — create or overwrite |
| **insert** | A token should be added only if absent — never overwrite |
| **shorthand** | Split `top/right/bottom/left` siblings collapse into one CSS shorthand |
| **custom** | Delete a node, rename a key, replace a value pattern across a file |

---

## Directory layout

```
{OUTPUT_DIR}/
├── main.js
└── utils/
    ├── core/
    │   ├── file-utils.js
    │   └── runTokenMigrations.js      ← upsert/insert/shorthand only
    └── tokens/
        ├── upsertTokensInFile.js      ← upsert or insert
        ├── insertTokensIfAbsentInFile.js ← insert only
        ├── migrateTokensToShorthand.js   ← shorthand only
        └── {customMigration}.js          ← one per custom transform
```

Only generate files needed for the operations in use.

---

## Token value rules

| Value type | How to write in `value` field |
|---|---|
| Reference to another token | `path.to.token` — normalizer wraps in `{}` |
| Literal CSS value | `10px`, `none`, `#fff` — used as-is |
| Token `name` field | Dot-notation without trailing `.value` — normalizer appends it |

Guard against double-wrapping: if a value already starts with `{`, do not wrap again.

---

## Bundling reminder

After generating all files, always output:

```
Files generated at: {OUTPUT_DIR}/

To bundle for deployment:

  cd {OUTPUT_DIR}
  npx esbuild main.js \
    --bundle \
    --platform=node \
    --outfile=index.js

Commit both main.js and index.js.
Run: node index.js --report-directory=./reports
```

---

## Rules to always follow

- Use ESM (`import`/`export`) — esbuild handles bundling
- Never hardcode absolute paths — always derive from `process.cwd()`
- Guard every file read with `fs.existsSync` — skip gracefully if missing
- Write JSON with `JSON.stringify(json, null, 2)` always
- Migration messages use `{}` as placeholder in `msg` with a matching `args` array
- Only generate/import utility files that are actually used
- For multiple files sharing the same transform, loop — never duplicate transform logic
- If a change doesn't fit upsert/insert/shorthand, write a custom recursive transform

For full file templates, see [TEMPLATES.md](TEMPLATES.md).
For gathering requirements from the user, see [REQUIREMENTS.md](REQUIREMENTS.md).
