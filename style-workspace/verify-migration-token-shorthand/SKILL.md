---
name: verify-migration-token-shorthand
description: Child skill for verifying shorthand token consolidation. Focuses specifically on validating that border-radius, border-width, and padding design tokens have been converted from split format to shorthand format. This is a specialized verification skill called by the parent verify-wavemaker-migration skill when shorthand consolidation changes are detected.
---

## Overview

**Child Skill Scope**: This skill focuses specifically on verifying shorthand token consolidation for `border-radius`, `border-width`, and `padding` properties. It is called by the parent `verify-wavemaker-migration` skill when shorthand consolidation changes are detected in the migration report.

**Purpose**: Validate that design tokens have been successfully migrated from split format (individual directional properties) to shorthand format (consolidated properties).

## Migration Format Reference

### Before Migration (Split Format)
JSON token structure with individual directional properties:
```json
{
  "padding": {
    "top": { "value": "16px" },
    "right": { "value": "12px" },
    "bottom": { "value": "16px" },
    "left": { "value": "12px" }
  },
  "border": {
    "top": {
      "left": { "radius": { "value": "4px" } },
      "right": { "radius": { "value": "4px" } }
    },
    "bottom": {
      "left": { "radius": { "value": "4px" } },
      "right": { "radius": { "value": "4px" } }
    },
    "top": { "width": { "value": "2px" } },
    "right": { "width": { "value": "2px" } },
    "bottom": { "width": { "value": "2px" } },
    "left": { "width": { "value": "2px" } }
  }
}
```

Or flat structure:
```json
{
  "padding-top": { "value": "16px" },
  "padding-right": { "value": "12px" },
  "padding-bottom": { "value": "16px" },
  "padding-left": { "value": "12px" }
}
```

### After Migration (Shorthand Format)
JSON token structure with consolidated shorthand properties:
```json
{
  "padding": {
    "value": "16px 12px 16px 12px"
  },
  "border": {
    "radius": {
      "value": "4px 4px 4px 4px",
      "type": "radius"
    },
    "value": "2px 2px 2px 2px"
  }
}
```

### Real-World Example
Example from WaveMaker component token file showing correct migrated format:
```json
{
  "text": {
    "padding": {
      "value": "{space.0.value} {space.0.value} {space.0.value} {space.0.value}",
      "type": "space",
      "attributes": {
        "subtype": "space",
        "description": "Controls the padding (top, right, bottom, left) of the text in the barcode scanner component. This creates spacing around the text. Acceptable units: px.<br>CSS variable: --wm-barcodescanner-text-padding"
      }
    }
  }
}
```

## Instructions

### Prerequisites
1. **Prism Project** - Ensure you're working within a WaveMaker Prism application project (the script automatically validates this)
2. **Migration Script** - Have access to the `index.js` migration script from the wavemaker-artifacts repository
3. **Backup** - Create a backup of your token files before running migration
4. **Project Structure** - Verify the project has `.wmproject.properties` file with `NATIVE_MOBILE` platform and `PRISM` template

### Running the Migration
1. **Navigate to project root** - Change to your WaveMaker Prism project directory (any Prism project)
2. **Count components before migration** - Record the number of component files:
   ```bash
   # Count component files in overrides directory
   find src/main/webapp/design-tokens/overrides/components -name "*.json" | wc -l
   
   # List all component files (optional - for detailed tracking)
   find src/main/webapp/design-tokens/overrides/components -name "*.json" -type f
   ```
3. **Execute migration** - Run the migration script with optional report directory:
   ```bash
   # Basic execution (report saved to current project directory)
   node /path/to/wavemaker-artifacts/index.js
   
   # With custom report directory
   node /path/to/wavemaker-artifacts/index.js --report-directory=/custom/report/path
   
   # Alternative syntax with quotes
   node /path/to/wavemaker-artifacts/index.js --report-directory="/custom/report/path"
   ```
4. **Monitor output** - Check console output for migration statistics and any errors
5. **Count components after migration** - Verify the number of component files remains the same:
   ```bash
   # Count component files after migration
   find src/main/webapp/design-tokens/overrides/components -name "*.json" | wc -l
   
   # Compare with pre-migration count to ensure no files were lost or added
   ```
