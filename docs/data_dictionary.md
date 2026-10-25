# OLIST-003: Source data dictionary

## Status and scope

All schemas below are **expected and unverified against local Olist CSVs**.
No Olist CSV was present at implementation time. Synthetic fixtures are not
source evidence. Publisher: [Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
Select and record a dataset version before treating these definitions as validated.

This ticket profiles six priority sources plus translations. It does not change
OLIST-001's four-file initial ingestion scope. Reviews and geolocation are only
inventoried if present. Every row remains unchanged.

Types below are proposed compatibility rules, not checks executed by the basic profiler or database tables. IDs and postal
prefixes stay text to preserve leading zeros. Integers must fit PostgreSQL's
signed 32-bit integer. Money uses finite plain decimals, without exponent syntax.
Timestamp strings must match `YYYY-MM-DD HH:MM:SS`; timezone meaning is unresolved.
Non-nullable fields are provisional expectations except required keys, which
also follow DQ-01. Empty means an empty CSV field; whitespace is reported separately.

## Orders: `olist_orders_dataset.csv`

Grain: one order. Candidate primary key: `order_id`.

| Column | Type | Nullable | Meaning |
| --- | --- | --- | --- |
| order_id | text | No | Order identifier |
| customer_id | text | No | Customer record referenced by this order |
| order_status | text | No | Lifecycle status; observed values counted |
| order_purchase_timestamp | timestamp | No | Purchase event; proposed reporting period |
| order_approved_at | timestamp | Yes | Payment approval event |
| order_delivered_carrier_date | timestamp | Yes | Carrier handoff event |
| order_delivered_customer_date | timestamp | Yes | Actual delivery; expected for delivered orders |
| order_estimated_delivery_date | timestamp | No | Promised delivery date/time |

Missing actual delivery can be legitimate before delivery or after cancellation.
Missing approval and carrier dates need status context; they are not universally
required. Missing delivery on delivered orders and delivery before purchase are
warnings. No timezone conversion or KPI calculation occurs here.

## Order items: `olist_order_items_dataset.csv`

Grain: one item position within an order. Candidate key: (`order_id`, `order_item_id`).

| Column | Type | Nullable | Meaning / provisional range |
| --- | --- | --- | --- |
| order_id | text | No | Parent order |
| order_item_id | integer | No | Item sequence, at least 1 |
| product_id | text | No | Referenced product |
| seller_id | text | No | Referenced seller |
| shipping_limit_date | timestamp | No | Shipping deadline |
| price | decimal | No | Merchandise amount, expected BRL, at least 0 |
| freight_value | decimal | No | Freight amount, expected BRL, at least 0 |

Zero price is allowed by the proposed KPI rules and counted for review. Negative
prices are warnings; later transformations decide order eligibility without
removing source rows. Currency remains subject to source verification.

## Customers: `olist_customers_dataset.csv`

Grain: one customer record. Candidate key: `customer_id`. All fields are expected
non-null text.

| Column | Meaning |
| --- | --- |
| customer_id | Customer record identifier used by orders |
| customer_unique_id | Identity across customer records; repetition can be legitimate |
| customer_zip_code_prefix | Postal prefix; preserve leading zeros |
| customer_city | Source city label |
| customer_state | Source state label |

Do not deduplicate by `customer_unique_id` or assume a one-to-one relationship
between that field and orders.

## Products: `olist_products_dataset.csv`

Grain: one product. Candidate key: `product_id`.

| Column | Type | Nullable | Meaning |
| --- | --- | --- | --- |
| product_id | text | No | Product identifier |
| product_category_name | text | Yes | Portuguese category label |
| product_name_lenght | integer | Yes | Name length; preserve source spelling |
| product_description_lenght | integer | Yes | Description length; preserve source spelling |
| product_photos_qty | integer | Yes | Photo count |
| product_weight_g | integer | Yes | Weight in grams |
| product_length_cm | integer | Yes | Package length in centimetres |
| product_height_cm | integer | Yes | Package height in centimetres |
| product_width_cm | integer | Yes | Package width in centimetres |

Numeric attributes are provisionally non-negative; zero values are counted,
not rejected. Missing attributes need investigation, not invented replacements.
Missing category or translation must remain available for the later `Unknown`
category behavior in OLIST-001.

## Sellers: `olist_sellers_dataset.csv`

Grain: one seller. Candidate key: `seller_id`. All fields are expected non-null text.

| Column | Meaning |
| --- | --- |
| seller_id | Seller identifier |
| seller_zip_code_prefix | Postal prefix; preserve leading zeros |
| seller_city | Source city label |
| seller_state | Source state label |

## Payments: `olist_order_payments_dataset.csv`

Grain: one payment sequence for an order. Candidate key:
(`order_id`, `payment_sequential`). Multiple payments per order are legitimate.

| Column | Type | Nullable | Meaning / provisional range |
| --- | --- | --- | --- |
| order_id | text | No | Parent order |
| payment_sequential | integer | No | Payment sequence, at least 1 |
| payment_type | text | No | Payment method |
| payment_installments | integer | No | Installment count, at least 0; zero counted for review |
| payment_value | decimal | No | Payment amount, expected BRL, at least 0 |

Do not impose equality between item prices and payment amounts: freight and
multiple payments affect the comparison. Aggregate each child source separately
before joining to prevent multiplication of amounts.

## Translations: `product_category_name_translation.csv`

Grain: one Portuguese category translation. Candidate key:
`product_category_name`. Both fields are non-null text.

| Column | Meaning |
| --- | --- |
| product_category_name | Portuguese category label |
| product_category_name_english | English label used for category reporting |

## Relationships and deferred sources

| Child | Parent | Missing non-empty references |
| --- | --- | --- |
| orders.customer_id | customers.customer_id | Warning |
| order_items.order_id | orders.order_id | Error under DQ-01 |
| order_items.product_id | products.product_id | Warning; preserve for later Unknown handling |
| order_items.seller_id | sellers.seller_id | Warning |
| order_payments.order_id | orders.order_id | Warning |
| products.product_category_name | translations.product_category_name | Warning |

For future validation, count blank references separately from orphan references.
Missing or duplicate parent keys prevent meaningful relationship checks.
The basic profiler does not execute the relationship checks above. A parent is not required to have children: orders without items are
reported by status rather than rejected automatically.

`olist_order_reviews_dataset.csv` represents review records; its key requires
profiling in a later scope. `olist_geolocation_dataset.csv` represents geographic
observations; a postal prefix is not assumed unique. Neither receives column,
key, or relationship checks in this ticket. Their file names, hashes and basic column statistics
are included if they are present in the selected profiling directory.
