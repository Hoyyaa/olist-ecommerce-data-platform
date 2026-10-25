# OLIST-001: Business Requirements

## Purpose and scope

Help business analysts track monthly sales, category contributions, and delivery performance using a maintainable historical batch platform.

This ticket covers documentation only. Pipeline code, infrastructure, dashboards, and Airflow are later work. Real-time processing, profit, inventory, forecasting, and refund accounting are outside the initial scope.

## Evidence

The [Olist dataset page](https://www.kaggle.com/olistbr/brazilian-ecommerce/home/) describes anonymized Brazilian marketplace data, about 100,000 orders from 2016-2018, and orders involving multiple sellers. No local CSVs were available: the schema and relationships below are expected, not verified.

## Requirements and acceptance criteria

These are requirements for later implementation, not completed data checks.

| ID | Measurable requirement |
| --- | --- |
| BR-01 | Provide all six KPIs below; category GMV including `Unknown` must equal overall GMV under the same filters. |
| BR-02 | Count each eligible order once; show source coverage, batch ID, refresh time, and exclusion counts. |
| DQ-01 | Check all required files and columns. Block publication for missing inputs, duplicate expected keys, missing required keys, or orphan order items. |
| DQ-02 | Report invalid prices, missing purchase/delivery dates, and unknown categories for every batch. Preserve source records; never silently deduplicate. |
| OP-01 | Rerunning the same snapshot must preserve business row counts and KPI values without duplicates. |
| OP-02 | Trace records to source files and batches; record file checksums and load times. Refresh Power BI only after all required checks pass. |

## Expected sources and grain

Grain means what one row represents. The first four files are required initially.

| CSV | Expected grain / key | Required analytical columns besides keys |
| --- | --- | --- |
| `olist_orders_dataset.csv` | One order / `order_id` | `order_status`, `order_purchase_timestamp`, `order_delivered_customer_date`, `order_estimated_delivery_date` |
| `olist_order_items_dataset.csv` | One item position / (`order_id`, `order_item_id`) | `product_id`, `price` |
| `olist_products_dataset.csv` | One product / `product_id` | `product_category_name` |
| `product_category_name_translation.csv` | One translation / `product_category_name` | `product_category_name_english` |
| `olist_customers_dataset.csv` | One customer record / `customer_id` | Deferred: customers and geography |
| `olist_sellers_dataset.csv` | One seller / `seller_id` | Deferred: seller analysis |
| `olist_order_payments_dataset.csv` | One payment sequence / (`order_id`, `payment_sequential`) | Deferred: payments |
| `olist_order_reviews_dataset.csv` | One review record / key requires profiling | Deferred: satisfaction |
| `olist_geolocation_dataset.csv` | One geographic observation / postal prefix is not assumed unique | Deferred: maps |

Relationships and join risks:

- Orders have many items through `order_id`; products and sellers have many items through `product_id` and `seller_id`.
- Orders reference customers through `customer_id`. Future repeat-customer analysis should use `customer_unique_id` after validation.
- Products reference translations through `product_category_name`.
- Payments and reviews may have multiple rows per order. Aggregate each child source before combining it with item totals to avoid multiplying money values.
- Customer/seller postal prefixes may match multiple geographic rows; define an aggregation rule before joining.

## KPI definitions - proposed business rules

**Sales population:** delivered orders with a valid purchase timestamp, at least one item, and valid non-negative prices for every item. Exclude an entire order if any item price is invalid; report exclusions. Allow zero prices but count them for review.

Use purchase time for period filters (inclusive start, exclusive end). Sum item `price` in BRL, excluding freight and refund adjustments. This is merchandise value, not accounting revenue. Preserve source timestamps without timezone conversion pending verification. Retain missing products/categories as `Unknown`.

All sales KPIs below use this population. Delivery has its own population.

| KPI | Meaning and calculation | Base grain -> report grain | Sources |
| --- | --- | --- | --- |
| GMV | Merchandise value: sum `price` | Item -> selected purchase period | Orders + items |
| Total orders | Eligible order count: distinct `order_id` | Order -> selected purchase period | Orders + items |
| Average order value | Merchandise value per order: GMV / total orders | Order -> selected purchase period | Orders + items |
| Monthly sales | GMV grouped by purchase year-month; label `Monthly GMV` | Item -> month | Orders + items |
| Sales by product category | Sum `price` by category, including `Unknown` | Item -> category, optionally month | Orders + items + products + translation |
| On-time delivery rate | 100 x on-time delivered orders / eligible delivery orders | Order -> purchase period, optionally month | Orders |

**Delivery population:** delivered orders with valid purchase, actual delivery, and estimated delivery dates. Exclude unparseable dates and delivery dates before purchase. Item prices do not affect eligibility. On time means the date portion of `order_delivered_customer_date` is on or before `order_estimated_delivery_date`; same-day delivery qualifies. Show numerator, denominator, and excluded counts. Undelivered backlog is outside this rate.

Return null for ratios with zero denominators. Calculate AOV from totals, not monthly averages. A covered period with no eligible sales has zero GMV and orders; do not turn missing coverage into zero sales. Warn that recent purchase months may be incomplete while orders await delivery.

## Open questions

- Confirm the proposed KPI rules: delivered-only sales, purchase-period reporting, BRL excluding freight/refunds, calendar-date delivery comparison, and whole-order exclusion for invalid prices.
- Confirm English category labels and the translation-file dependency.
- Select the dataset version and verify headers, keys, relationships, currency, timezone meaning, and license.
- Set a runtime target after measuring the local batch.

For ticket acceptance, review this contract, [architecture.md](architecture.md), and [decisions.md](decisions.md). Business-rule approval and source validation remain open.
