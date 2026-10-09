"""
CardioIA | Risk classifier (TF-IDF + Logistic Regression).

Script version of the same pipeline used in `notebooks/risk_classifier.ipynb`.

Usage:
    uv run python src/nlp/risk_classifier.py
    uv run python src/nlp/risk_classifier.py --sentence "I have strong chest pain and a cold sweat"

DISCLAIMER: academic project. The classification is text-based and does NOT replace medical triage or evaluation.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET = ROOT_DIR / "data" / "text" / "risk_dataset.csv"

RANDOM_STATE = 42
CLASSES = ["low risk", "high risk"]

NEW_SENTENCES = [
    "I have a strong chest pain that started half an hour ago and is not improving",
    "I have a mild pain in my legs after cycling on the weekend",
    "my husband fainted in the kitchen and is having trouble breathing",
    "I want to book a routine appointment for next month",
    "I am short of breath and my lips are turning purple",
    "I had a bit of a headache after spending too much time at the computer",
    "my heart is beating out of rhythm and I feel I am going to black out",
    "I have a runny nose and have been sneezing since yesterday",
    "I feel a tightness in my chest that goes to my neck and I am nauseous",
    "my blood pressure was fine at the last check and I feel energetic",
    "I am tired",
    "I have chest pain",
]


def load_dataset(path: Path = DATASET) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    df["sentence"] = df["sentence"].str.strip()
    df["label"] = df["label"].str.strip()
    return df.drop_duplicates(subset="sentence").reset_index(drop=True)


def build_pipeline() -> Pipeline:
    """TF-IDF (words and word pairs) + Logistic Regression."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )),
        ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)),
    ])


def train_and_evaluate(df: pd.DataFrame) -> Pipeline:
    X_train, X_test, y_train, y_test = train_test_split(
        df["sentence"], df["label"], test_size=0.2, random_state=RANDOM_STATE, stratify=df["label"]
    )
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    print(f"Train: {len(X_train)} sentences | Test: {len(X_test)} sentences\n")
    print(f"Accuracy (test): {accuracy_score(y_test, y_pred):.3f}\n")
    print("Classification report (test):")
    print(classification_report(y_test, y_pred, labels=CLASSES, digits=3, zero_division=0))
    print("Confusion matrix (rows = actual, columns = predicted):")
    matrix = confusion_matrix(y_test, y_pred, labels=CLASSES)
    print(pd.DataFrame(matrix, index=[f"actual: {c}" for c in CLASSES], columns=[f"pred: {c}" for c in CLASSES]))

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(build_pipeline(), df["sentence"], df["label"], cv=cv, scoring="accuracy")
    print(f"\nCross-validation (5 folds) - mean accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})\n")
    return pipeline


def classify(pipeline: Pipeline, sentences: list[str]) -> None:
    probas = pipeline.predict_proba(sentences)
    high_idx = list(pipeline.classes_).index("high risk")
    for sentence, proba in zip(sentences, probas):
        p_high = proba[high_idx]
        label = "high risk" if p_high >= 0.5 else "low risk"
        print(f"Sentence: {sentence}")
        print(f"  Classification: {label.upper()} | P(high risk) = {p_high:.1%}\n")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CardioIA - risk classifier")
    parser.add_argument("--sentence", action="append", help="sentence to classify (the option can be repeated)")
    args = parser.parse_args()

    df = load_dataset()
    print(f"Dataset: {len(df)} sentences")
    print(df["label"].value_counts().to_string(), "\n")

    pipeline = train_and_evaluate(df)
    print("=" * 78)
    print("Testing new sentences\n")
    classify(pipeline, args.sentence or NEW_SENTENCES)
    print("Disclaimer: educational text classification. It does not replace a medical evaluation.")


if __name__ == "__main__":
    main()
