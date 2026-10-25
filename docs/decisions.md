# OLIST-001: Design Decisions

Technical choices follow the approved plan. Proposed business rules and unresolved questions live in [requirements.md](requirements.md#open-questions).

| Decision | Alternative | Reason and trade-off |
| --- | --- | --- |
| One PostgreSQL instance with layer schemas | Separate databases or cloud warehouse | Simple local setup; layers share resources. |
| Immutable MinIO snapshots with checksums | Load directly from local CSV | Reproducible inputs and object-storage practice; adds service setup and storage management. |
| Full replacement and rebuilds first | Incremental loads immediately | Easier reruns; more processing, but avoids unverified change-detection rules. |
| Four KPI-required CSVs first | Load all sources | Keeps scope small; other analytical questions are deferred. |
| Python for movement, dbt for business rules | All logic in Python or Power BI | Reviewable, reusable SQL; requires learning dbt. |
| Separate order and item facts | One wide joined table | Protects grains and totals; requires careful report relationships. |
| Power BI Import after successful batches | DirectQuery or atomic mart publication | Stable imported reports during failures; database marts are not published atomically. |
| Manual runs before Airflow | Orchestration from day one | Easier debugging; initial execution and refresh control are manual. |
