"""
CardioIA | Rule-based symptom extraction (NLP).

Pipeline:
    1. read the simulated patient reports (symptoms.txt);
    2. read the knowledge map (knowledge_map.csv) and the spelling variants (synonyms.csv);
    3. normalize the text (lowercase, no accents, no punctuation, simple plural handling);
    4. search for each symptom (and its variants) as a contiguous sequence of words in the report;
    5. score the conditions of the map according to the symptoms found;
    6. print a report and, optionally, save a CSV with the results.

Usage:
    uv run python src/nlp/symptom_extraction.py
    uv run python src/nlp/symptom_extraction.py --csv        # also saves results/nlp/extraction_results.csv
    uv run python src/nlp/symptom_extraction.py --sentence "I have chest pain and a cold sweat"

DISCLAIMER: academic project. The suggestions are didactic simplifications and are NOT a medical diagnosis.
"""

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "text"
RESULTS_DIR = ROOT_DIR / "results" / "nlp"

REPORTS_FILE = DATA_DIR / "symptoms.txt"
MAP_FILE = DATA_DIR / "knowledge_map.csv"
SYNONYMS_FILE = DATA_DIR / "synonyms.csv"

DISCLAIMER = "Educational result only. This is not a medical diagnosis."
MAX_SUGGESTIONS = 3


def remove_accents(text: str) -> str:
    """Remove accents: 'café' -> 'cafe' (keeps the code robust to accented input)."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def simplify_token(token: str) -> str:
    """Simple plural handling: 'legs' -> 'leg', 'heartbeats' -> 'heartbeat'.

    This is not a full stemmer; it only drops the trailing 's' of words longer than 3 letters.
    Because the same rule is applied to the report and to the dictionary, singular and plural forms match.
    """
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def normalize_text(text: str) -> list[str]:
    """Turn a text into a list of normalized tokens.

    'I have CHEST pain, and swollen legs!' -> ['i', 'have', 'chest', 'pain', 'and', 'swollen', 'leg']
    """
    text = remove_accents(text.lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [simplify_token(tok) for tok in text.split()]


def contains_sequence(tokens: list[str], expression: list[str]) -> bool:
    """Check whether the expression appears in the report as a contiguous sequence of words.

    Comparing whole words avoids false matches such as 'art' inside 'heart'.
    """
    size = len(expression)
    return any(tokens[i:i + size] == expression for i in range(len(tokens) - size + 1))


def load_reports(path: Path = REPORTS_FILE) -> list[str]:
    with path.open(encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def load_knowledge_map(path: Path = MAP_FILE) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def load_synonyms(path: Path = SYNONYMS_FILE) -> dict[str, list[str]]:
    """Return {canonical_symptom: [variant_1, variant_2, ...]}."""
    synonyms = defaultdict(list)
    if path.exists():
        with path.open(encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                synonyms[row["canonical_symptom"].strip()].append(row["variant"].strip())
    return synonyms


def build_symptom_patterns(knowledge_map: list[dict], synonyms: dict[str, list[str]]) -> dict[str, list[list[str]]]:
    """For each symptom in the map, build the list of normalized expressions that represent it."""
    symptoms = sorted({row[col].strip() for row in knowledge_map for col in ("symptom_1", "symptom_2")})
    patterns = {}
    for symptom in symptoms:
        expressions = [symptom] + synonyms.get(symptom, [])
        patterns[symptom] = [normalize_text(expr) for expr in expressions]
    return patterns


def extract_symptoms(report: str, patterns: dict[str, list[list[str]]]) -> list[str]:
    """Return the canonical symptoms of the map found in the report."""
    tokens = normalize_text(report)
    return [symptom for symptom, expressions in patterns.items()
            if any(contains_sequence(tokens, expr) for expr in expressions)]


def suggest_diagnoses(found_symptoms: list[str], knowledge_map: list[dict], top_n: int = MAX_SUGGESTIONS) -> list[dict]:
    """Score each condition of the map based on the symptoms found.

    Scoring rule (intentionally simple):
      - points    = number of found symptoms that the map associates with the condition;
      - coverage  = points / total number of symptoms the map associates with the condition;
      - tie-break = coverage (conditions with fewer "missing" symptoms rank higher).
    """
    found = set(found_symptoms)
    related = defaultdict(set)
    for row in knowledge_map:
        related[row["associated_condition"].strip()].update({row["symptom_1"].strip(), row["symptom_2"].strip()})

    ranking = []
    for condition, condition_symptoms in related.items():
        matched = condition_symptoms & found
        if matched:
            ranking.append({
                "condition": condition,
                "points": len(matched),
                "coverage": len(matched) / len(condition_symptoms),
                "symptoms": sorted(matched),
            })
    ranking.sort(key=lambda item: (item["points"], item["coverage"]), reverse=True)
    return ranking[:top_n]


def analyze_report(report: str, patterns: dict, knowledge_map: list[dict]) -> dict:
    symptoms = extract_symptoms(report, patterns)
    return {"report": report, "symptoms": symptoms, "suggestions": suggest_diagnoses(symptoms, knowledge_map)}


def print_result(index: int, result: dict) -> None:
    print("=" * 78)
    print(f"Patient {index}")
    print(f'Report:\n  "{result["report"]}"\n')

    print("Identified symptoms:")
    if result["symptoms"]:
        for symptom in result["symptoms"]:
            print(f"  - {symptom}")
    else:
        print("  (no symptom from the knowledge map was found)")

    print("\nPossible conditions (ranked by score):")
    if result["suggestions"]:
        for pos, item in enumerate(result["suggestions"], start=1):
            print(f"  {pos}. {item['condition']:<30} points={item['points']}  "
                  f"coverage={item['coverage']:.0%}  ({', '.join(item['symptoms'])})")
    else:
        print("  (no suggestions)")

    print(f"\nDisclaimer: {DISCLAIMER}\n")


def save_csv(results: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["patient", "report", "identified_symptoms", "condition_1", "condition_2", "condition_3"])
        for index, result in enumerate(results, start=1):
            conditions = [f"{s['condition']} ({s['points']})" for s in result["suggestions"]]
            conditions += [""] * (MAX_SUGGESTIONS - len(conditions))
            writer.writerow([index, result["report"], "; ".join(result["symptoms"]), *conditions])
    print(f"Results saved to: {path.relative_to(ROOT_DIR).as_posix()}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="CardioIA - symptom extraction")
    parser.add_argument("--sentence", help="analyze a single sentence instead of the symptoms.txt file")
    parser.add_argument("--csv", action="store_true", help="save the results to results/extraction_results.csv")
    args = parser.parse_args()

    knowledge_map = load_knowledge_map()
    patterns = build_symptom_patterns(knowledge_map, load_synonyms())
    reports = [args.sentence] if args.sentence else load_reports()

    print(f"CardioIA - symptom extraction | {len(reports)} report(s), {len(knowledge_map)} associations in the map, "
          f"{len(patterns)} distinct symptoms\n")

    results = [analyze_report(report, patterns, knowledge_map) for report in reports]
    for index, result in enumerate(results, start=1):
        print_result(index, result)

    if args.csv:
        save_csv(results, RESULTS_DIR / "extraction_results.csv")


if __name__ == "__main__":
    main()
