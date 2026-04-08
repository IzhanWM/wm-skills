# style-workspace

A collection of Claude Code skills for WaveMaker design token and style system workflows.

## Skills

### verify-migration
Parent skill for verifying WaveMaker design token migrations. Analyzes `migration-info.json` reports, categorizes change types (shorthand consolidation, position node removal, structural updates), and delegates to child skills for detailed verification. Produces an HTML summary report.

**Invoke**: `/verify-migration`

### verify-migration-token-shorthand
Child skill focused on validating shorthand token consolidation. Verifies that `padding`, `border-radius`, and `border-width` tokens have been correctly converted from split directional format to consolidated shorthand format. Generates a per-project HTML diff report.

**Invoke**: `/verify-migration-token-shorthand`  
**Called by**: `verify-migration` when shorthand consolidation changes are detected

## Workflow

```
Run migration script
        ↓
/verify-migration          ← analyzes migration-info.json, categorizes changes
        ↓
/verify-migration-token-shorthand   ← detailed shorthand token verification
        ↓
HTML summary report saved to project root
```

## Related Tooling

- `wavemaker-artifacts/index.js` — migration script that produces `migration-info.json`
- `wavemaker-rn-codegen` — design token codegen run after migration
- Token files live at `src/main/webapp/design-tokens/overrides/components/`
