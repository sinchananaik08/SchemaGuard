from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "data" / "input" / "orders"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create orders where amount is incorrectly stored as text
orders = {
    "order_id": ["ORD031", "ORD032"],
    "customer_id": [101, 102],
    "order_date": [
        "2026-11-01",
        "2026-11-02"
    ],
    "amount": ["500 rupees", "300 rupees"],
    "status": ["Shipped", "Pending"],
    "discount": [5.0, 10.0]
}

orders["order_date"] = pa.array(
    [datetime.fromisoformat(date) for date in orders["order_date"]],
    type=pa.timestamp("ms")
)

table = pa.table(orders)

output_file = OUTPUT_DIR / "orders_wrong_type_test.parquet"

pq.write_table(table, output_file)

print("Wrong data type test batch generated!")
print("Expected amount type: double")
print("Actual amount type: string")
print("Output:", output_file)