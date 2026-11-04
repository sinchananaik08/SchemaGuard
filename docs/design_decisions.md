# SchemaGuard – Design Decisions and Trade-offs

## 1. Introduction

This document explains the major technical decisions, design choices, assumptions, and trade-offs made while developing SchemaGuard.

The solution prioritizes correctness, maintainability, reproducibility, and data quality over unnecessary infrastructure complexity.

## 2. Technology Selection

| Technology | Reason for Selection | Trade-off |
|---|---|---|
| Python | Simple and widely used for data engineering | May require optimization for very large workloads |
| PyArrow | Efficient Parquet reading and schema inspection | Requires understanding of Arrow data types |
| DuckDB | Lightweight analytical database that runs locally | Not intended as a complete distributed database |
| YAML | Separates schema definitions and evolution rules from code | Configuration must be validated carefully |
| JSON | Simple storage for audit logs and rejected records | Large log files may become inefficient |
| Pytest | Supports automated testing of individual modules | Mocked tests do not replace integration testing |

## 3. Modular Architecture

The pipeline is divided into separate modules:

- `ingestion.py`: Reads incoming Parquet files.
- `schema_detector.py`: Detects schema changes.
- `schema_validator.py`: Applies schema evolution rules.
- `data_quality.py`: Validates individual records.
- `quarantine.py`: Handles rejected files and records.
- `loader.py`: Publishes valid records into DuckDB.
- `batch_tracker.py`: Tracks processed batches.
- `pipeline.py`: Coordinates the processing workflow.

**Design decision:** Separate responsibilities into modules instead of implementing the entire pipeline in one file.

**Benefit:** Individual components can be tested and maintained independently.

**Trade-off:** More modules require clear interfaces and imports.

## 4. Schema Configuration and Evolution

Expected schemas and evolution rules are maintained in separate YAML files.

**Design decision:** Use configuration-driven schema validation rather than hardcoding every schema rule in the pipeline.

**Benefit:**
- Schema changes can be managed through configuration.
- Approved changes are explicit.
- Incompatible changes can be rejected consistently.

**Trade-off:** The configuration and validation logic must remain synchronized.

## 5. Quarantine Strategy

SchemaGuard uses two separate rejection paths.

### Schema-level rejection

Entire Parquet files are moved into `data/quarantine/` when their schemas contain breaking or unapproved changes.

### Record-level rejection

Individual invalid order records are saved in `data/quarantine/rejected_records/rejected_orders.json`.

**Design decision:** Separate schema failures from individual record failures.

**Benefit:** A batch with a compatible schema can still publish valid records even when some individual records are invalid.

**Trade-off:** Rejected records require separate investigation and possible correction before reprocessing.

## 6. Idempotency Strategy

SchemaGuard calculates SHA-256 hashes of incoming files to identify previously processed batches.

**Design decision:** Use file-content hashes instead of relying only on filenames.

**Benefit:**
- Identical file contents can be recognized even if filenames differ.
- Repeated processing of an already processed batch can be skipped.

**Trade-off:** If a single record changes, the entire file hash changes. The updated batch is therefore treated as a different input.

The current implementation does not provide a complete transactional recovery mechanism for every possible interruption during publishing.

## 7. Data Transformation

The pipeline calculates the `amount_after_discount` field.

Formula:

`amount_after_discount = amount × (1 - discount / 100)`

Missing discounts are treated as zero, and the result is rounded to two decimal places.

**Design decision:** Apply deterministic transformations before publishing records into DuckDB.

**Benefit:** The same input values produce the same transformed output.

**Trade-off:** Future business rules may require additional transformation logic and validation.

## 8. Target Storage Selection

DuckDB is used as the local analytical database.

**Design decision:** Use DuckDB instead of requiring an external database server.

**Benefit:**
- Easy local setup.
- No cloud credentials required.
- Supports SQL queries and analytical operations.
- Suitable for demonstrating the project within a limited development period.

**Trade-off:** This implementation does not provide the scalability, distributed processing, or operational capabilities of a large cloud data platform.

## 9. Data Generation Strategy

Synthetic data is used for reproducible testing.

The data generator uses a fixed random seed and supports generating a larger dataset of 100,000 or more orders.

Separate test generators cover schema changes, missing columns, incompatible data types, and invalid records.

**Design decision:** Use synthetic datasets instead of external production data.

**Benefit:** Data can be regenerated consistently without privacy or licensing concerns.

**Trade-off:** Synthetic data may not represent every complexity found in real production systems.

## 10. Performance Considerations

A Parquet read benchmark was performed using a dataset of 100,000 order records.

Recorded results:

- Dataset size: 100,000 records.
- File size: Approximately 1.65 MB.
- Read time: Approximately 1.77 seconds.
- Read throughput: Approximately 56,416 records per second.

This benchmark measures Parquet reading only, not complete pipeline execution.

Further optimization could include batch-oriented database inserts, efficient columnar operations, and avoiding unnecessary repeated file reads.

Any optimization should be benchmarked against the existing implementation and must preserve accurate inserted-row counts and idempotency.

## 11. Known Limitations

- The solution currently uses local file storage and DuckDB.
- Full end-to-end performance has not yet been benchmarked.
- Zero-row Parquet handling requires additional verification.
- Restart recovery and historical backfill are not fully implemented or demonstrated.
- Target database reconciliation requires additional verification.
- Some logical integer type distinctions may not be represented distinctly in Parquet.
- Additional integration testing is required beyond the existing unit tests.

## 12. Future Improvements

Potential improvements include:

1. Support for cloud object storage.
2. Distributed processing for larger datasets.
3. More advanced pipeline monitoring and reporting.
4. Stronger transactional recovery and restart handling.
5. Explicit historical backfill support.
6. Automated source-to-target reconciliation reports.
7. Expanded end-to-end integration testing.
8. Performance optimization of database publishing.

## 13. Conclusion

SchemaGuard demonstrates a modular and configurable approach to schema drift detection and data quality management.

The design prioritizes explicit schema evolution rules, traceable rejection handling, deterministic transformations, reproducible testing, and safe batch processing.

The local implementation provides a practical foundation that can be extended to larger production-oriented data engineering systems.