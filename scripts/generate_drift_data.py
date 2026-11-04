
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "data" / "input" / "orders"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create orders with one approved additional column
orders = {
    "order_id": ["ORD041", "ORD042", "ORD043"],
    "customer_id": [101, 102, 103],
    "order_date": [
        "2026-11-01",
        "2026-11-01",
        "2026-11-02"
    ],
    "amount": [1200.0, 2500.0, 900.0],
    "status": ["Delivered", "Pending", "Shipped"],
    "discount": [5.0, 10.0, None],
    "delivery_address": ["Bengaluru", "Mysuru", "Mandya"]
}

orders["order_date"] = pa.array(
    [
        datetime.fromisoformat(date)
        for date in orders["order_date"]
    ],
    type=pa.timestamp("ms")
)

table = pa.table(orders)

output_file = OUTPUT_DIR / "orders_quarantine_test.parquet"

pq.write_table(table, output_file)

print("Approved schema drift sample generated!")
print("New approved column: payment_method")
print("Unapproved columns: None")
print("Number of records:", table.num_rows)
print("Output:", output_file)
