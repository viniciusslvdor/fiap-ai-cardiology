# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href= "https://www.fiap.com.br/"><img src="assets/branding/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=40% height=40%></a>
</p>

<br>

# CardioIA - Phase 1: Data Heartbeats


## Member:
- Vinicius Salvador

## Professors:
### Tutor
- Leonardo Ruiz Orabona
### Coordinator
- André Godoi

## Description

**CardioIA** is the academic project carried out over 7 phases of FIAP's AI course, following the PBL (Project Based Learning) methodology. The goal is to progressively build a digital platform that simulates the ecosystem of a modern cardiology practice, integrating clinical data, Machine Learning, Computer Vision, IoT and intelligent agents to support triage, diagnosis, monitoring and remote patient assistance.

This repository contains the deliverable for **Phase 1, Data Heartbeats**, in which I take on the role of a hospital data scientist responsible for sourcing, organizing and documenting the three datasets that will feed the intelligent modules of the following phases:

1. **Numeric data** on cardiac patients (age, sex, blood pressure, cholesterol, symptoms, heart rate, disease history), to be used in future predictive models (Phase 2) and IoT monitoring (Phase 3);
2. **Textual data** on cardiovascular disease and public health, for exploration with NLP techniques (Phases 2 and 5, assisted diagnosis and virtual assistant);
3. **Visual data** from cardiology-related exams (chest X-ray images), for future use in Computer Vision (Phase 4).

For each of the three parts, this repository documents the origin of the data (real, with citation and license), justifies the clinical relevance of the selected variables/texts/images, and explicitly discusses **data governance and bias**, consistent with the AI governance concepts already covered in the course. This stage is deliberately effortful. Part of the learning goal of this phase is to deal with health datasets scattered across different repositories, in heterogeneous formats and sometimes blocked to automated access, and to work around that by combining reliable public sources (UCI Machine Learning Repository, Project Gutenberg, PubMed Central, GitHub) instead of giving up at the first obstacle.

All scripts used to download, clean and organize the data are reproducible and versioned under `scripts/`, so that anyone on the FIAP team can re-run the collection process from scratch.

## Folder structure

Among the files and folders present at the root of the project, the following are defined:

- <b>assets</b>: unstructured elements of the repository. `branding/` holds the institutional logo and `images/` holds the 150 chest X-ray images and their metadata (Part 3 deliverable).

- <b>data</b>: numeric data for Part 1. `raw/heart-disease/` contains the original files downloaded from UCI (untreated) and `processed/` contains the final dataset `cardioai_numeric_dataset.csv`.

- <b>docs</b>: the two medical/literary texts selected for Part 2 (NLP data).

- <b>notebooks</b>: exploratory data analysis of the Part 1 numeric dataset.

