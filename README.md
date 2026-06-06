# Data Engineering Practice

A structured, day-by-day learning repository for becoming a job-ready **Data Engineer** — built from the ground up using local tools before moving to cloud platforms.

This repository tracks daily practice exercises, concept notes, and hands-on projects covering the full data engineering stack: Python, dbt, Apache Airflow, PySpark, and beyond.

---

## Goals

- Build job-ready data engineering skills through daily hands-on practice
- Cover the full local data engineering stack before cloud platforms
- Maintain a portfolio of end-to-end pipeline projects for interviews

---

## Learning Roadmap

| Phase | Topics | Duration |
|-------|--------|----------|
| **Phase 1** | Python for Data Engineering | Weeks 1–2 |
| **Phase 2** | dbt (Data Build Tool) | Weeks 3–5 |
| **Phase 3** | Apache Airflow | Weeks 6–8 |
| **Phase 4** | Apache Spark / PySpark | Weeks 9–12 |
| **Phase 5** | Portfolio Projects | Week 13+ |

---

## Repository Structure

```
data-engineering-practice/
│
├── daily-exercises/              # Attempts, evaluations, fixes and scores
│   ├── day1_exercises.py
│   ├── day2_exercises.py
│   └── ...
│
├── daily-notes/                  # Full concept notes for each day's topics
│   ├── day1_notes.py
│   ├── day2_notes.py
│   └── ...
│
├── dayN/                         # Raw working/scratch files used during session
│   └── dayN_exercises.py
│
└── README.md
```

### Folder Descriptions

| Folder | Purpose |
|--------|---------|
| `daily-exercises/` | Polished exercise files — contains the original attempt, all corrections, evaluation score, and key takeaways |
| `daily-notes/` | Complete concept notes taught each day — syntax, rules, examples, and gotchas |
| `dayN/` | Raw scratch folder used during live coding — unpolished, as-written during the session |

---

## Day-wise Index

### Phase 1 — Python for Data Engineering

| Day | Topic | Concepts Covered | Score |
|-----|-------|-----------------|-------|
| [Day 1](daily-exercises/day1_exercises.py) | Python Basics | Data structures, functions, list comprehensions, file I/O (CSV/JSON), error handling, f-strings | 7.5/10 |
| Day 2 | Pandas Basics | *(upcoming)* | — |
| Day 3 | Pandas — Filtering & Aggregations | *(upcoming)* | — |
| Day 4 | File Formats | *(upcoming)* | — |
| Day 5 | SQLAlchemy | *(upcoming)* | — |
| Day 6 | psycopg2 | *(upcoming)* | — |
| Day 7 | Mini ETL Project | *(upcoming)* | — |

---

## Day-wise Notes Summary

### Day 1 — Python Basics for Data Engineering
**Date:** 2026-06-06

**Topics covered:**
- **Data structures** — lists, dicts, list-of-dicts (most common pipeline format), tuples
- **Functions & list comprehensions** — writing reusable clean functions, replacing for-loops with comprehensions
- **File I/O** — reading and writing CSV (`csv.DictReader`, `csv.DictWriter`) and JSON (`json.load`, `json.dump`)
- **Error handling** — wrapping `open()` inside `try`, catching specific exceptions (`FileNotFoundError`, `ValueError`, `TypeError`), returning `None` for bad values instead of crashing
- **f-strings** — preferred over string concatenation for readability and performance
- **Record mutation** — always use `record.copy()` before modifying; never mutate original raw data in a pipeline

**Key rules learned:**
- `newline=""` is for CSV writers only — never use on JSON file handles
- Always wrap `open()` inside the `try` block, not outside
- Functions must accept parameters — no hardcoded paths in pipeline code
- Catch specific exceptions, not broad `Exception`

📄 [Full notes](daily-notes/day1_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day1_exercises.py)

---

## Tools & Stack

| Tool | Purpose | Phase |
|------|---------|-------|
| Python 3.11+ | Scripting and pipeline logic | 1 |
| pandas | Data manipulation | 1 |
| SQLAlchemy | Python ↔ database connector | 1 |
| psycopg2 | Raw SQL from Python | 1 |
| PyArrow | Parquet file format support | 1 |
| PostgreSQL | Local relational database | 1–3 |
| dbt-core | SQL-based data transformations | 2 |
| Apache Airflow | Pipeline orchestration (via Docker) | 3 |
| Apache Spark | Distributed data processing | 4 |
| Docker Desktop | Run Airflow and Spark locally | 3–4 |
| DBeaver | Database GUI | 1+ |
| VS Code | Primary IDE | All |

---

## Prerequisites

- Python 3.11+
- PostgreSQL (local install)
- Docker Desktop (from Phase 3)
- VS Code with Python + Pylance extensions

Install Phase 1 dependencies:
```bash
python -m venv venv
venv\Scripts\activate
pip install pandas sqlalchemy psycopg2-binary pyarrow openpyxl
```
