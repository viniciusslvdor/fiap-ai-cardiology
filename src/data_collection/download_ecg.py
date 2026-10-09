"""
CardioIA | Download of the "ECG Heartbeat Categorization" dataset (Kaggle).

Dataset: https://www.kaggle.com/datasets/shayanfazeli/heartbeat  (~100 MB zipped, ~580 MB extracted)
Files copied to data/raw/ecg/:
    mitbih_train.csv, mitbih_test.csv    -> MIT-BIH Arrhythmia (5 heartbeat classes)
    ptbdb_normal.csv, ptbdb_abnormal.csv -> PTB Diagnostic ECG (normal x abnormal)

Usage:
    uv run python src/data_collection/download_ecg.py

Requires the `kagglehub` package (installed by `uv sync`). The dataset is public; the download usually
works without logging in. If you get a credentials error, an invalid ~/.kaggle/kaggle.json is usually the
cause: fix it with a valid token or download the ZIP manually from Kaggle into data/raw/ecg/.
The CSVs must NOT be pushed to GitHub (they are already in .gitignore).
"""

import shutil
from pathlib import Path

DATASET = "shayanfazeli/heartbeat"
FILES = ["mitbih_train.csv", "mitbih_test.csv", "ptbdb_normal.csv", "ptbdb_abnormal.csv"]
DESTINATION = Path(__file__).resolve().parents[2] / "data" / "raw" / "ecg"


def main() -> None:
    missing = [name for name in FILES if not (DESTINATION / name).exists()]
    if not missing:
        print(f"All files are already in {DESTINATION}")
        return

    import kagglehub

    print(f"Downloading {DATASET} via kagglehub...")
    source = Path(kagglehub.dataset_download(DATASET))
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for name in missing:
        shutil.copy2(source / name, DESTINATION / name)
        print(f"  copied: {name} ({(DESTINATION / name).stat().st_size / 1e6:.0f} MB)")
    print(f"Done. Files in: {DESTINATION}")


if __name__ == "__main__":
    main()