6. **Review migration report** - Check the generated `migration-info.json` file for detailed migration results
7. **Generate design tokens** - Run the codegen to generate design tokens after migration:
   ```bash
   # Generate design tokens using wavemaker-rn-codegen
   node /path/to/wavemaker-rn-codegen/build/index.js generate-design-tokens <project-root>/src/main/webapp <project-root>/target/generated-expo-app
   
   # Example with actual paths:
   # node /Users/username/wavemaker-rn-codegen/build/index.js generate-design-tokens ./src/main/webapp ./target/generated-expo-app
   ```

**Note**: The script works with any WaveMaker Prism project and will automatically detect and migrate the appropriate token files in that project's structure.

## Verification Steps

1. **Locate token files** - Find component token definitions in `src/main/webapp/design-tokens/overrides/components/`

2. **Search for split patterns** - Look for tokens matching these patterns:
   - Nested structure: `padding.top`, `padding.right`, `padding.bottom`, `padding.left`
   - Flat structure: `padding-top`, `padding-right`, `padding-bottom`, `padding-left`
   - Border radius: `border.top.left.radius`, `border.top.right.radius`, etc.
   - Border width: `border.top.width`, `border.right.width`, etc.

3. **Confirm shorthand conversion** - Verify these have been consolidated into:
   - Single `padding` token with `value` containing space-separated values (top right bottom left)
   - Single `border.radius` token with `value` containing space-separated corner values (top-left top-right bottom-right bottom-left)
   - Single `border` token with `value` containing space-separated width values (top right bottom left)

4. **Check for orphaned tokens** - Ensure no split-format tokens remain after migration

5. **Validate token references** - Confirm all component references have been updated to use new shorthand token names


## Validation Checklist

### Component File Integrity
- [ ] Pre-migration component count matches post-migration component count
- [ ] No component files were accidentally deleted or created during migration
- [ ] All original component directories are preserved

### Token Structure Validation
- [ ] No nested `padding.top`, `padding.right`, `padding.bottom`, `padding.left` structures exist
- [ ] No flat `padding-top`, `padding-right`, `padding-bottom`, `padding-left` tokens exist
- [ ] No nested `border.top.left.radius`, `border.top.right.radius`, etc. structures exist
- [ ] No nested `border.top.width`, `border.right.width`, etc. structures exist
- [ ] Shorthand `padding` tokens have `value` with space-separated directional values (top right bottom left)
- [ ] Shorthand `border.radius` tokens have `value` with space-separated corner values and `type: "radius"`
- [ ] Shorthand `border` tokens have `value` with space-separated width values (top right bottom left)
- [ ] All component files reference new shorthand token names

### Design Token Generation
- [ ] Design tokens generated successfully in `target/generated-expo-app` directory
- [ ] Generated tokens reflect the migrated shorthand format
- [ ] No errors during design token generation process
- [ ] Build/compilation succeeds without token reference errors

## HTML Summary Export

After every migration run, generate an HTML summary report and save it to the project's base directory (or a shared output directory if running across multiple projects).

### What to include in the HTML report

1. **Stats bar** — total projects passed, total files changed, total tokens removed, total tokens added
2. **Overall results table** — one row per project: project name, status (Success/Failure badge), files changed, tokens removed, tokens added, notes (e.g. position nodes removed)
3. **Per-project detail cards** — one card per project listing every changed file and the specific tokens that were removed (split format) and added (shorthand format)

### How to generate the report

After running the migration and computing the diffs, use Python to write the HTML file:

