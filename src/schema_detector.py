
from pathlib import Path
import pyarrow.parquet as pq
import yaml


# Find the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Location of our expected schema
SCHEMA_FILE = PROJECT_ROOT / "config" / "source_schema.yaml"


def load_expected_schema():
    """Load the expected schema from the YAML configuration."""

    with open(SCHEMA_FILE, "r", encoding="utf-8") as file:
        schema = yaml.safe_load(file)

    return schema


def read_incoming_schema(parquet_file):
    """Read the schema of an incoming Parquet file."""

    parquet_schema = pq.read_schema(parquet_file)

    incoming_schema = {}

    for field in parquet_schema:
        incoming_schema[field.name] = str(field.type)

    return incoming_schema


def read_incoming_nullability(parquet_file):
    """Read whether each incoming Parquet column allows null values."""

    parquet_schema = pq.read_schema(parquet_file)

    incoming_nullability = {}

    for field in parquet_schema:
        incoming_nullability[field.name] = field.nullable

    return incoming_nullability



def detect_schema_drift(incoming_schema, expected_schema, entity):
    """Compare incoming schema with expected schema."""

    expected_columns = expected_schema[entity]["columns"]

    expected_names = set(expected_columns.keys())
    incoming_names = set(incoming_schema.keys())

    added_columns = incoming_names - expected_names
    missing_columns = expected_names - incoming_names

    changed_types = {}

    for column in expected_names.intersection(incoming_names):

        expected_type = expected_columns[column]["type"]
        actual_type = incoming_schema[column]

        if not is_compatible_type(expected_type, actual_type):
            changed_types[column] = {
                "expected": expected_type,
                "actual": actual_type
            }

    return {
        "added_columns": sorted(added_columns),
        "missing_columns": sorted(missing_columns),
        "changed_types": changed_types
    }



def is_compatible_type(expected_type, actual_type):
    """Check whether the incoming physical type matches our logical type."""

    type_mapping = {
        "integer": ["int8", "int16", "int32","int64"],
        "bigint": ["int64"],
        "string": ["string", "large_string"],
        "double": ["double", "float"],
        "timestamp": [
            "timestamp[ms]",
            "timestamp[us]",
            "timestamp[ns]"
        ]
    }

    return actual_type in type_mapping.get(expected_type, [])

