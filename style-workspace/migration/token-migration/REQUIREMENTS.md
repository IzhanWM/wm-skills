# Requirements Gathering

Ask the user for the following if not already clear from context:

## 1. Output directory
Where should the migration files be written?
- Example: `migrations/1.2.0/`, `migrations/ui-migrations/11.16/1/`

## 2. Token file paths
Relative paths to the JSON files that need to change.
- Example: `tokens/components/button/button.json`

## 3. What changed
For each file, the user should provide one of:
- A **before/after JSON snippet** (preferred — most precise)
- A description of old and new token paths/values
- A list of tokens to add, update, or consolidate

## 4. Migration type
Infer from the change description. Only ask if genuinely ambiguous:
- **upsert** — force-set a value (create or overwrite)
- **insert** — add only if absent
- **shorthand** — consolidate `top/right/bottom/left` into CSS shorthand
- **custom** — anything else (delete, rename, replace pattern)

## 5. Single or batch
- **Single**: one file, one or a few tokens
- **Batch**: multiple files or many tokens — collect all `{ file, tokens[] }` entries upfront
