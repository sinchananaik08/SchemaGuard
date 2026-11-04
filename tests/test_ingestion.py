
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion import read_parquet_file


def test_read_orders_parquet():
    file_path = (
        PROJECT_ROOT
        / "data"
        / "input"
        / "orders"
        / "orders_batch_001.parquet"
    )

    orders = read_parquet_file(file_path)

    assert len(orders) == 10
    assert orders[0]["order_id"] == "ORD001"


def test_read_customers_parquet():
    customer_file = (
        PROJECT_ROOT
        / "data"
        / "input"
        / "customers"
        / "customers_batch_001.parquet"
    )

    customers = read_parquet_file(customer_file)

    assert len(customers) == 5
    assert customers[0]["customer_id"] == 101


def test_missing_parquet_file():
    missing_file = (
        PROJECT_ROOT
        / "data"
        / "input"
        / "orders"
        / "file_that_does_not_exist.parquet"
    )

    try:
        read_parquet_file(missing_file)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        assert True
