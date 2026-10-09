"""Extracts the clean English text of the ERICO editorial downloaded from PMC for the CardioIA text corpus."""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "tmp_pmc.html"
OUT = Path(__file__).resolve().parents[2] / "data" / "text" / "erico_cad_prognosis_public_health.txt"

HEADER = """MARINHO, Fatima. Prognosis of Coronary Artery Disease in Public Hospitals
in Brazil: The ERICO Study and the Application of Knowledge in Public Health.
Arquivos Brasileiros de Cardiologia, v. 117, n. 5, p. 986-987, Nov. 2021.

Source: PubMed Central (PMC), National Library of Medicine (NIH)
URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC8682102/
DOI: 10.36660/abc.20210825
License: Creative Commons Attribution License (CC BY) - open access article
Originally published in Arquivos Brasileiros de Cardiologia (SciELO-indexed
journal), English version provided in full by PMC/NIH.

================================================================================

"""


def main():
    html = SRC.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")

    start_marker = "The group of cardiovascular diseases (CVD) includes"
    end_marker = "Footnotes"
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    body = text[start:end]

    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r" ?\n ?", "\n", body)
    paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
    body_clean = "\n\n".join(paragraphs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(HEADER + body_clean + "\n", encoding="utf-8")
    print(f"Generated: {OUT} ({len(body_clean)} characters)")


if __name__ == "__main__":
    main()
