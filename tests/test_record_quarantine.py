
from pathlib import Path
import sys
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_quality import separate_valid_and_invalid_orders
from src.quarantine import quarantine_records


def test_separate_valid_and_invalid_records():
    orders = [
        {"order_id": "ORD301", "amount": 500, "status": "Shipped"},
        {"order_id": "ORD302", "amount": -200, "status": "Pending"},
        {"order_id": "ORD303", "amount": 300, "status": "Processing"}
    ]

    valid_orders, invalid_orders = separate_valid_and_invalid_orders(orders)

    assert len(valid_orders) == 1
    assert len(invalid_orders) == 2
    assert len(valid_orders) + len(invalid_orders) == len(orders)


def test_rejected_records_are_saved_in_quarantine():
    orders = [
        {"order_id": "ORD401", "amount": -200, "status": "Pending"}
    ]

    _, invalid_orders = separate_valid_and_invalid_orders(orders)

    output_file = quarantine_records(
        invalid_orders,
        "pytest_quarantine_batch.parquet"
    )

    assert output_file.exists()

    # Clean up this test's records from the quarantine JSON.
    try:
        data = json.loads(output_file.read_text(encoding="utf-8"))
        data = [
            item for item in data
            if not (
                item.get("source_file") == "pytest_quarantine_batch.parquet"
                and item.get("record", {}).get("order_id") == "ORD401"
            )
        ]
        output_file.write_text(json.dumps(data, indent=4), encoding="utf-8")
    finally:
        pass


def test_repeated_rejected_records_are_not_duplicated():
    orders = [
        {"order_id": "ORD501", "amount": -100, "status": "Pending"}
    ]

    _, invalid_orders = separate_valid_and_invalid_orders(orders)

    first_result = quarantine_records(
        invalid_orders,
        "pytest_duplicate_batch.parquet"
    )

    second_result = quarantine_records(
        invalid_orders,
        "pytest_duplicate_batch.parquet"
    )

    assert first_result.exists()
    assert second_result.exists()

    data = json.loads(first_result.read_text(encoding="utf-8"))

    matching_records = [
        item for item in data
        if item.get("source_file") == "pytest_duplicate_batch.parquet"
        and item.get("record", {}).get("order_id") == "ORD501"
    ]

    assert len(matching_records) == 1

    # Remove only the test records.
    data = [
        item for item in data
        if not (
            item.get("source_file") == "pytest_duplicate_batch.parquet"
            and item.get("record", {}).get("order_id") == "ORD501"
        )
    ]

    first_result.write_text(json.dumps(data, indent=4), encoding="utf-8")
