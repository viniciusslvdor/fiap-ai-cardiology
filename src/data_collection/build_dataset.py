"""Combines the 4 UCI Heart Disease databases into a single CSV for CardioIA."""
import csv
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "heart-disease"
OUT_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "cardioai_numeric_dataset.csv"

COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num",
]

FRIENDLY_NAMES = {
    "age": "age",
    "sex": "sex",
    "cp": "chest_pain_type",
    "trestbps": "resting_blood_pressure",
    "chol": "serum_cholesterol",
    "fbs": "high_fasting_blood_sugar",
    "restecg": "resting_ecg",
    "thalach": "max_heart_rate",
    "exang": "exercise_induced_angina",
    "oldpeak": "exercise_st_depression",
    "slope": "st_slope_peak_exercise",
    "ca": "num_major_vessels",
    "thal": "thalassemia",
    "num": "diagnosis_disease_0to4",
}

SOURCES = {
    "processed.cleveland.data": "Cleveland Clinic Foundation (USA)",
    "processed.hungarian.data": "Hungarian Institute of Cardiology, Budapest",
    "processed.switzerland.data": "University Hospital, Zurich/Basel (Switzerland)",
    "processed.va.data": "V.A. Medical Center, Long Beach (USA)",
}


def clean_row(row):
    return ["" if v.strip() == "?" else v for v in row]


def main():
    header = [FRIENDLY_NAMES[c] for c in COLUMNS] + ["sex_label", "disease_presence", "source_institution"]
    rows_out = []

    for filename, source_label in SOURCES.items():
        path = RAW_DIR / filename
        with open(path, newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 14:
                    continue
                row = clean_row(row)
                sex_val = row[1]
                sex_label = "M" if sex_val == "1.0" else ("F" if sex_val == "0.0" else "")
                num_val = row[13].strip()
                try:
                    disease_presence = "1" if num_val and float(num_val) > 0 else ("0" if num_val else "")
                except ValueError:
                    disease_presence = ""
                rows_out.append(row + [sex_label, disease_presence, source_label])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows_out)

    print(f"Rows written: {len(rows_out)}")
    print(f"File generated at: {OUT_PATH}")


if __name__ == "__main__":
    main()
