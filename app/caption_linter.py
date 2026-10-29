"""
Aletheia Lint — Deterministic Visual Caption QA Engine
Enforces strict lexical, structural, and PII rules on Short and Detailed Captions.
"""

import re
from dataclasses import dataclass, field
from typing import List


FILLER_PHRASES = [
    r"\bin the frame\b",
    r"\boverall\b",
    r"\bin view\b",
]

PROHIBITED_PATTERNS = {
    "META_WORDING": [
        r"\bthe image shows\b",
        r"\bin this image\b",
        r"\ba photo of\b",
        r"\ba photograph of\b",
        r"\bthis picture shows\b",
    ],
    "ASSUMPTIONS": [
        r"\bappears to\b",
        r"\bseems\b",
        r"\blikely\b",
        r"\bpossibly\b",
        r"\bprobably\b",
        r"\brapidly\b",
        r"\bmoving slowly\b",
    ],
    "CAMERA_FRAMING": [
        r"\bclose-up shot\b",
        r"\bclose-up\b",
        r"\bmacro\b",
        r"\beye-level\b",
        r"\bmedium shot\b",
        r"\blow-angle\b",
        r"\blong exposure\b",
    ],
    "AGE_PROVENANCE": [
        r"\bhistoric\b",
        r"\bvintage\b",
        r"\bantique\b",
        r"\barchival\b",
        r"\bold\b",
        r"\bancient\b",
    ],
    "SUBJECTIVE_PROMOTIONAL": [
        r"\bluxury\b",
        r"\bgourmet\b",
        r"\brugged\b",
        r"\bstriking\b",
        r"\bornate\b",
    ],
    "UNSUPPORTED_SETTING": [
        r"\boffice buildings?\b",
        r"\btaxis?\b",
        r"\bindoor/outdoor\b",
    ],
}

PII_PATTERNS = {
    "PHONE_NUMBER": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "STREET_ADDRESS": r"\b\d{1,5}\s+[A-Z][a-zA-Z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b",
}


@dataclass
class CaptionAuditResult:
    is_valid: bool
    short_word_count: int
    detailed_meaningful_word_count: int
    violations: List[str] = field(default_factory=list)
    recommended_tags: List[str] = field(default_factory=list)


def strip_quoted_text(text: str) -> str:
    """Remove exact quoted transcriptions before scanning for prohibited provenance words."""
    return re.sub(r'"[^"]*"', "", text)


def count_meaningful_words(text: str) -> int:
    """Count words after stripping filler phrases that cannot pad word counts."""
    cleaned = text
    for pattern in FILLER_PHRASES:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    words = [w for w in re.split(r"\s+", cleaned.strip()) if w]
    return len(words)


def split_sentences(text: str) -> List[str]:
    """Split caption into sentences while preserving abbreviations."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    return sentences


def audit_captions(short_caption: str, detailed_caption: str) -> CaptionAuditResult:
    violations: List[str] = []
    recommended_tags: List[str] = []

    short_words = [w for w in re.split(r"\s+", short_caption.strip()) if w]
    short_word_count = len(short_words)
    detailed_word_count = count_meaningful_words(detailed_caption)

    # 1. Short Caption length & sentence structure (1 sentence, 6-25 words)
    short_sentences = split_sentences(short_caption)
    if len(short_sentences) != 1:
        violations.append(
            f"Short Caption must be exactly 1 sentence (found {len(short_sentences)})."
        )
    if not (6 <= short_word_count <= 25):
        violations.append(
            f"Short Caption typically requires 6-25 words (found {short_word_count})."
        )

    # 2. Detailed Caption length & structure (1-3 sentences, minimum 26 meaningful words)
    detailed_sentences = split_sentences(detailed_caption)
    if not (1 <= len(detailed_sentences) <= 3):
        violations.append(
            f"Detailed Caption must be 1-3 sentences (found {len(detailed_sentences)})."
        )
    if detailed_word_count < 26:
        violations.append(
            f"Detailed Caption requires at least 26 meaningful words (found {detailed_word_count} after removing filler)."
        )

    # 3. Prevent Detailed Caption from simply repeating Short Caption at the start
    if detailed_caption.strip().lower().startswith(short_caption.strip().rstrip(".").lower()):
        violations.append(
            "Detailed Caption must not begin by simply repeating the Short Caption."
        )

    # 4. Check prohibited vocabulary across both captions
    combined_text = f"{short_caption} {detailed_caption}"
    unquoted_text = strip_quoted_text(combined_text)

    for category, patterns in PROHIBITED_PATTERNS.items():
        target = unquoted_text if category == "AGE_PROVENANCE" else combined_text
        for pattern in patterns:
            match = re.search(pattern, target, flags=re.IGNORECASE)
            if match:
                violations.append(
                    f"Prohibited {category} term detected: '{match.group(0)}'."
                )

    # 5. Check formatting: double spaces & consecutive repeated words
    if "  " in short_caption or "  " in detailed_caption:
        violations.append("Unnecessary double spaces detected.")

    repeated_word = re.search(r"\b(\w+)\s+\1\b", combined_text, flags=re.IGNORECASE)
    if repeated_word:
        violations.append(f"Repeated consecutive word detected: '{repeated_word.group(1)}'.")

    # 6. Check PII/PHI triggers
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, combined_text):
            recommended_tags.append(f"PII_PHI:{pii_type}")

    return CaptionAuditResult(
        is_valid=len(violations) == 0,
        short_word_count=short_word_count,
        detailed_meaningful_word_count=detailed_word_count,
        violations=violations,
        recommended_tags=recommended_tags,
    )
