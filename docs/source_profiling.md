# OLIST-003: Source profiling

## Scope

Use `scripts/profile_sources.py` to understand local CSVs before ingestion.
It reports file name, SHA-256, row/column counts, exact duplicate rows, and each
column's empty, whitespace-only and distinct non-blank value counts.
All values stay strings, preserving identifiers and leading zeros.
No extra packages are needed.

The script profiles every top-level `*.csv` in the chosen directory. It does not
require all expected sources. Compare the inventory with
[data_dictionary.md](data_dictionary.md): prioritize orders, order_items,
customers, products, sellers and order_payments, plus category translations for
the existing KPI scope. Reviews and geolocation can be explored later.

`config/data_contracts.yml` remains a provisional reference using JSON syntax
(valid YAML 1.2). The profiler does not read or enforce it. Key uniqueness,
relationships, timestamp validity and business ranges need later targeted checks
and dbt tests. Exact duplicate rows are not the same as duplicate primary keys.

## Run in PowerShell

Download one snapshot from the Olist publisher, record its URL, version, download
date and archive checksum locally, then extract unchanged CSVs into the ignored
`data/source/olist/<snapshot>/` directory. Do not mix versions or commit datasets.

```powershell
.\.venv\Scripts\python.exe .\scripts\profile_sources.py `
  --source-dir '.\data\source\olist\<snapshot>' `
  --output '.\data\profiling\<snapshot>\profile.json'
$LASTEXITCODE
```

Exit 0 means the report was written, not that business quality rules passed.
Exit 1 means profiling failed. Missing CSVs, invalid encoding, malformed records,
missing/duplicate headers and wrong field counts stop the run. Output must be
outside the source directory; existing reports are never overwritten.

Read the JSON report and investigate unexpected counts. Missing delivery dates
can be legitimate for undelivered orders. Missing product categories need later
`Unknown` handling. Never repair or remove source rows automatically.

## Verify and limits

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_profile_sources.py -v
git check-ignore data/source/ data/profiling/
git status --short
```

Run again with another output filename: identical inputs produce identical JSON.
Do not edit CSVs during profiling; SHA-256 records the input identity before read.
Sources are only opened for reading. Distinct values and row tuples are held in
memory; large files may require a narrower profiling scope.
Empty fields and whitespace-only fields are counted separately. Literal `NULL`
is text. No data types are inferred and no record samples are copied to reports.
A header-only file has zero rows; completely empty files cannot supply a schema.

**Real Olist results remain unavailable:** no local source CSVs have been profiled.
Synthetic tests verify code behavior only. Completion still requires a selected
snapshot, reviewed findings, and documented decisions for later transformations.
The profiler creates no database objects or ingestion infrastructure.
