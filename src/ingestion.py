from pathlib import Path
import pyarrow.parquet as pq


def read_parquet_file(file_path):
    """
    Read records from a Parquet file.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path}"
        )

    if file_path.stat().st_size == 0:
        raise ValueError("Input Parquet file is empty.")

    table = pq.read_table(file_path)

    records = table.to_pylist()

    print("Parquet file read successfully!")
    print("File:", file_path.name)
    print("Number of records:", len(records))

    return records