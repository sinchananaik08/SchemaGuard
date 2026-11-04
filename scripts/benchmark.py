
from pathlib import Path
import time
import tempfile
import duckdb
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ORDERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "input"
    / "orders"
    / "orders_large.parquet"
)

BATCH_SIZE = 500
TEST_RECORD_COUNT = 10000


def benchmark_parquet_read():
    """Measure Parquet reading performance."""

    if not ORDERS_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {ORDERS_FILE}")

    start = time.perf_counter()
    table = pq.read_table(ORDERS_FILE)
    elapsed = time.perf_counter() - start

    total_rows = table.num_rows

    print("\nPARQUET READING BENCHMARK")
    print("-------------------------")
    print("Dataset:", ORDERS_FILE.name)
    print("Total rows:", total_rows)
    print(f"Reading time: {elapsed:.4f} seconds")
    print(f"Reading speed: {total_rows / elapsed:,.0f} rows/second")

    return table.to_pylist()


def create_table(connection):
    connection.execute("""
        CREATE TABLE orders (
            order_id VARCHAR PRIMARY KEY,
            customer_id INTEGER,
            order_date TIMESTAMP,
            amount DOUBLE,
            status VARCHAR,
            discount DOUBLE
        )
    """)


def prepare_values(records):
    return [
        (
            order["order_id"],
            order["customer_id"],
            order["order_date"],
            order["amount"],
            order["status"],
            order["discount"]
        )
        for order in records
    ]


def benchmark_individual_insert(records, database_file):
    connection = duckdb.connect(str(database_file))

    try:
        create_table(connection)

        query = "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)"
        start = time.perf_counter()

        connection.execute("BEGIN TRANSACTION")

        for values in prepare_values(records):
            connection.execute(query, values)

        connection.execute("COMMIT")
        elapsed = time.perf_counter() - start

        count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        return elapsed, count

    finally:
        connection.close()


def benchmark_batch_insert(records, database_file):
    connection = duckdb.connect(str(database_file))

    try:
        create_table(connection)

        query = "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)"
        values = prepare_values(records)

        start = time.perf_counter()
        connection.execute("BEGIN TRANSACTION")

        for position in range(0, len(values), BATCH_SIZE):
            batch = values[position:position + BATCH_SIZE]
            connection.executemany(query, batch)

        connection.execute("COMMIT")
        elapsed = time.perf_counter() - start

        count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        return elapsed, count

    finally:
        connection.close()


def benchmark_database_inserts(records):
    """Compare insertion methods using temporary databases."""

    records = records[:TEST_RECORD_COUNT]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        individual_time, individual_count = benchmark_individual_insert(
            records, temp_dir / "individual.duckdb"
        )

        batch_time, batch_count = benchmark_batch_insert(
            records, temp_dir / "batch.duckdb"
        )

    print("\nDATABASE INSERTION BENCHMARK")
    print("----------------------------")
    print("Records tested:", len(records))
    print("Batch size:", BATCH_SIZE)

    print(f"\nIndividual insertion time: {individual_time:.4f} seconds")
    print("Individual records inserted:", individual_count)

    print(f"\nBatch insertion time: {batch_time:.4f} seconds")
    print("Batch records inserted:", batch_count)

    if individual_count != len(records) or batch_count != len(records):
        raise RuntimeError("Insertion counts do not match.")

    if batch_time < individual_time:
        improvement = (
            (individual_time - batch_time) / individual_time
        ) * 100
        print(f"\nBatch insertion was {improvement:.2f}% faster.")
    else:
        print("\nBatch insertion did not show an improvement in this test.")


if __name__ == "__main__":
    print("Starting SchemaGuard performance benchmark...")

    orders = benchmark_parquet_read()
    benchmark_database_inserts(orders)

    print("\nPerformance benchmark completed.")
