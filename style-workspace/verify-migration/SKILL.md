---
name: verify-wavemaker-migration
description: Comprehensive verification of WaveMaker design token migrations including shorthand consolidation, position node removal, and other token transformations. This parent skill analyzes migration changes and delegates to specialized child skills for detailed verification.
---

## Overview

Verify and analyze all changes made by WaveMaker migration scripts, including design token transformations, structural modifications, and component updates. This skill provides a comprehensive overview of migration impacts and delegates to specialized verification skills when needed.

## Migration Types Detected

### 1. Shorthand Token Consolidation
**What it does**: Converts split directional properties into consolidated shorthand format
- `padding.top/right/bottom/left` → `padding.value: "top right bottom left"`
- `border.radius` corner properties → `border.radius.value: "tl tr br bl"`
- `border.width` directional properties → `border.value: "top right bottom left"`

**When detected**: Use child skill `verify-migration-token-shorthand` for detailed verification

### 2. Position Node Removal
**What it does**: Removes deprecated `position` properties from button components
- Deletes `position` nodes from `btn` structures in `button/button.json`

### 3. Component Structure Updates
**What it does**: Modifies component token file structure and organization
- Updates token hierarchies
- Consolidates nested properties
- Removes obsolete token references

## Instructions

### Running Migration Analysis
1. **Execute migration** - Run the WaveMaker migration script:
   ```bash
   # Navigate to Prism project root
   cd /path/to/your/prism-project
   
   # Run migration with report
   node /path/to/wavemaker-artifacts/index.js --report-directory=./migration-reports
   ```

2. **Analyze migration report** - Review the generated `migration-info.json`:
   ```bash
   # View migration summary
   cat ./migration-reports/migration-info.json | jq '.'
   ```

3. **Categorize changes** - Identify the types of changes made:
   - Count shorthand consolidations
   - Count position node removals
   - Count other structural changes

### Change Analysis Workflow

1. **Parse migration report** - Extract change statistics from `migration-info.json`
2. **Categorize by change type**:
   - **Shorthand changes**: Look for messages containing "merged", "shorthand", "padding", "border"
   - **Position removals**: Look for messages containing "position", "deprecated"
   - **Other changes**: Any remaining modifications
3. **Delegate verification**:
   - For shorthand changes → Use `verify-migration-token-shorthand` skill
   - For position changes → Manual verification of button components
   - For other changes → Manual review of affected files

## Verification Summary

### Migration Report Analysis
- [ ] Migration completed without errors
- [ ] `migration-info.json` report generated successfully
- [ ] All change messages parsed and categorized
- [ ] No unexpected file modifications detected

### Change Type Distribution
- [ ] Shorthand consolidations identified and counted
- [ ] Position node removals identified and counted  
- [ ] Other structural changes identified and documented
- [ ] Change impact assessed per component

### Delegation to Child Skills
- [ ] Shorthand changes verified using `verify-migration-token-shorthand` skill
- [ ] Position removals manually verified in button components
- [ ] All other changes manually reviewed and validated

## Migration Impact Summary

After analysis, provide a summary including:

### Statistics
- **Total projects processed**: X
- **Total files modified**: X  
- **Shorthand consolidations**: X tokens across Y files
- **Position nodes removed**: X nodes across Y files
- **Other changes**: X modifications across Y files

### Success Indicators
- All migrations completed without errors
- No component files lost or corrupted
- All token references remain valid
- Generated design tokens reflect changes correctly

### Risk Assessment
- **Low risk**: Only shorthand consolidations and position removals
- **Medium risk**: Structural changes to component hierarchies
- **High risk**: Unexpected modifications or error conditions

## Common Migration Patterns

### Expected Changes
1. **Shorthand consolidation messages**:
   ```
   "Merged 4 padding nodes (top, right, bottom, left) into shorthand in src/main/webapp/design-tokens/overrides/components/button/button.json"
   ```

2. **Position removal messages**:
   ```
   "Removed 3 deprecated 'position' nodes from src/main/webapp/design-tokens/overrides/components/button/button.json"
   ```

### Unexpected Changes
- File deletions or creations
- Token value modifications beyond consolidation
- Structural changes outside expected patterns

## Child Skills Reference

### verify-migration-token-shorthand
**Use when**: Migration report shows shorthand consolidation changes
**Purpose**: Detailed verification of padding, border-radius, and border-width token consolidation
**Scope**: Focuses specifically on split-to-shorthand token transformations

