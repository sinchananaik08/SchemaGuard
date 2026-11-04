
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "data" / "input" / "orders"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Test records include normal, invalid, duplicate,
# missing, boundary, and late-arriving data.
orders = [
    # Valid record
    {
        "order_id": "ORD051",
        "customer_id": 101,
        "amount": 1000.0,
        "status": "Delivered",
        "order_date": "2026-11-02",
        "discount": 10.0,
        "test_case": "normal"
    },

    # Negative amount
    {
        "order_id": "ORD052",
        "customer_id": 102,
        "amount": -200.0,
        "status": "Pending",
        "order_date": "2026-11-02",
        "discount": 5.0,
        "test_case": "negative_amount"
    },

    # Valid record with zero discount
    {
        "order_id": "ORD053",
        "customer_id": 103,
        "amount": 500.0,
        "status": "Shipped",
        "order_date": "2026-11-02",
        "discount": 0.0,
        "test_case": "boundary_zero_discount"
    },

    # Duplicate order ID
    {
        "order_id": "ORD051",
        "customer_id": 104,
        "amount": 700.0,
        "status": "Pending",
        "order_date": "2026-11-03",
        "discount": 5.0,
        "test_case": "duplicate_order_id"
    },

    # Missing amount
    {
        "order_id": "ORD054",
        "customer_id": 101,
        "amount": None,
        "status": "Pending",
        "order_date": "2026-11-03",
        "discount": 5.0,
        "test_case": "missing_amount"
    },

    # Invalid status
    {
        "order_id": "ORD055",
        "customer_id": 102,
        "amount": 800.0,
        "status": "Processing",
        "order_date": "2026-11-03",
        "discount": 5.0,
        "test_case": "invalid_status"
    },

    # Invalid customer reference
    {
        "order_id": "ORD056",
        "customer_id": 9999,
        "amount": 900.0,
        "status": "Shipped",
        "order_date": "2026-11-03",
        "discount": 10.0,
        "test_case": "invalid_customer_reference"
    },

    # Missing order ID
    {
        "order_id": None,
        "customer_id": 103,
        "amount": 400.0,
        "status": "Delivered",
        "order_date": "2026-11-03",
        "discount": 0.0,
        "test_case": "missing_order_id"
    },

    # Discount at maximum allowed boundary
    {
        "order_id": "ORD057",
        "customer_id": 104,
        "amount": 1000.0,
        "status": "Delivered",
        "order_date": "2026-11-03",
        "discount": 100.0,
        "test_case": "boundary_max_discount"
    },

    # Discount above allowed boundary
    {
        "order_id": "ORD058",
        "customer_id": 105,
        "amount": 1000.0,
        "status": "Delivered",
        "order_date": "2026-11-03",
        "discount": 120.0,
        "test_case": "discount_above_limit"
    },

    # Late-arriving record with an older event date
    {
        "order_id": "ORD059",
        "customer_id": 101,
        "amount": 650.0,
        "status": "Shipped",
        "order_date": "2026-10-15",
        "discount": 5.0,
        "test_case": "late_arriving_record"
    },

    # Another out-of-order record
    {
        "order_id": "ORD060",
        "customer_id": 102,
        "amount": 750.0,
        "status": "Pending",
        "order_date": "2026-10-10",
        "discount": 10.0,
        "test_case": "out_of_order_record"
    }
]

# Convert order dates to Parquet timestamps
order_dates = pa.array(
    [
        datetime.fromisoformat(order["order_date"])
        for order in orders
    ],
    type=pa.timestamp("ms")
)

table = pa.Table.from_pylist(orders)

table = table.set_column(
    table.schema.get_field_index("order_date"),
    "order_date",
    order_dates
)

output_file = OUTPUT_DIR / "orders_edge_cases.parquet"

pq.write_table(table, output_file)

print("Synthetic edge-case dataset generated successfully!")
print("Total records:", len(orders))
print("Output:", output_file)
print("\nTest cases included:")

for order in orders:
    print("-", order["test_case"])
