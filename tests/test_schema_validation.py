
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.schema_detector import load_expected_schema, detect_schema_drift
from src.schema_validator import validate_schema_changes


expected_schema = load_expected_schema()


def run_validation(incoming_schema, incoming_nullability=None):
    drift = detect_schema_drift(
        incoming_schema,
        expected_schema,
        "orders"
    )

    return validate_schema_changes(
        drift,
        "orders",
        incoming_schema,
        incoming_nullability
    )


def test_approved_new_nullable_column():
    incoming_schema = {
        "order_id": "string",
        "customer_id": "int64",
        "order_date": "timestamp[ms]",
        "amount": "double",
        "status": "string",
        "discount": "double",
        "payment_method": "string"
    }

    decision = run_validation(incoming_schema, {"payment_method": True})
    assert decision["status"] == "ACCEPTED"


def test_unapproved_new_column():
    incoming_schema = {
        "order_id": "string",
        "customer_id": "int64",
        "order_date": "timestamp[ms]",
        "amount": "double",
        "status": "string",
        "discount": "double",
        "delivery_address": "string"
    }

    decision = run_validation(incoming_schema, {"delivery_address": True})
    assert decision["status"] == "REJECTED"


def test_missing_required_column():
    incoming_schema = {
        "order_id": "string",
        "customer_id": "int64",
        "order_date": "timestamp[ms]",
        "status": "string",
        "discount": "double"
    }

    decision = run_validation(incoming_schema)
    assert decision["status"] == "REJECTED"


def test_missing_optional_column():
    incoming_schema = {
        "order_id": "string",
        "customer_id": "int64",
        "order_date": "timestamp[ms]",
        "amount": "double",
        "status": "string"
    }

    decision = run_validation(incoming_schema)
    assert decision["status"] == "ACCEPTED"


def test_incompatible_data_type():
    incoming_schema = {
        "order_id": "string",
        "customer_id": "int64",
        "order_date": "timestamp[ms]",
        "amount": "string",
        "status": "string",
        "discount": "double"
    }

    decision = run_validation(incoming_schema)
    assert decision["status"] == "REJECTED"


def test_approved_integer_to_bigint_widening():
    widening_drift = {
        "added_columns": [],
        "missing_columns": [],
        "changed_types": {
            "customer_id": {
                "expected": "integer",
                "actual": "bigint"
            }
        }
    }

    widening_schema = {
        "order_id": "string",
        "customer_id": "bigint",
        "order_date": "timestamp[ms]",
        "amount": "double",
        "status": "string",
        "discount": "double"
    }

    decision = validate_schema_changes(
        widening_drift,
        "orders",
        widening_schema
    )

    assert decision["status"] == "ACCEPTED"


def test_approved_column_marked_non_nullable():
    incoming_schema = {
        "order_id": "string",
        "customer_id": "int64",
        "order_date": "timestamp[ms]",
        "amount": "double",
        "status": "string",
        "discount": "double",
        "payment_method": "string"
    }

    decision = run_validation(
        incoming_schema,
        {"payment_method": False}
    )

    assert decision["status"] == "REJECTED"
