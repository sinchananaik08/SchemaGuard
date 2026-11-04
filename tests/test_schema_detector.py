
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.schema_detector import (
    load_expected_schema,
    read_incoming_schema,
    detect_schema_drift
)


def test_customer_schema_has_no_drift():
    expected_schema = load_expected_schema()

    file_path = (
        PROJECT_ROOT
        / "data"
        / "input"
        / "customers"
        / "customers_batch_001.parquet"
    )

    incoming_schema = read_incoming_schema(file_path)

    result = detect_schema_drift(
        incoming_schema,
        expected_schema,
        "customers"
    )

    assert result["added_columns"] == []
    assert result["missing_columns"] == []
    assert result["changed_types"] == {}


def test_order_schema_has_no_drift():
    expected_schema = load_expected_schema()

    file_path = (
        PROJECT_ROOT
        / "data"
        / "input"
        / "orders"
        / "orders_batch_001.parquet"
    )

    incoming_schema = read_incoming_schema(file_path)

    result = detect_schema_drift(
        incoming_schema,
        expected_schema,
        "orders"
    )

    assert result["added_columns"] == []
    assert result["missing_columns"] == []
    assert result["changed_types"] == {}


def test_schema_detector_identifies_added_column():
    expected_schema = load_expected_schema()

    incoming_schema = {
        "order_id": "string",
        "customer_id": "int64",
        "order_date": "timestamp[ms]",
        "amount": "double",
        "status": "string",
        "discount": "double",
        "payment_method": "string"
    }

    result = detect_schema_drift(
        incoming_schema,
        expected_schema,
        "orders"
    )

    assert result["added_columns"] == ["payment_method"]
