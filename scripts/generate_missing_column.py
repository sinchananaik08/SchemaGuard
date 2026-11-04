from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "data" / "input" / "orders"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create orders without the required amount column
orders = {
    "order_id": ["ORD021", "ORD022"],
    "customer_id": [101, 102],
    "order_date": [
        "2026-11-01",
        "2026-11-02"
    ],
    "status": ["Shipped", "Pending"],
    "discount": [5.0, 10.0]
}

orders["order_date"] = pa.array(
    [datetime.fromisoformat(date) for date in orders["order_date"]],
    type=pa.timestamp("ms")
)

table = pa.table(orders)

output_file = OUTPUT_DIR / "orders_missing_column_test.parquet"

pq.write_table(table, output_file)

print("Missing-column test batch generated!")
print("Missing required column: amount")
print("Output:", output_file)