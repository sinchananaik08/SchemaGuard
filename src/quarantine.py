
from pathlib import Path
import json
import shutil
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]

QUARANTINE_DIR = PROJECT_ROOT / "data" / "quarantine"


def quarantine_file(file_path, reason):
    """Move a schema-rejected file into quarantine."""

    file_path = Path(file_path)

    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    destination = QUARANTINE_DIR / file_path.name

    shutil.move(str(file_path), str(destination))

    result = {
        "status": "QUARANTINED",
        "reason": reason,
        "file": str(destination),
        "quarantined_at": datetime.now(timezone.utc).isoformat()
    }

    print("File moved to quarantine!")
    print("Reason:", reason)

    return result


def quarantine_records(invalid_records, source_file):
    """Save rejected records without creating duplicates."""

    rejected_records_dir = (
        QUARANTINE_DIR / "rejected_records"
    )

    rejected_records_dir.mkdir(parents=True, exist_ok=True)

    output_file = rejected_records_dir / "rejected_orders.json"

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as file:
            existing_records = json.load(file)
    else:
        existing_records = []

    existing_keys = {
        (
            record.get("source_file"),
            str(record.get("record", {}).get("order_id"))
        )
        for record in existing_records
    }

    new_records = []

    for invalid_record in invalid_records:

        record = invalid_record.get("record", {})

        rejection_entry = {
            "source_file": source_file,
            "record": record,
            "errors": invalid_record.get("errors", []),
            "quarantined_at": datetime.now(timezone.utc).isoformat()
        }

        unique_key = (
            source_file,
            str(record.get("order_id"))
        )

        if unique_key not in existing_keys:
            new_records.append(rejection_entry)
            existing_keys.add(unique_key)

    existing_records.extend(new_records)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(existing_records, file, indent=4, default=str)

    print("Rejected records saved successfully!")
    print("New rejected records:", len(new_records))
    print("Total rejected records:", len(existing_records))

    return output_file
