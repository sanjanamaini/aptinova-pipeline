# APTINOVA Resume Pipeline

A small set of standalone scripts for an AI-assisted resume-screening workflow: pull resume files from a MongoDB-backed store, parse them into structured JSON using a locally-run LLM, and score one parsed candidate against a hardcoded set of HR requirements. This is a prototype/capstone-stage pipeline (3 loose scripts, no orchestration, no API, no UI) rather than a finished platform.

## Tech Stack

- Python
- `pymongo` + `requests` — fetch resume files from a MongoDB Atlas collection (`fetch_resume.py`)
- `PyMuPDF` (`fitz`), `python-docx`, `unoconv` (subprocess) — extract raw text from PDF/DOCX/DOC resumes (`parsing_direct_with_DSR1.py`)
- `ollama` running the local model `deepseek-r1:1.5b-qwen-distill-fp16` — LLM-based extraction of resume text into structured JSON (`parsing_direct_with_DSR1.py`)
- Plain Python dict/JSON logic — candidate scoring (`matching.py`), no ML/LLM involved in this step

## How It Works (3 separate scripts, run manually and in sequence)

1. **`fetch_resume.py`** — connects to a MongoDB `resumes` collection and downloads each resume's file (by URL) into a local `resumeDownloads/` folder.
2. **`parsing_direct_with_DSR1.py`** — for each downloaded resume, extracts raw text (PDF via PyMuPDF, DOCX via python-docx, legacy DOC via `unoconv`), then sends the text to a local DeepSeek-R1 model (via Ollama) with a prompt instructing it to return structured JSON: Name, Skills, Experience (with months + description), Education, Certifications, Projects, and an "Everything Else" free-text field. Output is saved as one JSON file per candidate in `parsed_resumes/`.
3. **`matching.py`** — loads one parsed candidate JSON and compares it against a single **hardcoded** `hr_requirements` dict (technical skills: Python/SQL; soft skills: problem-solving/teamwork; a red-flag list; minimum experience). Scoring is a simple weighted sum (+5 per matched technical skill, +3 per soft skill, +2 per additional skill, +1 per extra skill, -10 per red flag, +5 for meeting minimum experience). Soft skills are "inferred" by keyword search (e.g. looking for "team" or "problem" in experience descriptions) rather than by any model.

## Security Note

`fetch_resume.py` reads the MongoDB connection string from the `MONGO_URI` environment variable (see `.env.example`). Earlier versions in git history contained a hardcoded Atlas credential; treat that credential as compromised and rotate it.

## Run

Each script is run independently and expects local state from the previous step (`resumeDownloads/`, then `parsed_resumes/`). Requires `pymongo`, `requests`, `pymupdf`, `python-docx`, `ollama` (with the `deepseek-r1:1.5b-qwen-distill-fp16` model pulled locally), and `unoconv` (only if processing legacy `.doc` files). No `requirements.txt` is present in this repo.
