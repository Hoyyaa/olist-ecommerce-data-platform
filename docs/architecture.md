# OLIST-001: Architecture

## Data flow and responsibilities

```mermaid
flowchart LR
    CSV[Olist CSV] --> Bronze[MinIO: Bronze]
    Bronze --> Loader[Python loader]
    Loader --> Raw[PostgreSQL: Raw]
    Raw --> Staging[dbt: Staging]
    Staging --> Intermediate[dbt: Intermediate]
    Intermediate --> Marts[dbt: Marts]
    Marts --> BI[Power BI Import]
```

Use one PostgreSQL instance with separate schemas for each database layer.

| Component | Responsibility |
| --- | --- |
| MinIO / Bronze | Preserve unchanged source files in immutable snapshots. |
| Python | Upload, validate, load Raw, and record file/batch metadata. |
| PostgreSQL / Raw | Store source-shaped records with file and batch references. |
| dbt Staging | Standardize names and types; flag invalid values. |
| dbt Intermediate | Define reusable totals, eligibility flags, and exclusion reasons. |
| dbt Marts | Publish reporting tables at documented grains. |
| Power BI | Present measures following the [KPI contract](requirements.md#kpi-definitions---proposed-business-rules). |
| Docker Compose | Later: run local MinIO and PostgreSQL consistently. |
| Airflow | Later: schedule existing batch tasks and safe retries. |

Use decimals for money and text for identifiers/postal prefixes where leading zeros matter. Keep credentials and source CSVs outside Git.

## Reporting grains

| Table | Grain and use |
| --- | --- |
| Order fact | One row per order: totals, status, purchase/delivery dates, eligibility, and exclusion reasons. Use for order counts and overall AOV. |
| Order-item fact | One row per (`order_id`, `order_item_id`): price, product/category, purchase date, and sales eligibility. Use for category GMV. |
| Date dimension | One row per date: shared calendar filtering. |

Retain ineligible orders for audit, filter measures explicitly, and reconcile eligible item totals to order totals. Avoid direct fact-to-fact relationships. Additional dimensions need a business requirement.

## Batch and reruns

Start with full snapshot replacement and full dbt rebuilds:

1. Identify a snapshot by file names/checksums; give each execution a separate attempt ID.
2. Preserve files in Bronze and load temporary database tables.
3. Apply the [required checks](requirements.md#requirements-and-acceptance-criteria), then replace active Raw tables in one transaction.
4. Rebuild dbt layers and reconcile order/item and category/overall totals.
5. Mark success and permit Power BI refresh only after checks pass.

Run one batch at a time. Failure before Raw replacement leaves the previous snapshot active. Failure during transformation may leave partially updated marts: block refresh, retain Power BI's previous import, fix the issue, and rerun the preserved snapshot. This is not an atomic pipeline; use a controlled refresh window initially.

## Future limits

Add Airflow after manual runs are reliable. Incremental ingestion needs stable keys, change detection, and upserts; maximum purchase time alone misses updates to old orders. The static dataset provides no proven live change feed. Add stronger publication controls or performance optimizations only when measured needs justify them.