```python
import os, json

# Collect per-project results into a list:
# results = [
#   {
#     "name": "My Project",
#     "status": "Success",          # or "Failure"
#     "files_changed": 5,
#     "tokens_removed": 27,
#     "tokens_added": 10,
#     "notes": "2 position nodes removed",
#     "files": [
#       {
#         "path": "button/button.json",
#         "removed": ["btn.appearances.foo.mapping.padding.top.value", ...],
#         "added":   ["btn.appearances.foo.mapping.padding.value", ...]
#       },
#       ...
#     ]
#   },
#   ...
# ]
#
# Then call write_html_summary(results, output_path)

def write_html_summary(results, output_path):
    run_date = __import__('datetime').date.today().strftime("%B %d, %Y")
    total_files    = sum(r["files_changed"]  for r in results)
    total_removed  = sum(r["tokens_removed"] for r in results)
    total_added    = sum(r["tokens_added"]   for r in results)
    passed         = sum(1 for r in results if r["status"] == "Success")

    def badge(text, cls):
        return f'<span class="badge badge-{cls}">{text}</span>'

    file_rows_html = ""
    for r in results:
        st = "success" if r["status"] == "Success" else "removed"
        status_badge = badge("✓ Success" if r["status"] == "Success" else "✗ Failure", st)
        file_rows_html += f"""
        <tr>
          <td><strong>{r['name']}</strong></td>
          <td>{status_badge}</td>
          <td>{r['files_changed']}</td>
          <td>{badge(str(r['tokens_removed']) + ' removed', 'removed')}</td>
          <td>{badge(str(r['tokens_added']) + ' added', 'added')}</td>
          <td>{r.get('notes','—')}</td>
        </tr>"""

    cards_html = ""
    for r in results:
        file_details = ""
        for f in r.get("files", []):
            items = ""
            for tok in f.get("removed", []):
                items += f'<li><span class="tag-removed">- {tok}</span></li>'
            for tok in f.get("added", []):
                items += f'<li><span class="tag-added">+ {tok}</span></li>'
            file_details += f"""
            <div class="file-row">
              <div class="file-name">{f['path']}</div>
              <ul class="change-list">{items}</ul>
            </div>"""
        cards_html += f"""
        <div class="project-card">
          <div class="project-card-header">
            <h3>{r['name']}</h3>
            <span class="meta">{r['files_changed']} files changed</span>
          </div>
          <div class="project-card-body">{file_details}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Design Token Migration Summary</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f4f6f9;color:#1a1d23;padding:32px 24px}}
    .page-header{{max-width:1100px;margin:0 auto 32px}}
    .page-header h1{{font-size:1.75rem;font-weight:700}}
    .page-header p{{margin-top:6px;color:#5a6070;font-size:.9rem}}
    .stats-bar{{max-width:1100px;margin:0 auto 32px;display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
    .stat-card{{background:#fff;border-radius:10px;padding:20px 24px;box-shadow:0 1px 4px rgba(0,0,0,.07);text-align:center}}
    .stat-card .value{{font-size:2rem;font-weight:700;color:#2563eb}}
    .stat-card .label{{font-size:.78rem;color:#6b7280;margin-top:4px;text-transform:uppercase;letter-spacing:.04em}}
    .section{{max-width:1100px;margin:0 auto 32px}}
    .section h2{{font-size:1.05rem;font-weight:600;color:#374151;margin-bottom:12px;padding-left:4px}}
    table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.07);font-size:.875rem}}
    thead tr{{background:#1e293b;color:#f1f5f9}}
    thead th{{padding:12px 16px;text-align:left;font-weight:600;font-size:.78rem;text-transform:uppercase;letter-spacing:.05em}}
    tbody tr:nth-child(even){{background:#f8fafc}}
    tbody tr:hover{{background:#eff6ff}}
    tbody td{{padding:11px 16px;border-bottom:1px solid #e5e7eb;vertical-align:top}}
    tbody tr:last-child td{{border-bottom:none}}
    .badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.75rem;font-weight:600}}
    .badge-success{{background:#dcfce7;color:#15803d}}
    .badge-removed{{background:#fee2e2;color:#b91c1c}}
    .badge-added{{background:#dbeafe;color:#1d4ed8}}
    code{{font-family:"SF Mono","Fira Code",monospace;font-size:.8rem;background:#f1f5f9;padding:2px 6px;border-radius:4px;color:#334155}}
    .project-grid{{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:20px}}
    .project-card{{background:#fff;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.07);overflow:hidden}}
    .project-card-header{{background:#1e293b;color:#f1f5f9;padding:14px 20px;display:flex;align-items:center;justify-content:space-between}}
    .project-card-header h3{{font-size:.95rem;font-weight:600}}
    .project-card-header .meta{{font-size:.75rem;color:#94a3b8}}
    .file-row{{border-bottom:1px solid #f1f5f9;padding:12px 20px}}
    .file-row:last-child{{border-bottom:none}}
    .file-name{{font-family:"SF Mono","Fira Code",monospace;font-size:.8rem;color:#2563eb;font-weight:600;margin-bottom:6px}}
    .change-list{{list-style:none;font-size:.8rem;color:#4b5563}}
    .change-list li{{padding:2px 0 2px 14px;position:relative}}
    .change-list li::before{{content:"→";position:absolute;left:0;color:#9ca3af}}
    .tag-removed{{color:#dc2626}}
    .tag-added{{color:#2563eb}}
    footer{{max-width:1100px;margin:40px auto 0;text-align:center;font-size:.78rem;color:#9ca3af}}
  </style>
</head>
<body>
  <div class="page-header">
    <h1>Design Token Migration Summary</h1>
    <p>Run date: {run_date}</p>
  </div>
  <div class="stats-bar">
    <div class="stat-card"><div class="value">{passed} / {len(results)}</div><div class="label">Projects Passed</div></div>
    <div class="stat-card"><div class="value">{total_files}</div><div class="label">Files Changed</div></div>
    <div class="stat-card"><div class="value" style="color:#dc2626">{total_removed}</div><div class="label">Tokens Removed</div></div>
    <div class="stat-card"><div class="value" style="color:#16a34a">{total_added}</div><div class="label">Tokens Added</div></div>
  </div>
  <div class="section">
    <h2>Overall Results</h2>
    <table>
      <thead><tr><th>Project</th><th>Status</th><th>Files Changed</th><th>Tokens Removed</th><th>Tokens Added</th><th>Notes</th></tr></thead>
      <tbody>{file_rows_html}</tbody>
    </table>
  </div>
  <div class="section"><h2>Per-Project File Changes</h2></div>
  <div class="project-grid">{cards_html}</div>
  <footer>Generated by Claude Code &nbsp;|&nbsp; Design Token Migration &nbsp;|&nbsp; {run_date}</footer>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"HTML summary written to: {output_path}")
```

