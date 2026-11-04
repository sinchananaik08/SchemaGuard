
from pathlib import Path
import json
import math

from src.ingestion import read_parquet_file
from src.data_quality import separate_valid_and_invalid_orders
from src.quarantine import quarantine_records, quarantine_file
from src.loader import load_valid_orders, verify_orders_in_database

from src.batch_tracker import (
    mark_batch_as_processed,
    is_batch_processed,
    calculate_file_hash,
    create_run_id,
    get_current_timestamp,
    create_audit_record
)

from src.schema_detector import (
    load_expected_schema,
    read_incoming_schema,
    read_incoming_nullability,
    detect_schema_drift
)

from src.schema_validator import validate_schema_changes


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_FILE = PROJECT_ROOT / "database" / "audit_logs.json"


def save_audit_record(audit_record):
    """Append an audit record without losing previous records."""

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    audit_logs = []

    if AUDIT_FILE.exists():
        with open(AUDIT_FILE, "r", encoding="utf-8") as file:
            audit_logs = json.load(file)

    audit_logs.append(audit_record)

    with open(AUDIT_FILE, "w", encoding="utf-8") as file:
        json.dump(audit_logs, file, indent=4)


def transform_orders(valid_orders):
    """
    Transform accepted orders by calculating the amount
    payable after applying the discount.

    The original amount and discount are preserved.
    """

    transformed_orders = []

    for order in valid_orders:
        transformed_order = order.copy()

        amount = order["amount"]
        discount = order.get("discount")

        if discount is None:
            discount = 0.0

        amount_after_discount = amount * (1 - discount / 100)

        transformed_order["amount_after_discount"] = round(
            amount_after_discount, 2
        )

        transformed_orders.append(transformed_order)

    return transformed_orders


