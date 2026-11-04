# SchemaGuard – Schema Drift Detection and Data Quality Pipeline

## 1. Project Overview

SchemaGuard is a Python-based data engineering pipeline designed to process multiple Parquet data batches, detect schema changes, validate incoming records, and quarantine incompatible or invalid data.

The pipeline compares incoming Parquet schemas against a predefined source schema and applies explicitly configured schema evolution rules.

Compatible changes are accepted, while breaking or unapproved changes are rejected and moved to quarantine.

The project uses Python, PyArrow, Pandas, PyYAML, and DuckDB to implement a locally runnable data processing solution.

## 2. Business Problem

Data sources may change their schemas over time. These changes can introduce unexpected columns, remove required fields, or change existing data types.

If these changes are not detected, they can cause data quality problems and failures in downstream analytical systems.

SchemaGuard addresses this problem through:

- Schema drift detection.
- Configurable schema evolution rules.
- Record-level data quality validation.
- Duplicate and foreign-key checks.
- Rejection and quarantine handling.
- Data transformation and target publishing.
- Source-to-target verification and reconciliation.
- Audit logging and batch tracking.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Pipeline implementation |
| PyArrow | Parquet file reading and writing |
| Pandas | Data handling and analysis |
| DuckDB | Target analytical database |
| PyYAML | Schema and configuration management |
| Pytest | Automated testing |
| JSON | Audit logs and rejected record storage |
| Git | Version control |

## 4. Project Structure

```text
SchemaGuard/
│
├── config/
│   ├── source_schema.yaml
│   └── evolution_rules.yaml
│
├── data/
│   ├── input/
│   │   ├── customers/
│   │   └── orders/
│   └── quarantine/
│       └── rejected_records/
│
├── database/
│   ├── audit_logs.json
│   ├── processed_batches.json
│   └── schemaguard.duckdb
│
├── docs/
│   ├── data_dictionary.md
│   ├── architecture.md
│   └── design_decisions.md
│
├── logs/
├── reports/
│
├── scripts/
│   ├── benchmark.py
│   ├── check_database.py
│   ├── generate_data.py
│   ├── generate_drift_data.py
│   ├── generate_invalid_data.py
│   ├── generate_missing_column.py
│   ├── generate_wrong_type.py
│   └── inspect_data.py
│
├── src/
│   ├── batch_tracker.py
│   ├── data_quality.py
│   ├── ingestion.py
│   ├── loader.py
│   ├── pipeline.py
│   ├── quarantine.py
│   ├── schema_detector.py
│   └── schema_validator.py
│
├── tests/
│   ├── test_data_quality.py
│   ├── test_ingestion.py
│   ├── test_pipeline.py
│   ├── test_quarantine.py
│   ├── test_record_quarantine.py
│   ├── test_schema_detector.py
│   └── test_schema_validation.py
│
├── requirements.txt
└── README.md
```

## 5. Source Entities and Business Rules

### Customers

Customer master data is stored in Parquet format.

- Primary key: `customer_id`
- Customer IDs must be unique.
- Customer references must exist before an order can be accepted.

### Orders

Orders represent individual customer transactions.

- Primary key: `order_id`
- Foreign key: `customer_id`
- Each order belongs to a valid customer.
- Order amount cannot be negative.
- Order status must be one of: Pending, Shipped, Delivered, or Cancelled.
- Discount must be between 0 and 100.
- Required fields and nullability are defined in the source schema configuration.

## 6. Schema Management

The expected source schema is maintained in:

`config/source_schema.yaml`

Approved and rejected schema changes are configured in:

`config/evolution_rules.yaml`

Examples of supported schema checks:

- Addition of an explicitly approved nullable column.
- Missing required columns.
- Incompatible data type changes.
- Unexpected columns.
- Safe integer type widening where distinguishable.

Unapproved or breaking schema changes are quarantined.

## 7. Pipeline Architecture

The pipeline follows this processing sequence:

1. **Ingestion:** Read incoming Parquet batches.
2. **Batch tracking:** Check whether the same batch has already been processed using its SHA-256 file hash.
3. **Schema detection:** Compare incoming and expected schemas.
4. **Schema validation:** Apply approved evolution rules.
5. **Data quality validation:** Check required fields, amounts, statuses, duplicate order IDs, and customer references.
6. **Quarantine:** Store rejected batches or individual invalid records separately.
7. **Transformation:** Calculate the `amount_after_discount` field.
8. **Target publishing:** Load valid transformed records into DuckDB using batch insertion.
9. **Reconciliation:** Compare received, accepted, rejected, and published record counts and amount totals.
10. **Source-to-target verification:** Verify published order IDs and important field values against the transformed source records.
11. **Audit logging:** Record run IDs, timestamps, record counts, processing status, and failure reasons.

## 8. Installation and Setup

### Prerequisites

- Python 3.10 or later recommended.
- Visual Studio Code or another Python editor.
- Git (optional, for version control).

### Step 1: Open the project folder

Open the SchemaGuard project folder in VS Code.

### Step 2: Create a virtual environment

```powershell
python -m venv .venv
```

