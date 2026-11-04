
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_quality import (
    validate_order_amount,
    validate_order_status,
    validate_order_id,
    find_duplicate_order_ids,
    validate_order_record,
    separate_valid_and_invalid_orders,
    validate_customer_reference,
)


def test_valid_order_amount():
    assert validate_order_amount(500)[0] is True


def test_negative_order_amount():
    assert validate_order_amount(-200)[0] is False


def test_missing_order_amount():
    assert validate_order_amount(None)[0] is False


def test_zero_order_amount():
    assert validate_order_amount(0)[0] is True


def test_valid_order_status():
    assert validate_order_status("Shipped")[0] is True


def test_invalid_order_status():
    assert validate_order_status("Processing")[0] is False


def test_missing_order_status():
    assert validate_order_status(None)[0] is False


def test_valid_order_id():
    assert validate_order_id("ORD001")[0] is True


def test_missing_order_id():
    assert validate_order_id(None)[0] is False


def test_empty_order_id():
    assert validate_order_id("")[0] is False


def test_duplicate_order_ids():
    duplicates = find_duplicate_order_ids([
        "ORD001", "ORD002", "ORD003",
        "ORD001", "ORD004", "ORD002"
    ])
    assert duplicates == {"ORD001", "ORD002"}


def test_valid_order_record():
    order = {
        "order_id": "ORD010",
        "amount": 500,
        "status": "Shipped"
    }
    result = validate_order_record(order)
    assert result["status"] == "ACCEPTED"
    assert result["errors"] == []


def test_invalid_order_record():
    order = {
        "order_id": "ORD011",
        "amount": -200,
        "status": "Processing"
    }
    result = validate_order_record(order)
    assert result["status"] == "REJECTED"
    assert len(result["errors"]) == 2


def test_separate_valid_and_invalid_orders():
    orders = [
        {"order_id": "ORD101", "customer_id": 101, "amount": 500, "status": "Shipped"},
        {"order_id": "ORD102", "customer_id": 102, "amount": -200, "status": "Pending"},
        {"order_id": "ORD103", "customer_id": 103, "amount": 300, "status": "Processing"},
        {"order_id": "ORD104", "customer_id": 999, "amount": 700, "status": "Delivered"},
    ]

    customer_ids = {101, 102, 103, 104, 105}

    valid_orders, invalid_orders = separate_valid_and_invalid_orders(
        orders, customer_ids
    )

    assert len(valid_orders) == 1
    assert len(invalid_orders) == 3
    assert len(valid_orders) + len(invalid_orders) == len(orders)


def test_duplicate_order_inside_batch():
    orders = [
        {"order_id": "ORD201", "amount": 500, "status": "Shipped"},
        {"order_id": "ORD202", "amount": 300, "status": "Pending"},
        {"order_id": "ORD201", "amount": 700, "status": "Delivered"},
    ]

    valid_orders, invalid_orders = separate_valid_and_invalid_orders(orders)

    assert len(valid_orders) == 2
    assert len(invalid_orders) == 1


def test_existing_customer_reference():
    order = {"order_id": "ORD401", "customer_id": 101}
    assert validate_customer_reference(order, {101, 102, 103})[0] is True


def test_non_existing_customer_reference():
    order = {"order_id": "ORD402", "customer_id": 999}
    assert validate_customer_reference(order, {101, 102, 103})[0] is False


def test_missing_customer_reference():
    order = {"order_id": "ORD403", "customer_id": None}
    assert validate_customer_reference(order, {101, 102, 103})[0] is False
