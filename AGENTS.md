# AGENTS.md

## Purpose
This repository contains a Windows-oriented business automation tool that reads `output.xlsx`, enriches rows with Keepa data, estimates monthly sales, and writes `output_keepa.xlsx`.

The project is optimized for:
- local Windows development
- later packaging with PyInstaller
- conservative Keepa token usage
- maintainable, minimal-risk changes

When making changes, prefer reliability, traceability, and low operational cost over cleverness.

---

## Core behavior to preserve
Unless explicitly instructed otherwise, keep all of the following behaviors intact:

- Read input from `output.xlsx`
- Write output to `output_keepa.xlsx`
- Keep rows with missing `ASIN` in the output
- Rows with missing `ASIN` must be marked as:
  - `estimate_source = unavailable`
  - `estimate_confidence = D`
  - `estimate_note = ASIN missing`
- Use `monthlySold` first when available
- If `monthlySold` is missing, estimate using `salesRankDrops30 * coefficient`
- If neither source is usable, mark as unavailable
- Format `keepa_lastSoldUpdate` as `YYYY-MM-DD HH:MM:SS`
- Use `config.ini` first for configuration
- Fallback to environment variable `KEEPA_API_KEY` only if needed
- Resolve paths relative to the script or executable directory
- Write logs to `keepa_enrich.log`
- Continue processing even if some ASIN fetches fail

Do not silently change these behaviors.

---

## Development priorities
When there is a tradeoff, prefer the following in order:

1. Correctness
2. Token efficiency
3. Clear logs and diagnosability
4. Backward compatibility
5. Performance
6. Refactoring elegance

Avoid large rewrites unless explicitly requested.

---

## Keepa API usage rules
This project is designed to minimize Keepa token consumption.

### Always prefer low-cost requests
For monthly sales estimation, the normal request profile should be:

- `domain=5`
- `stats=180`
- `history=0`
- `buybox=0`
- no `offers`

Do not add expensive request options like `offers` unless explicitly requested.

### Token efficiency expectations
Assume:
- Product request cost is effectively per ASIN
- Up to 100 ASINs may be batched into one request
- Tokens are scarce
- Full refetch of all ASINs on every run is not acceptable for large datasets

Therefore:
- use differential update logic
- fetch only ASINs that need refresh
- use cached data whenever possible

---

## Differential update queue policy
The repository should support a local cache and differential fetch selection.

### Required design intent
The code should be structured so that these responsibilities are clearly separated:

1. Read input rows
2. Extract unique valid ASINs
3. Load local cache
4. Decide which ASINs should be fetched now
5. Fetch only queued ASINs from Keepa
6. Update cache with results
7. Build final output using both cache and new fetches

Do not tightly couple queue selection with API transport.

### Queue selection principles
ASINs should be selected for refresh when they are:
- new and not in cache
- due by `next_fetch_after`
- previously failed with retry-worthy errors
- previously unavailable
- missing both `monthlySold` and `salesRankDrops30`
- otherwise stale

ASINs should usually be skipped when:
- recently fetched
- cache is still fresh
- usable monthly sales or fallback data already exists

### Cache expectations
A local cache should track state per ASIN.

Preferred fields:
- `asin`
- `last_fetched_at`
- `last_success_at`
- `last_failure_at`
- `keepa_lastSoldUpdate`
- `keepa_monthlySold`
- `keepa_salesRankDrops30`
- `estimate_source`
- `estimate_confidence`
- `estimate_note`
- `failure_type`
- `rows_seen_in_input`
- `fetch_priority`
- `next_fetch_after`
- `consecutive_failures`

CSV is acceptable for MVP.
SQLite is acceptable if kept simple and maintainable.

---

## Logging requirements
Logging is important in this project. Do not reduce visibility.

### Logs should make these distinguishable
- `queue_decision=new`
- `queue_decision=retry`
- `queue_decision=stale`
- `queue_decision=skip_cached`

And also:
- `failure_type=communication_error`
- `failure_type=keepa_product_not_found`
- `status=monthlySold_missing`
- `status=salesRankDrops30_missing`

### Summary output
When practical, summary output should include counts such as:
- `total_input_rows`
- `rows_with_missing_asin`
- `rows_with_valid_asin`
- `unique_valid_asins`
- `queued_for_fetch_count`
- `skipped_by_cache_count`
- `fetched_success_count`
- `fetched_failure_count`
- `cache_hit_count`
- `cache_miss_count`
- `monthlySold_used_count`
- `salesRankDrops30_calibrated_count`
- `unavailable_count`