- <b>scripts</b>: all source code used to collect, clean and organize the data for the three parts throughout Phase 1 (equivalent to the standard template's `src`).

- <b>README.md</b>: general project guide (this file).

```
cardioai/
├── README.md
├── assets/
│   ├── branding/logo-fiap.png
│   └── images/                              # Part 3: 150 chest X-ray images
│       ├── cxr_001.jpeg ... cxr_150.png
│       └── images_metadata.csv
├── data/                                    # Part 1: numeric dataset
│   ├── raw/heart-disease/                   # original files downloaded from UCI (untreated)
│   └── processed/
│       └── cardioai_numeric_dataset.csv
├── docs/                                    # Part 2: medical/literary texts
│   ├── harvey_motion_of_the_heart.txt
│   └── erico_cad_prognosis_public_health.txt
├── notebooks/
│   └── eda_numeric_dataset.ipynb            # exploratory analysis of the Part 1 dataset
├── scripts/
│   ├── build_dataset.py                     # generates the combined CSV from the raw UCI data
│   ├── extract_pmc_text.py                  # extracts the clean text of the ERICO article (PMC) for Part 2
│   └── download_images.py                   # filters and downloads the image sample for Part 3
├── pyproject.toml                           # project metadata and dependencies (managed with uv)
└── uv.lock                                  # pinned dependency versions
```

## How to run the code

Prerequisites: Python 3.13+, internet access (the scripts download data from public sources), and [uv](https://docs.astral.sh/uv/) if you want to run the notebook.

```bash
# Part 1: generates data/processed/cardioai_numeric_dataset.csv
python scripts/build_dataset.py

# Part 2: re-extracts the ERICO article text from the HTML downloaded from PMC
python scripts/extract_pmc_text.py

# Part 3: downloads the sample of 150 chest X-ray images and generates the metadata
python scripts/download_images.py
```

The three scripts above only require the Python standard library (`csv`, `re`, `urllib`).

The exploratory data analysis notebook needs a few extra packages (pandas, matplotlib, Jupyter). This project uses [uv](https://docs.astral.sh/uv/) to manage the environment and dependencies, declared in `pyproject.toml` and pinned in `uv.lock`:

```bash
uv sync

# opens the notebook using that environment
uv run jupyter notebook notebooks/eda_numeric_dataset.ipynb
```

`uv run` can also be used to execute the three scripts above (e.g. `uv run python scripts/build_dataset.py`) without needing to manually activate the virtual environment.

---

## Phase 1 deliverables

## Part 1 - Numeric Data (IoT)

### Data origin

**Real** (not simulated) data, sourced from the **UCI Machine Learning Repository, Heart Disease Data Set**, one of the most widely used datasets in the AI-for-cardiology literature.

- Official source: https://archive.ics.uci.edu/dataset/45/heart+disease
- License: Creative Commons Attribution 4.0 International (CC BY 4.0). Free use and redistribution, with attribution.
- Citation: Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1989). *Heart Disease* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C52P4X

The final dataset (`data/processed/cardioai_numeric_dataset.csv`) combines the **4 hospital databases** made available by UCI, totaling **920 patients**:

| Institution | Records |
|---|---|
| Cleveland Clinic Foundation (USA) | 303 |
| Hungarian Institute of Cardiology, Budapest | 294 |
| University Hospital, Zurich/Basel (Switzerland) | 123 |
| V.A. Medical Center, Long Beach (USA) | 200 |

The final CSV was generated by the script [`scripts/build_dataset.py`](scripts/build_dataset.py), which reads the 4 raw files (`data/raw/heart-disease/processed.*.data`), assigns readable column names, handles missing values (marked as `?` in the original source), and adds two derived columns to help readability (`sex_label` and `disease_presence`).

A simple exploratory data analysis of this dataset (missing values, distributions, target balance, and the institution bias check) is available in [`notebooks/eda_numeric_dataset.ipynb`](notebooks/eda_numeric_dataset.ipynb).

### Variable dictionary

| CSV column | Original variable (UCI) | Description |
|---|---|---|
| `age` | age | Patient age in years |
| `sex` | sex | 1 = male, 0 = female |
| `chest_pain_type` | cp | Chest pain type (1 = typical angina, 2 = atypical angina, 3 = non-anginal pain, 4 = asymptomatic) |
| `resting_blood_pressure` | trestbps | Resting blood pressure (mm Hg) on hospital admission |
| `serum_cholesterol` | chol | Serum cholesterol (mg/dl) |
| `high_fasting_blood_sugar` | fbs | Fasting blood sugar > 120 mg/dl (1 = true, 0 = false) |
| `resting_ecg` | restecg | Resting electrocardiographic results (0 = normal, 1 = ST-T wave abnormality, 2 = left ventricular hypertrophy) |
| `max_heart_rate` | thalach | Maximum heart rate achieved during exercise test |
| `exercise_induced_angina` | exang | Exercise-induced angina (1 = yes, 0 = no) |
| `exercise_st_depression` | oldpeak | ST depression induced by exercise relative to rest |
| `st_slope_peak_exercise` | slope | Slope of the peak exercise ST segment |
| `num_major_vessels` | ca | Number of major vessels (0 to 3) colored by fluoroscopy |
| `thalassemia` | thal | 3 = normal, 6 = fixed defect, 7 = reversible defect |
| `diagnosis_disease_0to4` | num | Original heart disease diagnosis, scale 0 (absent) to 4 (most severe) |
| `sex_label` | (derived) | `M`/`F`, readable version of `sex` |
| `disease_presence` | (derived from num) | Usual binarization in the literature: 0 = no disease, 1 = disease present (any grade 1 or higher) |
| `source_institution` | (derived) | Hospital/institution where the record was collected |

### Most clinically relevant variables and why

- **`age`, `sex`**: non-modifiable risk factors. Cardiovascular risk increases with age and differs by biological sex, making these essential stratification variables in any predictive model.
- **`chest_pain_type` and `exercise_induced_angina`**: symptoms directly associated with myocardial ischemia. They are often the strongest predictors in coronary disease classification models.
- **`resting_blood_pressure`** and **`serum_cholesterol`**: classic, modifiable risk factors (hypertension and dyslipidemia), widely used in cardiovascular risk scores such as Framingham.
- **`max_heart_rate`** and **`exercise_st_depression`**: obtained during a stress test, they indicate cardiac functional capacity and exercise-induced ischemia, making them strong predictors of obstructive disease.
- **`num_major_vessels`** and **`thalassemia`**: results from imaging/perfusion exams, directly correlated with the anatomical extent of coronary disease.
- **`disease_presence`**: the target variable, what the ML models in the following phases (Phase 2, Automated Diagnosis) will try to predict from the other variables.

### Data governance and bias

- The data was **anonymized at the source** (patient names and identification numbers were already removed by the dataset's original authors).
- Because it combines **4 institutions from different countries** (USA, Hungary, Switzerland), the dataset carries a **population-composition bias**: different proportions of age, sex, and diagnosis prevalence per institution. The exploratory analysis in [`notebooks/eda_numeric_dataset.ipynb`](notebooks/eda_numeric_dataset.ipynb) quantifies this: diagnosis prevalence ranges from about 36% in the Hungarian records to about 93% in the Swiss records. This must be considered before training generalist models in the following phases, at the risk of the model learning population-specific patterns and generalizing poorly to others.
- There are **missing values** (mainly in the `thalassemia` and `num_major_vessels` columns for the Swiss and Hungarian databases), left as empty cells in the CSV. Any ML pipeline in the following phases will need an explicit imputation or exclusion strategy.
- Use restricted to academic purposes, respecting the CC BY 4.0 license and the mandatory citation of the original authors.

**Public link to the full dataset:** https://drive.google.com/drive/folders/1Rnyb5qoJ4UAI7IpOl44qkLuWHbx4s8Bs?usp=sharing (shared Google Drive folder, contains both the Part 1 and Part 3 deliverables)

---

## Part 2 - Textual Data (NLP)

Two public-domain / open-access texts were selected, representing the two source types suggested in the assignment: classic literature (Project Gutenberg) and a public health scientific article (SciELO/PMC).

### Text 1: Classic scientific literature

**File:** [`docs/harvey_motion_of_the_heart.txt`](docs/harvey_motion_of_the_heart.txt) (about 79,000 words)

- **Title:** *An Anatomical Disquisition on the Motion of the Heart & Blood in Animals*
- **Author:** William Harvey (1628), translated by Robert Willis, J. M. Dent & Co. edition, 1906
- **Source:** Project Gutenberg, https://www.gutenberg.org/ebooks/67065
- **License:** Public domain (Project Gutenberg License, free use and redistribution)
- **Context:** The founding work of modern cardiology, in which Harvey describes for the first time blood circulation and the functioning of the heart as a mechanical pump. A long text, structured in chapters, with technical-descriptive language on cardiac anatomy and physiology.

### Text 2: Public health scientific article

**File:** [`docs/erico_cad_prognosis_public_health.txt`](docs/erico_cad_prognosis_public_health.txt) (about 950 words)

- **Title:** *Prognosis of Coronary Artery Disease in Public Hospitals in Brazil: The ERICO Study and the Application of Knowledge in Public Health*
- **Author:** Fatima Marinho (UFMG / Vital Strategies)
- **Publication:** Arquivos Brasileiros de Cardiologia, v. 117, n. 5, p. 986-987, Nov. 2021 (SciELO-indexed journal)
- **Access source:** PubMed Central / National Library of Medicine (NIH), https://pmc.ncbi.nlm.nih.gov/articles/PMC8682102/ (DOI: 10.36660/abc.20210825)
- **License:** Creative Commons Attribution (CC BY), open access article
- **Context:** Editorial on the epidemiology of coronary artery disease in Brazil, SUS (public health system) data, risk factors (hypertension, sedentary lifestyle, smoking), and socioeconomic determinants of cardiovascular mortality. The article was originally published in Portuguese; the text used here is the **official English version** provided in full by the journal/PMC, not a machine translation.

> Collection note: the raw documents from Brazil's Ministry of Health/BVS (`bvsms.saude.gov.br`) and the SciELO HTML pages (`scielo.br`) returned connection errors (blocking automated access) at collection time. As an equivalent alternative, using the same journal, same content and same SciELO indexing, the article was obtained via its official mirror on PubMed Central (NIH), preserving the scientific origin and open license required by the assignment.

### How these texts can be explored with NLP

- **Symptom and clinical term extraction (NER, Named Entity Recognition):** both texts explicitly mention symptoms, clinical findings and medical terminology (e.g., "angina," "hypertension," "acute myocardial infarction," "acute coronary syndrome"). An NLP pipeline can extract these entities to build a dictionary of cardiology symptoms used in Phases 2 and 5 (automated diagnosis and triage chatbot).
- **Topic classification:** since the two texts have very different styles and purposes (a historical anatomical treatise vs. a contemporary epidemiological editorial), the pair is useful for training/testing a topic or text-genre classifier (e.g., "historical medical literature" vs. "public health/epidemiology"), relevant for organizing a future CardioIA knowledge base.
- **Sentiment/tone analysis:** the ERICO study text uses alerting, urgent language about mortality and risk factors, while Harvey's text is descriptive and neutral. Comparing polarity and tone between the two is a direct sentiment-analysis exercise applied to biomedical text.
- **Automatic summarization:** the ERICO article, being short and dense, is a good candidate for testing extractive/abstractive summarization models, generating summaries that could feed the Phase 5 virtual assistant.
- **Statistical/relation extraction (Information Extraction):** the ERICO text contains public health statistics in natural language (e.g., "prevalence of 1.75%," "78,575 angioplasties"). It is a good exercise in structured data extraction from unstructured text, bridging Part 1 (numeric data) and Part 2 (textual data) of the project.

These analyses are relevant to an AI-in-health project because a large share of clinical and epidemiological knowledge still exists only as free text (medical records, articles, guidelines). Extracting and structuring that information is what allows systems like CardioIA to complement numeric and image data with clinical context and up-to-date scientific evidence.

---

## Part 3 - Visual Data (Computer Vision)

### Data origin

**150 real images** of **chest X-rays** (one of the three modalities suggested in the assignment, along with ECG and angiogram), selected from the public **COVID-19 Image Data Collection**, maintained by Dr. Joseph Paul Cohen (Mila/Université de Montréal) and collaborators.

- Source: https://github.com/ieee8023/covid-chestxray-dataset
- Citation: Cohen, J. P., Morrison, P., & Dao, L. (2020). *COVID-19 Image Data Collection*. arXiv:2003.11597. https://arxiv.org/abs/2003.11597
- Project approved by the University of Montreal's Ethics Committee (#CERSES-20-058-D); images extracted from publicly published scientific articles and clinical case reports.
- **License:** each image has its own license listed in the `license` column of [`assets/images/images_metadata.csv`](assets/images/images_metadata.csv), predominantly CC BY-NC-SA and CC BY-NC-ND (non-commercial use, compatible with academic purposes). The original dataset's `metadata.csv` is licensed under CC BY-NC-SA 4.0.

### How the sample was selected

Out of the roughly 950 entries in the original dataset (X-rays and CT scans, multiple views), only images matching the following were kept:
- **Modality:** X-ray (`X-ray`), excluding CT scans;
- **View:** PA, AP, or AP Supine (standard chest radiograph views used in clinical practice);
- **Format:** `.jpg`/`.jpeg`/`.png`.

The selection and download process is in the script [`scripts/download_images.py`](scripts/download_images.py), which also generates [`assets/images/images_metadata.csv`](assets/images/images_metadata.csv) with, for each image: file name, clinical finding (`finding`), view, sex, age, license, and DOI of the source publication.

**Public link to the full image set:** https://drive.google.com/drive/folders/1Rnyb5qoJ4UAI7IpOl44qkLuWHbx4s8Bs?usp=sharing (same shared Google Drive folder as Part 1, contains both deliverables)

### Bias and data governance (images)

- The dataset is heavily biased toward **COVID-19/viral pneumonia** cases (in the downloaded sample, about 75% of cases have the finding `Pneumonia/Viral/COVID-19`), reflecting its original COVID-19 research purpose. It is not an epidemiologically representative sample of the general population, nor is it balanced between "normal" and "pathological" cases. This must be taken into account in Phases 4 (Computer Vision) and 7 before training any classifier with these images, at the risk of the model learning to recognize pneumonia patterns rather than general cardiac patterns.
- Clinical metadata (age, sex, finding) per image was preserved to allow demographic bias auditing.
- Use restricted to academic, non-commercial purposes, respecting the individual licenses listed in the metadata CSV.

### Potential for Computer Vision analysis

- **Edge detection and cardiac silhouette segmentation:** edge-detection algorithms (e.g., Canny, Sobel) and segmentation models (e.g., U-Net) can isolate the outline of the heart and rib cage in the radiograph, enabling calculation of the **cardiothoracic ratio**, a classic measure used to identify cardiomegaly (heart enlargement), an indirect sign of heart failure.
- **Pattern/anomaly recognition:** convolutional neural networks (CNNs) can be trained to distinguish normal radiographs from those with opacities, consolidations, or infiltrates. This is the same technical principle used to detect signs of pulmonary congestion associated with heart failure, even though this specific dataset labels the anomalies as pneumonia/COVID-19.
- **Multi-class classification:** the `finding` column in the metadata CSV already provides labels (viral, bacterial, fungal, "no finding") that allow training and evaluating supervised image classifiers, serving as a direct exercise for Phase 4 of the project.
- **Longitudinal comparison:** since the original dataset includes multiple images of the same patient at different dates (`patientid`/`offset` columns), it is possible to explore image-comparison-over-time models, relevant for tracking the evolution of cardiac/pulmonary conditions in remote monitoring (Phase 5/6).

These analyses are relevant to AI applied to healthcare because reading imaging exams still heavily depends on the availability and expertise of a specialist. Computer vision algorithms can act as a second opinion, enable automated triage in locations with a shortage of radiologists, and support the prioritization of urgent cases, all central goals of the CardioIA ecosystem.

---

## Release history

* 0.1.0 - 08/25/2026
    * Phase 1 deliverable: numeric dataset (920 patients, UCI Heart Disease), two texts for NLP (Harvey / ERICO study), and 150 chest X-ray images for Computer Vision, with documented origin, license, and governance/bias notes.

## License

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/agodoi/template">FIAP GIT MODEL</a> by <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">Fiap</a> is licensed under <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>

The data used in this repository follows the individual licenses of each source, detailed in the Part 1, Part 2 and Part 3 sections above (UCI CC BY 4.0, Project Gutenberg public domain, article under CC BY, images predominantly CC BY-NC-SA/CC BY-NC-ND).
