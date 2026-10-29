# CLAUDE.md — Project Aletheia Development Guide

## Project Overview
Aletheia (`aletheia-core`) is a Python 3.12 (FastAPI) and TypeScript application for multimodal fact-checking (PT-BR & Global) and deterministic image caption quality assurance.

## Commands
- Run linter engine tests: `pytest tests/`
- Start API server: `uvicorn app.main:app --reload`

## Architecture & Coding Standards
1. **`app/caption_linter.py`**: Must remain 100% deterministic (Python/RegEx/NLP) with zero hallucination risk. Never allow filler phrases ("in the frame", "overall", "in view") to count toward the 26-word minimum for Detailed Captions.
2. **`app/claim_engine.py`**: Handles multimodal claim extraction, PT-BR language gate exceptions (foreign audio + PT-BR overlay = evaluate normally), `<redacted>` URL slug recovery, and standardized Option A / B / C report generation without bracketed citations.
3. **Priority Categories**: `health` always takes highest severity priority when multiple claims exist in a single post.
