
from pathlib import Path
import sys
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_data_quality_pipeline


def test_pipeline_returns_valid_and_invalid_orders():
    batch_name = "test_pipeline_batch.parquet"
    batch_file = (
        PROJECT_ROOT / "data" / "input" / "orders" / batch_name
    )

    batch_file.parent.mkdir(parents=True, exist_ok=True)

    valid_order = {
        "order_id": "TEST001",
        "customer_id": 101,
        "amount": 500,
        "status": "Shipped"
    }

    invalid_order = {
        "order_id": "TEST002",
        "customer_id": 101,
        "amount": -200,
        "status": "Pending"
    }

    # Create a placeholder because the pipeline checks file existence.
    batch_file.write_bytes(b"test placeholder")

    try:
        with patch("src.pipeline.is_batch_processed", return_value=False), \
             patch(
                 "src.pipeline.read_parquet_file",
                 side_effect=[
                     [{"customer_id": 101}],
                     [valid_order, invalid_order]
                 ]
             ), \
             patch(
                 "src.pipeline.read_incoming_schema",
                 return_value={
                     "order_id": "string",
                     "customer_id": "int64",
                     "order_date": "timestamp[ms]",
                     "amount": "double",
                     "status": "string",
                     "discount": "double"
                 }
             ), \
             patch("src.pipeline.read_incoming_nullability", return_value={}), \
             patch(
                 "src.pipeline.detect_schema_drift",
                 return_value={
                     "added_columns": [],
                     "missing_columns": [],
                     "changed_types": {}
                 }
             ), \
             patch(
                 "src.pipeline.validate_schema_changes",
                 return_value={
                     "status": "ACCEPTED",
                     "reason": "Schema is compatible."
                 }
             ), \
             patch("src.pipeline.quarantine_records"), \
             patch("src.pipeline.load_valid_orders", return_value=1), \
             patch("src.pipeline.verify_orders_in_database", return_value=True), \
             patch("src.pipeline.mark_batch_as_processed"), \
             patch("src.pipeline.create_run_id", return_value="TEST_RUN_001"):

            valid_orders, invalid_orders = run_data_quality_pipeline(batch_name)

        assert len(valid_orders) == 1
        assert len(invalid_orders) == 1
        assert valid_orders[0]["order_id"] == "TEST001"
        assert invalid_orders[0]["record"]["order_id"] == "TEST002"

    finally:
        if batch_file.exists():
            batch_file.unlink()