### Where to save the report

- **Single project**: save as `<project-root>/migration-summary.html` alongside `migration-info.json`
- **Multiple projects**: save as `<shared-base-directory>/migration-summary.html` (e.g., the Downloads folder or wherever the projects live)

### When to generate

Always generate the HTML report as the **final step** after:
1. Running the migration script on all projects
2. Removing any new empty component files (files not present before migration)
3. Computing diffs between pre- and post-migration token files
4. Verifying no split-format tokens remain

Print the output path at the end so the user knows where to find it.

---

## Common Issues

**Issue**: Split tokens still present after running migration script
- **Solution**: Check that the migration script `migrateTokensToShorthand.js` executed completely without errors; verify file permissions and that token files are in the expected location (`src/main/webapp/design-tokens/overrides/components`)

**Issue**: Shorthand tokens have incorrect value order
- **Solution**: Verify order follows CSS convention (top, right, bottom, left for directional properties; top-left, top-right, bottom-right, bottom-left for corner properties)

**Issue**: Border radius tokens missing `type: "radius"` property
- **Solution**: Ensure the migration script properly sets the `type` field for border radius tokens as required by the WaveMaker token system

**Issue**: Components fail to build after migration
- **Solution**: Search codebase for old split token references and update to use new shorthand token paths; check that component token files are properly structured JSON

**Issue**: Migration script reports 0 tokens updated
- **Solution**: Verify that the token input data contains the expected token names and structure; check that the `buildMap` function is correctly parsing token names

**Issue**: Design token generation fails after migration
- **Solution**: Ensure the migration completed successfully and all token files are valid JSON; verify the codegen path is correct and the target directory exists; check that the wavemaker-rn-codegen build is available