If priority tiers exist, also include:
- `queue_priority_high_count`
- `queue_priority_medium_count`
- `queue_priority_low_count`

Do not remove existing useful summary metrics without a good reason.

---

## Error handling rules
This project is intended for business users on Windows PCs.

### Required behavior
- Do not crash the whole run because of one ASIN failure
- Preserve partial progress where possible
- Use explicit Japanese messages for user-facing errors when appropriate
- Log detailed technical context for troubleshooting

### Example expectations
- If output Excel is locked, raise a clear message that the file may be open in Excel
- If API key is missing, explain how to set it in `config.ini`
- If date formatting fails, log a warning and continue safely

---

## Windows and packaging assumptions
This project is expected to run in two modes:
- Python source execution during development
- packaged `.exe` execution after local Windows build

### Keep this compatible with PyInstaller
The code should continue to work when frozen.

Use path resolution that works for both:
- script execution
- executable execution

Do not assume the working directory is the same as the script location.
Do not hardcode developer-specific absolute paths.

### Packaging guidance
PyInstaller `onedir` is the default packaging assumption unless explicitly changed.

Expected companion files near the executable may include:
- `config.ini`
- `output.xlsx`
- `run.bat`

Do not design the runtime so that editable user files must be embedded inside the executable.

---

## Config and secrets
Never hardcode secrets.

### Rules
- Never commit real API keys
- Only commit `config.ini.example`
- `config.ini` should be user-provided or locally created
- Prefer reading config from file first, then environment variables

Do not print full secrets into logs.

---

## Excel handling rules
Preserve the original input rows unless explicitly instructed otherwise.

### Expectations
- Original columns should remain
- New columns should be appended
- Missing-ASIN rows must remain in output
- Cached data may be used to populate output even if the ASIN was not fetched in the current run

Do not silently drop rows.

---

## Coefficient and estimation rules
This repository currently uses `monthlySold` as the preferred value and `salesRankDrops30 * coefficient` as fallback.

### Important
- Do not replace `monthlySold` when it exists
- Be careful when changing coefficient logic
- If introducing smarter calibration, make it robust to mixed product groups and outliers
- Prefer conservative estimation over aggressive speculation
- It is acceptable to leave some rows unavailable if calibration quality is weak

If you change coefficient logic, document:
- selection criteria
- fallback order
- minimum sample sizes
- handling of outliers

---

## Code structure guidance
Prefer small, testable functions.

Recommended separations:
- config loading
- path resolution
- logging setup
- input loading
- cache load/save
- queue decision logic
- Keepa fetch transport
- Keepa response normalization
- coefficient calculation
- dataframe enrichment
- summary generation

Avoid monolithic functions unless the file is still genuinely small and clear.

---

## Testing guidance
Add or update lightweight tests when changing behavior.

Prioritize tests for:
- missing ASIN row handling
- queue selection logic
- cache hit / cache miss behavior
- retry decision behavior
- coefficient fallback behavior
- output dataframe enrichment
- timestamp formatting
- permission and configuration edge cases where practical

A small inline logic test is acceptable for MVP.
Do not introduce an overly heavy test framework unless requested.

---

## Documentation guidance
If behavior changes, update documentation.

At minimum, keep `README_keepa.md` accurate regarding:
- input/output file names
- config format
- cache behavior
- differential update queue behavior
- logging behavior
- build steps for local Windows
- packaged runtime expectations

If a user-facing operational rule changes, document it.

---

## Change management rules
When editing this repository:

- prefer minimal changes
- avoid unrelated refactoring
- keep function names and file layout stable where possible
- explain important tradeoffs in comments or README
- do not introduce dependencies casually
- do not add network features unrelated to Keepa
- do not add GUI frameworks unless explicitly requested

If a major design change is needed, make it incremental.

---

## Non-goals unless explicitly requested
Do not add these unless the task specifically asks for them:

- GUI
- web server
- parallel Keepa fetching
- complex database migrations
- cloud deployment
- advanced token scheduler
- burst/drip runtime modes
- packaging automation beyond basic documentation
- category ML models
- external analytics dashboards

Keep the implementation practical and local-first.

---

## Good completion criteria
A change is usually good when:

- it reduces unnecessary Keepa fetches
- it preserves correct output rows
- it keeps logs understandable
- it remains buildable on Windows
- it does not break config or packaging assumptions
- it keeps the codebase easy to operate by one person

When in doubt, optimize for maintainability and token efficiency.