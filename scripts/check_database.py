
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_FILE = PROJECT_ROOT / "database" / "schemaguard.duckdb"

connection = duckdb.connect(str(DATABASE_FILE), read_only=True)

try:
    result = connection.execute("""
        SELECT
            order_id,
            amount,
            discount,
            amount_after_discount,
            payment_method
        FROM orders
        ORDER BY order_id
    """).fetchdf()

    print("Orders stored in the database:")
    print(result)

finally:
    connection.close()
