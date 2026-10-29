# Aletheia (`aletheia-core`)
> *"Unconcealing what is hidden"* — Multimodal OSINT Claim Verification & Visual Caption QA Engine

**Aletheia** is a modular Python (FastAPI) and TypeScript verification platform designed for Portuguese (PT-BR) and Global media analysis. It combines a cross-lingual claim verification pipeline with a deterministic NLP/RegEx linter that enforces strict editorial and accessibility rules on visual captions.

## Core Modules

### 1. `Aletheia Verify` — Cross-Lingual OSINT & Claim Engine (`app/claim_engine.py`)
- **PT-BR Language Gate with Multimodal Exceptions:** Automatically evaluates Portuguese posts, standalone textless media, and foreign-audio videos that contain Portuguese captions or mid-frame text overlays.
- **Metadata & Temporal Auditor:** Compares post `creation_time` against historical event dates to flag out-of-context footage and recovers `<redacted>` tokens from external URL slugs.
- **Trusted Source Router:** Generates targeted verification queries for primary Brazilian fact-checking organizations (*Estadão Verifica, Aos Fatos, Agência Lupa, UOL Confere, AFP Checamos, Reuters Fact Check PT*) and global health authorities (*WHO, CDC, NIH, Mayo Clinic, Cleveland Clinic*).
- **Standardized Audit Formatter:** Classifies claims across 6 core domains (`health`, `politics and social issues`, `crisis event`, `entertainment`, `scam`, `business and consumer`) and generates structured audit reports.

### 2. `Aletheia Lint` — Deterministic Visual Caption QA (`app/caption_linter.py`)
- **Strict Length & Structure Validation:** Enforces 1 complete sentence (6–25 words) for Short Captions and 1–3 sentences (minimum 26 meaningful words, excluding filler phrases) for Detailed Captions.
- **Prohibited Lexical Filters:** Blocks meta-wording (*"the image shows"*), speculative assumptions (*"appears to"*, *"likely"*), camera/framing jargon (*"close-up"*, *"low-angle"*), provenance assumptions (*"vintage"*, *"historic"*), and subjective/promotional adjectives (*"luxury"*, *"striking"*).
- **Formatting & Privacy Checks:** Validates digit formatting for dates/pages, word formatting for item counts, duplicate word detection, and automated PII/PHI tagging (phone numbers, street addresses, license plates).

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
