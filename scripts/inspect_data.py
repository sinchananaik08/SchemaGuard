
from pathlib import Path
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[1]

files = [
    PROJECT_ROOT / "data/input/customers/customers_batch_001.parquet",
    PROJECT_ROOT / "data/input/orders/orders_batch_001.parquet"
]

for file_path in files:
    print("\nFile:", file_path.name)

    table = pq.read_table(file_path)

    print("\nSchema:")
    print(table.schema)

    print("\nNumber of rows:", table.num_rows)

    print("\nSample records:")
    print(table.to_pandas().head())


