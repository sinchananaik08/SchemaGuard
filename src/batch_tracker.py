
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone
import uuid

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BATCH_TRACKER_FILE = (
    PROJECT_ROOT / "database" / "processed_batches.json"
)


def load_processed_batches():
    if not BATCH_TRACKER_FILE.exists():
        return []

    with open(BATCH_TRACKER_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_file_hash(file_path):
    """Generate a SHA-256 fingerprint of a file."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def is_batch_processed(file_hash, batch_name=None):
    processed_batches = load_processed_batches()

    for batch in processed_batches:
        if not isinstance(batch, dict):
            continue

        if batch.get("file_hash") == file_hash:
            return True

        # Support older entries that have no saved hash
        if (
            batch_name
            and batch.get("batch_name") == batch_name
            and batch.get("file_hash") is None
        ):
            batch["file_hash"] = file_hash

            with open(BATCH_TRACKER_FILE, "w", encoding="utf-8") as file:
                json.dump(processed_batches, file, indent=4)

            return True

    return False

def mark_batch_as_processed(batch_name, file_hash):
    """Save the filename and content hash of a processed batch."""

    processed_batches = load_processed_batches()

    if not any(
        batch.get("file_hash") == file_hash
        for batch in processed_batches
        if isinstance(batch, dict)
    ):
        processed_batches.append({
            "batch_name": batch_name,
            "file_hash": file_hash
        })

    BATCH_TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(BATCH_TRACKER_FILE, "w", encoding="utf-8") as file:
        json.dump(processed_batches, file, indent=4)

    print(f"Batch '{batch_name}' marked as processed.")


def create_run_id():
    return str(uuid.uuid4())


def get_current_timestamp():
    return datetime.now(timezone.utc).isoformat()


def create_audit_record(
    run_id,
    source_file,
    start_time,
    end_time,
    records_received,
    records_accepted,
    records_rejected,
    status,
    failure_reason=None,
    records_published=0,
    records_already_existing=0
):
    return {
        "run_id": run_id,
        "source_file": source_file,
        "start_time": start_time,
        "end_time": end_time,
        "records_received": records_received,
        "records_accepted": records_accepted,
        "records_rejected": records_rejected,
        "records_published": records_published,
        "records_already_existing": records_already_existing,
        "status": status,
        "failure_reason": failure_reason
    }