# style-workspace

A collection of Claude Code skills for WaveMaker design token and style system workflows.

## Skills

### token-migration
Generates design token migration scripts that apply structured JSON changes to token files in WaveMaker projects. Supports upsert, insert, shorthand consolidation, and custom recursive transforms. Multiple types can be composed in a single migration.

**Invoke**: `/token-migration`

### generate-migration
Guides the creation of a WaveMaker UI migration script inside `migrations/ui-migrations/`. Asks for version/batch, platform target, and token changes, then generates the full directory layout with `main.js` and utility files. Includes a bundling reminder.

**Invoke**: `/generate-migration`

### verify-migration
Parent skill for verifying WaveMaker design token migrations. Analyzes `migration-info.json` reports, categorizes change types (shorthand consolidation, position node removal, structural updates), and delegates to child skills for detailed verification. Produces an HTML summary report.

**Invoke**: `/verify-migration`

### verify-migration-token-shorthand
Child skill focused on validating shorthand token consolidation. Verifies that `padding`, `border-radius`, and `border-width` tokens have been correctly converted from split directional format to consolidated shorthand format. Generates a per-project HTML diff report.

**Invoke**: `/verify-migration-token-shorthand`  
**Called by**: `verify-migration` when shorthand consolidation changes are detected

### Sample prompt:
```
Run the migration verification for design-token components across all projects using the migration script:wavemaker-artifacts/index.js for <project names>.
For each project: Run the migration script and verify that all design-token components are successfully migrated, provide a consolidated summary including-Migration status for each project (Success/Failure), Summaries of files changed and Overall result across all projects 
```

## Workflow

```
Identify token changes
        ↓
/token-migration  OR  /generate-migration    ← generate migration script files
        ↓
Bundle: npx esbuild main.js --bundle --platform=node --outfile=index.js
        ↓
Run migration in WaveMaker project → produces migration-info.json
        ↓
/verify-migration          ← analyzes migration-info.json, categorizes changes
        ↓
/verify-migration-token-shorthand   ← detailed shorthand token verification
        ↓
HTML summary report saved to project root
```

## Migration script layout

```
migrations/ui-migrations/{VERSION}/{BATCH}/
├── main.js
└── utils/
    ├── core/
    │   ├── file-utils.js (or wm-utils.js)
    │   └── runTokenMigrations.js      ← upsert/insert/shorthand only
    └── tokens/
        ├── upsertTokensInFile.js
        ├── insertTokensIfAbsentInFile.js
        ├── migrateTokensToShorthand.js
        └── {customMigration}.js
```

## Related Tooling

- `wavemaker-artifacts/index.js` — migration script that produces `migration-info.json`
- `wavemaker-rn-codegen` — design token codegen run after migration
- Token files live at `src/main/webapp/design-tokens/overrides/components/`