### Step 3: Activate the virtual environment

```powershell
.venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## 9. Running the Pipeline

Run the following command from the project root directory:

```powershell
python -c "from src.pipeline import run_data_quality_pipeline; run_data_quality_pipeline('orders_batch_001.parquet')"
```

Replace the filename with the name of another available batch in `data/input/orders/` when required.

The pipeline processes the selected batch and reports its processing status.

## 10. Generating Sample Data

The project includes scripts for generating sample, large-scale, and test datasets.

Generate sample and large datasets:

```powershell
python scripts/generate_data.py
```

The large dataset generator supports configurable customer and order counts, with a fixed random seed for reproducibility.

The default large dataset contains:

- 5,000 customers.
- 100,000 orders.
- Randomly generated order amounts, dates, statuses, and discounts.

**Note:** The main generator also writes sample batch files. Running it again can overwrite existing sample data.

Generate schema drift test data:

```powershell
python scripts/generate_drift_data.py
```

Generate missing-column test data:

```powershell
python scripts/generate_missing_column.py
```

Generate incompatible data-type test data:

```powershell
python scripts/generate_wrong_type.py
```

Generate invalid and boundary test data:

```powershell
python scripts/generate_invalid_data.py
```

### Database Inspection

Run the following script to inspect stored order records in the DuckDB database:

```powershell
python scripts/check_database.py

## 11. Automated Testing

Run the complete test suite:

```powershell
python -m pytest tests/ -v
```

Latest verified test execution:

**36 tests passed.**

The test suite covers:

- Data quality validation.
- Missing and invalid values.
- Duplicate order IDs.
- Customer reference validation.
- Parquet ingestion.
- Pipeline execution.
- Record and file quarantine.
- Schema drift detection.
- Approved and rejected schema evolution.

## 12. Idempotency and Recovery

SchemaGuard uses SHA-256 file hashing to identify previously processed batches.

- Successfully processed batches are tracked.
- Repeated processing of the same file contents is skipped.
- Failed batches are not marked as successfully processed and can be retried.
- Rejected schema batches are quarantined.
- Repeated rejected records are prevented from being duplicated in the quarantine JSON file.
- Audit logs maintain the history of pipeline executions.

The pipeline also uses database transactions during target publishing to help prevent partial database writes.

## 13. Audit Logging and Monitoring

Pipeline execution details are stored in `database/audit_logs.json`.

The audit information includes:

- Run ID.
- Source filename.
- Start and end timestamps.
- Records received.
- Records accepted.
- Records rejected.
- Records published.
- Records already existing.
- Processing status.
- Failure reason, where applicable.

Processed batch information is maintained in `database/processed_batches.json`.

## 14. Performance Testing and Optimization

A reproducible synthetic dataset containing 100,000 order records was used for performance evaluation.

### Parquet reading benchmark

| Measurement | Result |
|---|---:|
| Dataset | orders_large.parquet |
| Records | 100,000 |
| File size | Approximately 1.65 MB |
| Reading time | 1.5993 seconds |
| Reading speed | 62,528 rows/second |

### Database insertion benchmark

Two insertion approaches were compared using the same 10,000 records and separate temporary DuckDB databases.

| Measurement | Individual insertion | Batch insertion |
|---|---:|---:|
| Records inserted | 10,000 | 10,000 |
| Batch size | 1 | 500 |
| Execution time | 7.4610 seconds | 3.2894 seconds |

**Measured batch insertion improvement: approximately 55.91%.**

### Optimization implemented

The target loader uses DuckDB's `executemany()` method to insert records in batches of 1,000 rather than issuing a separate insertion call for every record.

The benchmark uses a batch size of 500 for its controlled comparison. The measured improvement applies to that benchmark configuration and test environment.

Run the performance benchmark using:

```powershell
python scripts/benchmark.py
```

The benchmark measures Parquet reading performance and compares individual and batch database insertion. It uses temporary databases for the insertion comparison and does not modify the actual SchemaGuard database.

The benchmark is not a measurement of the complete end-to-end pipeline.

## 15. Known Limitations

- The implementation uses local Parquet files and DuckDB rather than a cloud-based distributed processing platform.
- The performance benchmark measures Parquet reading and controlled database insertion, not the complete pipeline.
- Some schema type distinctions, such as integer and bigint, may not be distinguishable from the physical Parquet representation.
- Restart recovery and historical backfill have not been fully validated under production-scale failure scenarios.
- Further integration testing is required for concurrent processing and larger workloads.

## 16. Future Improvements

- Add cloud storage and distributed processing support.
- Improve operational monitoring and reporting.
- Extend restart and backfill capabilities.
- Add more end-to-end integration tests.
- Improve performance for larger datasets.
- Add automated performance regression testing.

## 17. Conclusion

SchemaGuard demonstrates a locally runnable data engineering pipeline that detects schema drift, applies configurable schema evolution rules, validates data quality, quarantines invalid data, transforms accepted records, and publishes results into an analytical database.

The project emphasizes data correctness, reproducibility, traceability, idempotency, and safe batch processing.
