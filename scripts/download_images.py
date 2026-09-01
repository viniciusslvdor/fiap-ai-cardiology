"""Downloads a sample of chest X-ray images from the public
ieee8023/covid-chestxray-dataset for CardioIA Part 3."""
import csv
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
METADATA_URL = "https://raw.githubusercontent.com/ieee8023/covid-chestxray-dataset/master/metadata.csv"
METADATA = BASE / "data" / "raw" / "covid_chestxray_metadata.csv"
OUT_DIR = BASE / "assets" / "images"
OUT_METADATA = OUT_DIR / "images_metadata.csv"
RAW_BASE = "https://raw.githubusercontent.com/ieee8023/covid-chestxray-dataset/master/images/"

VALID_VIEWS = {"PA", "AP", "AP Supine", "AP erect"}
VALID_EXT = {".jpg", ".jpeg", ".png"}
TARGET_COUNT = 150


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    METADATA.parent.mkdir(parents=True, exist_ok=True)
    if not METADATA.exists():
        urllib.request.urlretrieve(METADATA_URL, METADATA)

    rows = []
    seen_filenames = set()
    with open(METADATA, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("modality") != "X-ray":
                continue
            if row.get("view") not in VALID_VIEWS:
                continue
            filename = row.get("filename", "").strip()
            if not filename:
                continue
            ext = Path(filename).suffix.lower()
            if ext not in VALID_EXT:
                continue
            if filename in seen_filenames:
                continue
            seen_filenames.add(filename)
            rows.append(row)

    print(f"Candidates found: {len(rows)}")
    rows = rows[:TARGET_COUNT]

    downloaded = []
    for i, row in enumerate(rows, 1):
        filename = row["filename"]
        ext = Path(filename).suffix.lower()
        new_name = f"cxr_{i:03d}{ext}"
        url = RAW_BASE + urllib.parse.quote(filename)
        dest = OUT_DIR / new_name
        try:
            urllib.request.urlretrieve(url, dest)
            if dest.stat().st_size < 1000:
                dest.unlink()
                print(f"[skipped, too small] {filename}")
                continue
        except Exception as e:
            print(f"[error] {filename}: {e}")
            continue
        downloaded.append({
            "filename": new_name,
            "original_filename": filename,
            "finding": row.get("finding", ""),
            "view": row.get("view", ""),
            "sex": row.get("sex", ""),
            "age": row.get("age", ""),
            "license": row.get("license", ""),
            "doi": row.get("doi", ""),
        })
        if i % 20 == 0:
            print(f"{i}/{len(rows)} downloaded...")

    with open(OUT_METADATA, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(downloaded[0].keys()))
        writer.writeheader()
        writer.writerows(downloaded)

    print(f"Total successfully downloaded: {len(downloaded)}")
    print(f"Metadata saved at: {OUT_METADATA}")


if __name__ == "__main__":
    main()
