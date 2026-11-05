# Aletheia (`aletheia-core`)

![Aletheia CI](https://github.com/wandersonsc/aletheia-core/actions/workflows/ci.yml/badge.svg) ![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg) ![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)

> *"Unconcealing what is hidden"* — Multimodal OSINT Claim Verification & Visual Caption QA Web Platform

**Aletheia** is a full-stack Python (FastAPI) and TypeScript web application and verification workbench designed for Portuguese (PT-BR) and Global media analysis. It combines an interactive dark-mode analyst UI, a cross-lingual claim verification pipeline, and a deterministic NLP/RegEx linter that enforces strict editorial and accessibility rules on visual captions.

## Core Modules

### 1. `Aletheia Studio Workbench` — Interactive Web Application (`app/main.py`)
- **Split-Screen Analyst UI:** Serves a dark-mode web workbench at `/` where analysts, journalists, and researchers can audit visual captions and run OSINT claim pre-checks side-by-side in the browser.
- **Real-Time Compliance & OSINT API:** Exposes REST endpoints (`/api/v1/lint-caption`, `/api/v1/precheck-claim`, `/health`) backing the interactive web interface.

### 2. `Aletheia Verify` — Cross-Lingual OSINT & Claim Engine (`app/claim_engine.py`)
- **PT-BR Language Gate with Multimodal Exceptions:** Automatically evaluates Portuguese posts, standalone textless media, and foreign-audio videos that contain Portuguese captions or mid-frame text overlays.
- **Metadata & Temporal Auditor:** Compares post `creation_time` against historical event dates to flag out-of-context footage and recovers `<redacted>` tokens from external URL slugs.
- **Trusted Source Router:** Generates targeted verification queries for primary Brazilian fact-checking organizations (*Estadão Verifica, Aos Fatos, Agência Lupa, UOL Confere, AFP Checamos, Reuters Fact Check PT*) and global health authorities (*WHO, CDC, NIH, Mayo Clinic, Cleveland Clinic*).
- **Standardized Audit Formatter:** Classifies claims across 6 core domains (`health`, `politics and social issues`, `crisis event`, `entertainment`, `scam`, `business and consumer`) and generates structured audit reports.

### 3. `Aletheia Lint` — Deterministic Visual Caption QA (`app/caption_linter.py`)
- **Strict Length & Structure Validation:** Enforces 1 complete sentence (6–25 words) for Short Captions and 1–3 sentences (minimum 26 meaningful words, excluding filler phrases) for Detailed Captions.
- **Prohibited Lexical Filters:** Blocks meta-wording (*"the image shows"*), speculative assumptions (*"appears to"*, *"likely"*), camera/framing jargon (*"close-up"*, *"low-angle"*), provenance assumptions (*"vintage"*, *"historic"*), and subjective/promotional adjectives (*"luxury"*, *"striking"*).
- **Formatting & Privacy Checks:** Validates digit formatting for dates/pages, word formatting for item counts, duplicate word detection, and automated PII/PHI tagging (phone numbers, street addresses, license plates).

## Quick Start (Web App & Tests)

    # Install dependencies
    pip install -r requirements.txt

    # Launch the interactive Aletheia Studio Web Workbench at http://localhost:8000
    uvicorn app.main:app --reload

    # Run the automated Pytest suite
    PYTHONPATH=. pytest tests/

## Roadmap (Active Development with Claude Code)
- [x] Core deterministic regex & word-count engine (`app/caption_linter.py`)
- [x] PT-BR Language Gate, URL slug unmasker, and Claim Report formatter (`app/claim_engine.py`)
- [x] Interactive dark-mode Web Workbench UI & FastAPI endpoints (`app/main.py`)
- [x] Automated Pytest suite & GitHub Actions CI pipeline (`tests/test_aletheia.py`, `.github/workflows/ci.yml`)
- [ ] **Live Inline Editor & Highlighting:** Upgrade the web UI with live word-count badges and inline red underlines highlighting prohibited lexical terms as the user types
- [ ] **One-Click Report Builder UI:** Add interactive Option A / Option B / Option C report generator cards in the web workbench with one-click clipboard export
- [ ] **SQLite Audit History & Search Dashboard:** Persist past caption audits and claim verification reports in a local SQLite database with a searchable history tab in the web UI
- [ ] **Automated Fact-Check Source Scraper (`app/source_scraper.py`):** Fetch live article titles and snippets from Brazilian fact-checkers and clinical authorities directly inside the workbench
- [ ] **Temporal & EXIF Media Inspector:** Add image upload support to inspect metadata timestamps against post creation dates and flag recycled crisis/political media
- [ ] **Expanded Edge-Case Test Coverage:** Grow Pytest suite to 50+ unit and integration tests covering FastAPI routes, number-to-word formatting, and distortion trap rules
