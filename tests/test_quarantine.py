
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.quarantine import quarantine_file


def test_quarantine_file():
    # Create a temporary sample file for testing
    test_file = PROJECT_ROOT / "data" / "test_quarantine_sample.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Sample invalid data", encoding="utf-8")

    try:
        result = quarantine_file(
            test_file,
            "Unapproved schema change detected"
        )

        assert result["status"] == "QUARANTINED"
        assert result["reason"] == "Unapproved schema change detected"
        assert Path(result["file"]).exists()

    finally:
        # Remove the temporary quarantined test file
        quarantined_file = (
            PROJECT_ROOT
            / "data"
            / "quarantine"
            / test_file.name
        )

        if quarantined_file.exists():
            quarantined_file.unlink()