## HTML Summary Export

After every migration run, generate a comprehensive HTML summary report and save it to the project's base directory (or a shared output directory if running across multiple projects).

### What to include in the HTML report

1. **Stats bar** — total projects processed, total files changed, total tokens consolidated, total position nodes removed, total other changes
2. **Overall results table** — one row per project: project name, status (Success/Failure badge), files changed, shorthand consolidations, position removals, other changes, notes
3. **Per-project detail cards** — one card per project with sections for:
   - **Shorthand Consolidations**: Files and specific tokens converted (split → shorthand)
   - **Position Node Removals**: Files and number of deprecated position nodes removed
   - **Other Changes**: Any additional structural modifications

### How to generate the report

After running the migration analysis:

```bash
# Generate HTML report from migration data
# This should be done by the parent skill after analyzing migration-info.json
```

### HTML Template Structure

```html
<!DOCTYPE html>
<html>
<head>
    <title>WaveMaker Migration Report</title>
    <style>
        .stats-bar { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { padding: 15px; border-radius: 8px; background: #f5f5f5; }
        .success { color: #28a745; }
        .failure { color: #dc3545; }
        .project-card { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .change-section { margin: 15px 0; }
        .change-list { list-style-type: none; padding-left: 20px; }
    </style>
</head>
<body>
    <h1>WaveMaker Migration Summary</h1>
    
    <!-- Stats Bar -->
    <div class="stats-bar">
        <div class="stat-card">
            <h3>Projects Processed</h3>
            <p class="stat-value">{totalProjects}</p>
        </div>
        <div class="stat-card">
            <h3>Files Modified</h3>
            <p class="stat-value">{totalFiles}</p>
        </div>
        <div class="stat-card">
            <h3>Shorthand Consolidations</h3>
            <p class="stat-value">{shorthandCount}</p>
        </div>
        <div class="stat-card">
            <h3>Position Nodes Removed</h3>
            <p class="stat-value">{positionCount}</p>
        </div>
        <div class="stat-card">
            <h3>Other Changes</h3>
            <p class="stat-value">{otherCount}</p>
        </div>
    </div>
    
    <!-- Results Table -->
    <table>
        <thead>
            <tr>
                <th>Project</th>
                <th>Status</th>
                <th>Files Changed</th>
                <th>Shorthand</th>
                <th>Position</th>
                <th>Other</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
            <!-- Per project rows -->
            <tr>
                <td>{projectName}</td>
                <td><span class="success">✓ Success</span></td>
                <td>{filesChanged}</td>
                <td>{shorthandChanges}</td>
                <td>{positionChanges}</td>
                <td>{otherChanges}</td>
                <td>{notes}</td>
            </tr>
        </tbody>
    </table>
    
    <!-- Detailed Cards -->
    <div class="project-details">
        <div class="project-card">
            <h2>{projectName}</h2>
            
            <div class="change-section">
                <h3>Shorthand Consolidations</h3>
                <ul class="change-list">
                    <li><strong>File:</strong> {fileName}
                        <ul>
                            <li>Removed: {splitTokens}</li>
                            <li>Added: {shorthandToken}</li>
                        </ul>
                    </li>
                </ul>
            </div>
            
            <div class="change-section">
                <h3>Position Node Removals</h3>
                <ul class="change-list">
                    <li><strong>File:</strong> {fileName}
                        <ul>
                            <li>Removed: {positionCount} deprecated position nodes</li>
                        </ul>
                    </li>
                </ul>
            </div>
            
            <div class="change-section">
                <h3>Other Changes</h3>
                <ul class="change-list">
                    <li><strong>File:</strong> {fileName}
                        <ul>
                            <li>Change: {changeDescription}</li>
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
```

## Troubleshooting

**Issue**: Migration report shows no changes but tokens appear modified
- **Solution**: Check migration script execution logs; verify project is detected as Prism; ensure token files are in expected locations

**Issue**: Unexpected file modifications detected
- **Solution**: Review migration script version; check for custom modifications; validate against known migration patterns

**Issue**: Child skill verification fails after successful migration
- **Solution**: Check token file integrity; verify JSON syntax; ensure all references are valid

**Issue**: HTML report generation fails
- **Solution**: Verify migration-info.json exists and is valid JSON; check write permissions for output directory; ensure all required data fields are available
