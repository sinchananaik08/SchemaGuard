
from pathlib import Path
import random
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timedelta

# Project folders
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CUSTOMER_DIR = PROJECT_ROOT / "data" / "input" / "customers"
ORDERS_DIR = PROJECT_ROOT / "data" / "input" / "orders"

CUSTOMER_DIR.mkdir(parents=True, exist_ok=True)
ORDERS_DIR.mkdir(parents=True, exist_ok=True)


def generate_customers():
    """Generate the original sample customer records."""

    customers = {
        "customer_id": [101, 102, 103, 104, 105],
        "customer_name": ["Ananya", "Rahul", "Priya", "Arjun", "Meera"],
        "email": [
            "ananya@example.com",
            "rahul@example.com",
            "priya@example.com",
            "arjun@example.com",
            "meera@example.com"
        ],
        "city": ["Bengaluru", "Mysuru", "Mandya", "Mangaluru", "Hassan"]
    }

    table = pa.table(customers)
    output_file = CUSTOMER_DIR / "customers_batch_001.parquet"
    pq.write_table(table, output_file)

    print(f"Sample customer data saved: {output_file}")


def generate_orders():
    """Generate the original sample order records."""

    orders = {
        "order_id": [
            "ORD001", "ORD002", "ORD003", "ORD004", "ORD005",
            "ORD006", "ORD007", "ORD008", "ORD009", "ORD010"
        ],
        "customer_id": [
            101, 102, 103, 104, 105,
            101, 102, 103, 104, 105
        ],
        "order_date": [
            "2026-10-20", "2026-10-21", "2026-10-22",
            "2026-10-23", "2026-10-24", "2026-10-25",
            "2026-10-26", "2026-10-27", "2026-10-28",
            "2026-10-29"
        ],
        "amount": [
            1500.0, 2500.0, 800.0, 1200.0, 3000.0,
            950.0, 1800.0, 2200.0, 750.0, 4000.0
        ],
        "status": [
            "Delivered", "Pending", "Shipped", "Delivered",
            "Cancelled", "Pending", "Shipped", "Delivered",
            "Pending", "Delivered"
        ],
        "discount": [
            10.0, 5.0, None, 0.0, 15.0,
            5.0, None, 10.0, 0.0, 20.0
        ]
    }

    orders["order_date"] = pa.array(
        [datetime.fromisoformat(date) for date in orders["order_date"]],
        type=pa.timestamp("ms")
    )

    table = pa.table(orders)
    output_file = ORDERS_DIR / "orders_batch_001.parquet"
    pq.write_table(table, output_file)

    print(f"Sample order data saved: {output_file}")


def generate_large_dataset(customer_count=5000, order_count=100000, seed=42):
    """Generate reproducible large customer and order datasets."""

    random.seed(seed)

    # Generate large customer dataset
    customer_ids = list(range(1001, 1001 + customer_count))

    customers = {
        "customer_id": customer_ids,
        "customer_name": [
            f"Customer_{i}" for i in range(1, customer_count + 1)
        ],
        "email": [
            f"customer{i}@example.com"
            for i in range(1, customer_count + 1)
        ],
        "city": [
            random.choice([
                "Bengaluru", "Mysuru", "Mandya",
                "Mangaluru", "Hassan"
            ])
            for _ in range(customer_count)
        ]
    }

    customer_table = pa.table(customers)
    customer_file = CUSTOMER_DIR / "customers_large.parquet"
    pq.write_table(customer_table, customer_file)

    # Generate large order dataset
    statuses = ["Pending", "Shipped", "Delivered", "Cancelled"]
    start_date = datetime(2026, 1, 1)

    orders = {
        "order_id": [
            f"LARGE_{i:06d}" for i in range(1, order_count + 1)
        ],
        "customer_id": [
            random.choice(customer_ids) for _ in range(order_count)
        ],
        "order_date": [
            start_date + timedelta(days=random.randint(0, 300))
            for _ in range(order_count)
        ],
        "amount": [
            round(random.uniform(0, 10000), 2)
            for _ in range(order_count)
        ],
        "status": [
            random.choice(statuses) for _ in range(order_count)
        ],
        "discount": [
            random.choice([None, 0.0, 5.0, 10.0, 15.0, 20.0])
            for _ in range(order_count)
        ]
    }

    order_table = pa.table(orders)
    order_file = ORDERS_DIR / "orders_large.parquet"
    pq.write_table(order_table, order_file)

    print("\nLarge dataset generated successfully!")
    print(f"Customers: {customer_count}")
    print(f"Orders: {order_count}")
    print(f"Customer file: {customer_file}")
    print(f"Order file: {order_file}")


if __name__ == "__main__":
    generate_customers()
    generate_orders()
    generate_large_dataset(
        customer_count=5000,
        order_count=100000,
        seed=42
    )

    print("\nAll sample data generation completed!")
