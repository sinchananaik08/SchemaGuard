
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_FILE = DATABASE_DIR / "schemaguard.duckdb"


def create_target_table():
    connection = duckdb.connect(str(DATABASE_FILE))

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id VARCHAR PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                order_date TIMESTAMP NOT NULL,
                amount DOUBLE NOT NULL,
                status VARCHAR NOT NULL,
                discount DOUBLE,
                payment_method VARCHAR,
                amount_after_discount DOUBLE
            )
        """)

        connection.execute("""
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS amount_after_discount DOUBLE
        """)

    finally:
        connection.close()

    print("Target orders table is ready.")


def load_valid_orders(valid_orders):
    if not valid_orders:
        print("No valid orders to publish.")
        return 0

    create_target_table()

    connection = duckdb.connect(str(DATABASE_FILE))
    inserted_count = 0

    try:
        connection.execute("BEGIN TRANSACTION")

        insert_query = """
            INSERT INTO orders (
                order_id,
                customer_id,
                order_date,
                amount,
                status,
                discount,
                payment_method,
                amount_after_discount
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (order_id) DO NOTHING
        """

        batch_size = 1000

        for start in range(0, len(valid_orders), batch_size):
            batch = valid_orders[start:start + batch_size]

            values = [
                (
                    order.get("order_id"),
                    order.get("customer_id"),
                    order.get("order_date"),
                    order.get("amount"),
                    order.get("status"),
                    order.get("discount"),
                    order.get("payment_method"),
                    order.get("amount_after_discount")
                )
                for order in batch
            ]

            order_ids = list(set(value[0] for value in values))

            placeholders = ", ".join(["?"] * len(order_ids))

            existing_ids = connection.execute(
                f"""
                SELECT order_id
                FROM orders
                WHERE order_id IN ({placeholders})
                """,
                order_ids
            ).fetchall()

            existing_ids = {row[0] for row in existing_ids}

            new_ids = set(order_ids) - existing_ids

            connection.executemany(insert_query, values)

            inserted_count += len(new_ids)

        connection.execute("COMMIT")

        print("Database transaction committed successfully.")
        print("Valid orders considered:", len(valid_orders))
        print("New orders inserted:", inserted_count)

        return inserted_count

    except Exception:
        connection.execute("ROLLBACK")
        print("Database transaction rolled back.")
        raise

    finally:
        connection.close()


def verify_orders_in_database(expected_orders):
    """Verify published order IDs and values against DuckDB."""

    if not expected_orders:
        print("No orders supplied for database verification.")
        return True

    connection = duckdb.connect(str(DATABASE_FILE))

    try:
        all_verified = True

        print("\nSOURCE-TO-TARGET VERIFICATION")
        print("-----------------------------")
        print("Expected orders:", len(expected_orders))

        for expected in expected_orders:

            result = connection.execute(
                """
                SELECT
                    customer_id,
                    amount,
                    discount,
                    status,
                    amount_after_discount
                FROM orders
                WHERE order_id = ?
                """,
                [expected["order_id"]]
            ).fetchone()

            if result is None:
                print("Missing order:", expected["order_id"])
                all_verified = False
                continue

            actual_customer_id, actual_amount, actual_discount, actual_status, actual_final_amount = result

            expected_discount = expected.get("discount")
            if expected_discount is None:
                expected_discount = 0.0

            expected_final_amount = expected.get("amount_after_discount")

            values_match = (
                actual_customer_id == expected.get("customer_id")
                and abs(actual_amount - expected["amount"]) <= 0.000001
                and (
                    actual_discount is None
                    or abs(actual_discount - expected_discount) <= 0.000001
                )
                and actual_status == expected.get("status")
                and abs(actual_final_amount - expected_final_amount) <= 0.000001
            )

            if values_match:
                print("Verified:", expected["order_id"])
            else:
                print("Mismatch:", expected["order_id"])
                print("Expected:", expected)
                print("Actual:", result)
                all_verified = False

        print("Orders checked:", len(expected_orders))

        if all_verified:
            print("Source-to-target verification: PASSED")
        else:
            print("Source-to-target verification: FAILED")

        return all_verified

    finally:
        connection.close()
