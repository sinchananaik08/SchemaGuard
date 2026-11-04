# SchemaGuard – Data Dictionary

## 1. Overview

This document describes the entities, columns, data types, keys, relationships, constraints, and derived fields used in the SchemaGuard pipeline.

The project processes two primary source entities: Customers and Orders.

## 2. Customers Entity

**Description:** Stores customer master information.

**Grain:** One record per customer.

**Primary Key:** `customer_id`

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| customer_id | Integer | No | Unique customer identifier |
| customer_name | String | No | Customer name |
| email | String | No | Customer email address |
| city | String | Yes | Customer's city |

### Business Rules

- `customer_id` uniquely identifies each customer.
- Customer identifiers must not be null.
- Customer names and email addresses are required.
- Customer records are used to validate order references.

## 3. Orders Entity

**Description:** Stores customer order transactions.

**Grain:** One record per order.

**Primary Key:** `order_id`

**Foreign Key:** `customer_id` references `customers.customer_id`.

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| order_id | String | No | Unique order identifier |
| customer_id | Integer | No | Customer associated with the order |
| order_date | Timestamp | No | Date and time of the order |
| amount | Double | No | Original order amount |
| status | String | No | Current order status |
| discount | Double | Yes | Discount percentage |

### Business Rules

- Every order must have a unique `order_id`.
- Every order must reference an existing customer.
- Order amount must be zero or greater.
- Allowed order statuses are Pending, Shipped, Delivered, and Cancelled.
- Discount must be between 0 and 100.
- Required fields must not contain null values.

**Implementation note:** The source schema defines `order_date` as non-nullable. However, the current data-quality validator treats a missing order date as optional for backward compatibility. This is a known validation inconsistency.

## 4. Target Orders Entity

**Description:** Stores validated and transformed order records in DuckDB.

The target table is created and managed by `src/loader.py`.

| Column | Data Type | Description |
|---|---|---|
| order_id | VARCHAR | Unique order identifier and primary key |
| customer_id | INTEGER | Customer reference |
| order_date | TIMESTAMP | Order timestamp |
| amount | DOUBLE | Original order amount |
| status | VARCHAR | Order status |
| discount | DOUBLE | Discount percentage |
| payment_method | VARCHAR | Approved optional schema-evolution field, when supplied |
| amount_after_discount | DOUBLE | Calculated order amount after discount |

The target table contains the original order fields, the approved optional `payment_method` field, and the derived `amount_after_discount` field.

## 5. Derived Fields

### amount_after_discount

This field is calculated during transformation.

**Formula:**

`amount_after_discount = amount × (1 - discount / 100)`

If discount is missing, it is treated as zero.

**Examples:**

| Original Amount | Discount | Amount After Discount |
|---:|---:|---:|
| 1000 | 10% | 900 |
| 500 | 0% | 500 |
| 750 | Missing | 750 |

The calculation is deterministic and rounded to two decimal places.

## 6. Schema Evolution Rules

Schema evolution rules are maintained in `config/evolution_rules.yaml`.

### Approved changes

- Addition of explicitly approved nullable columns.
- Safe integer type widening where supported by the schema representation.

### Rejected changes

- Removal of required columns.
- Incompatible data type changes.
- Addition of required columns without defaults.
- Unapproved column renaming.
- Unexpected columns not covered by approved rules.

Rejected schema batches are moved to the quarantine directory.

## 7. Data Quality and Referential Integrity

SchemaGuard performs the following checks:

- Required field validation.
- Primary key and duplicate order ID validation.
- Customer foreign-key validation.
- Numeric amount validation.
- Allowed order status validation.
- Discount range validation.
- Schema compatibility validation.

Invalid records are stored separately with their source filename and rejection reasons.

## 8. Audit and Batch Tracking

### Audit records

Stored in `database/audit_logs.json`.

Important fields include:

- `run_id`
- `source_file`
- `start_time`
- `end_time`
- `records_received`
- `records_accepted`
- `records_rejected`
- `records_published`
- `records_already_existing`
- `status`
- `failure_reason`

### Processed batch tracking

Stored in `database/processed_batches.json`.

SHA-256 file hashes are used to identify previously processed batches and prevent unintended reprocessing.

## 9. Naming Conventions

- Table and column names use snake_case.
- `run_id` identifies an individual pipeline execution.
- `source_file` identifies the originating Parquet batch.
- Timestamps use ISO-8601 format.
- Order IDs and customer IDs provide stable record identification.