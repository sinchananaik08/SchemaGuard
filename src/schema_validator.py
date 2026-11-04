
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RULES_FILE = PROJECT_ROOT / "config" / "evolution_rules.yaml"
SCHEMA_FILE = PROJECT_ROOT / "config" / "source_schema.yaml"


def load_evolution_rules():
    """Load approved and rejected schema evolution rules."""

    with open(RULES_FILE, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_expected_schema():
    """Load the original expected schema."""

    with open(SCHEMA_FILE, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def validate_schema_changes(
    drift_result,
    entity,
    incoming_schema,
    incoming_nullability=None
):
    """Decide whether detected schema changes should be accepted."""

    rules = load_evolution_rules()
    expected_schema = load_expected_schema()

    entity_columns = expected_schema[entity]["columns"]

    # 1. Check newly added columns
    approved_columns = (
        rules["approved_changes"]["add_nullable_column"]
        ["columns"].get(entity, {})
    )

    for column in drift_result["added_columns"]:

        # Check whether the new column is approved
        if column not in approved_columns:
            return {
                "status": "REJECTED",
                "reason": f"New column '{column}' is not approved."
            }

        # Read approved column configuration
        column_rules = approved_columns[column]

        expected_type = column_rules["type"]
        actual_type = incoming_schema[column]

        # Check YAML nullable permission
        if not column_rules["nullable"]:
            return {
                "status": "REJECTED",
                "reason": f"New column '{column}' must be nullable."
            }

        # Check actual Parquet nullability
        if incoming_nullability is not None:
            if not incoming_nullability.get(column, False):
                return {
                    "status": "REJECTED",
                    "reason": (
                        f"Incoming column '{column}' is not nullable."
                    )
                }

        # Check whether the data type matches
        if actual_type != expected_type:
            return {
                "status": "REJECTED",
                "reason": (
                    f"New column '{column}' has type '{actual_type}', "
                    f"but '{expected_type}' was expected."
                )
            }

    # 2. Check missing columns
    for column in drift_result["missing_columns"]:

        if not entity_columns[column].get("nullable", False):
            return {
                "status": "REJECTED",
                "reason": f"Required column '{column}' is missing."
            }

    # 3. Check changed data types
    for column, type_change in drift_result["changed_types"].items():

        widening_rule = rules["approved_changes"]["integer_widening"]

        if (
            widening_rule["allowed"]
            and type_change["expected"] == widening_rule["from"]
            and type_change["actual"] == widening_rule["to"]
        ):
            continue

        return {
            "status": "REJECTED",
            "reason": (
                f"Incompatible type change in '{column}': "
                f"expected {type_change['expected']}, "
                f"received {type_change['actual']}."
            )
        }

    return {
        "status": "ACCEPTED",
        "reason": "All detected schema changes are approved."
    }