def run_data_quality_pipeline(order_batch_name="orders_batch_001.parquet"):

    run_id = create_run_id()
    start_time = get_current_timestamp()

    records_received = 0
    records_accepted = 0
    records_rejected = 0
    records_published = 0
    records_already_existing = 0

    status = "FAILED"
    failure_reason = None

    try:
        # Step 1: Locate the incoming order file
        order_file = (
            PROJECT_ROOT
            / "data"
            / "input"
            / "orders"
            / order_batch_name
        )

        if not order_file.exists():
            raise FileNotFoundError(
                f"Input file not found: {order_file}"
            )

        # Step 2: Check whether this file was processed before
        file_hash = calculate_file_hash(order_file)

        if is_batch_processed(file_hash, order_batch_name):
            print(f"Batch '{order_batch_name}' was already processed.")
            print("Skipping this batch to avoid duplicate processing.")

            status = "SKIPPED"
            failure_reason = (
                "This file's contents were already processed."
            )

            return [], []

        print("Starting SchemaGuard pipeline...")
        print("Run ID:", run_id)
        print("Start time:", start_time)

        # Step 3: Read customer data
        customer_file = (
            PROJECT_ROOT
            / "data"
            / "input"
            / "customers"
            / "customers_batch_001.parquet"
        )

        customers = read_parquet_file(customer_file)

        customer_ids = {
            customer["customer_id"] for customer in customers
        }

        # Step 4: Detect schema drift
        expected_schema = load_expected_schema()

        incoming_schema = read_incoming_schema(order_file)

        incoming_nullability = read_incoming_nullability(order_file)

        drift_result = detect_schema_drift(
            incoming_schema,
            expected_schema,
            "orders"
        )

        print("\nSCHEMA DRIFT RESULT")
        print("-------------------------")
        print(drift_result)

        # Step 5: Validate schema changes
        schema_decision = validate_schema_changes(
            drift_result,
            "orders",
            incoming_schema,
            incoming_nullability
        )

        print("Schema validation:", schema_decision["status"])
        print("Reason:", schema_decision["reason"])

        # Step 6: Quarantine incompatible schema
        if schema_decision["status"] == "REJECTED":

            quarantine_file(
                order_file,
                schema_decision["reason"]
            )

            mark_batch_as_processed(
                order_batch_name,
                file_hash
            )

            status = "QUARANTINED"
            failure_reason = schema_decision["reason"]

            return [], []

        # Step 7: Read incoming orders
        orders = read_parquet_file(order_file)
        records_received = len(orders)

        # Step 8: Validate individual records
        valid_orders, invalid_orders = separate_valid_and_invalid_orders(
            orders,
            customer_ids
        )

        records_accepted = len(valid_orders)
        records_rejected = len(invalid_orders)

        # Step 9: Reconcile incoming record counts
        reconciled_count = records_accepted + records_rejected

        print("\nDATA RECONCILIATION")
        print("-------------------------")
        print("Records received:", records_received)
        print("Records accepted + rejected:", reconciled_count)

        if records_received != reconciled_count:
            raise ValueError(
                "Data reconciliation failed! "
                "Received records do not match accepted and rejected records."
            )

        print("Record reconciliation: PASSED")

        # Step 9B: Reconcile order amounts
        def get_valid_amount_total(records):
            total = 0.0
            count = 0

            for record in records:
                amount = record.get("amount")

                if (
                    isinstance(amount, (int, float))
                    and not isinstance(amount, bool)
                    and math.isfinite(amount)
                ):
                    total += amount
                    count += 1

            return total, count

        incoming_amount, incoming_amount_count = (
            get_valid_amount_total(orders)
        )

        accepted_amount, accepted_amount_count = (
            get_valid_amount_total(valid_orders)
        )

        rejected_amount, rejected_amount_count = (
            get_valid_amount_total(
                [item.get("record", {}) for item in invalid_orders]
            )
        )

        accounted_amount = accepted_amount + rejected_amount

        print("\nAMOUNT RECONCILIATION")
        print("-------------------------")
        print("Incoming amount total:", incoming_amount)
        print("Accepted amount total:", accepted_amount)
        print("Rejected amount total:", rejected_amount)
        print("Amounts checked:", incoming_amount_count)
        print(
            "Amounts accounted for:",
            accepted_amount_count + rejected_amount_count
        )

        if (
            incoming_amount_count
            != accepted_amount_count + rejected_amount_count
        ):
            raise ValueError(
                "Amount reconciliation failed! "
                "Some records have missing or invalid amounts."
            )

        if abs(incoming_amount - accounted_amount) > 0.000001:
            raise ValueError(
                "Amount reconciliation failed! "
                "Incoming and accounted amounts do not match."
            )

        print("Amount reconciliation: PASSED")

        # Step 10: Quarantine invalid records
        if invalid_orders:
            quarantine_records(invalid_orders, order_batch_name)

        # Step 11: Transform accepted orders
        transformed_orders = transform_orders(valid_orders)

        print("\nTRANSFORMATION")
        print("-------------------------")
        print("Orders transformed:", len(transformed_orders))
        print("Calculated amount after discount.")

        # Step 12: Publish transformed orders
        records_published = load_valid_orders(transformed_orders)

        records_already_existing = (
            records_accepted - records_published
        )

        if records_already_existing < 0:
            raise ValueError(
                "Publication reconciliation failed! "
                "Published count exceeds accepted count."
            )

        if (
            records_accepted
            != records_published + records_already_existing
        ):
            raise ValueError(
                "Publication reconciliation failed! "
                "Accepted orders do not match published and existing orders."
            )

        print("\nPUBLICATION RECONCILIATION")
        print("-------------------------")
        print("Accepted orders:", records_accepted)
        print("New orders published:", records_published)
        print("Already existing orders:", records_already_existing)
        print("Publication reconciliation: PASSED")

        # Step 13: Verify actual records in DuckDB
        verification_passed = verify_orders_in_database(
            transformed_orders
        )

        if not verification_passed:
            raise ValueError(
                "Source-to-target verification failed! "
                "Stored database records do not match expected records."
            )

        # Step 14: Mark batch as processed
        mark_batch_as_processed(
            order_batch_name,
            file_hash
        )

        status = "SUCCESS"

        # Step 15: Display pipeline summary
        print("\nPIPELINE SUMMARY")
        print("-------------------------")
        print("Customers read:", len(customers))
        print("Orders received:", records_received)
        print("Valid orders:", records_accepted)
        print("Invalid orders:", records_rejected)
        print("Orders transformed:", len(transformed_orders))
        print("Orders published to database:", records_published)
        print("Already existing orders:", records_already_existing)
        print("Source-to-target verification: PASSED")

        return valid_orders, invalid_orders

    except Exception as error:
        failure_reason = str(error)
        status = "FAILED"
        raise

    finally:
        end_time = get_current_timestamp()

        audit_record = create_audit_record(
            run_id=run_id,
            source_file=order_batch_name,
            start_time=start_time,
            end_time=end_time,
            records_received=records_received,
            records_accepted=records_accepted,
            records_rejected=records_rejected,
            status=status,
            failure_reason=failure_reason,
            records_published=records_published,
            records_already_existing=records_already_existing
        )

        save_audit_record(audit_record)

        print("\nAUDIT RECORD")
        print("-------------------------")
        print(audit_record)
