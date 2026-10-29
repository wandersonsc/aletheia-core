"""
Aletheia Verify — Multimodal OSINT & Claim Verification Engine (PT-BR & Global)
Handles language gate logic, redacted URL recovery, source routing, and report formatting.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from urllib.parse import urlparse


class ClaimCategory(str, Enum):
    HEALTH = "health"
    POLITICS = "politics and social issues"
    CRISIS = "crisis event"
    ENTERTAINMENT = "entertainment"
    SCAM = "scam"
    BUSINESS = "business and consumer"


class EvaluationRating(str, Enum):
    TRUE = "True"
    FALSE = "False"
    PARTLY_FALSE = "Partly False"
    FALSE_OR_PARTLY_FALSE = "False or Partly False"
    NO_CLAIM = "No Claim"
    NO_EVIDENCE = "No Evidence / Unverified"


PT_BR_FACT_CHECK_DOMAINS = [
    "estadao.com.br/estadao-verifica",
    "noticias.uol.com.br/confere",
    "checamos.afp.com",
    "reuters.com/fact-check/portugues",
    "aosfatos.org",
    "lupa.uol.com.br",
    "observador.pt/factchecks",
]

GLOBAL_MEDICAL_DOMAINS = [
    "who.int",
    "cdc.gov",
    "nih.gov",
    "fda.gov",
    "mayoclinic.org",
    "my.clevelandclinic.org",
    "health.harvard.edu",
]


@dataclass
class PostJobInput:
    content_in_review: str = ""
    creation_time: Optional[str] = None
    external_link_url: Optional[str] = None
    text_in_media: str = ""
    mid_video_overlay_text: str = ""
    transcript: str = ""
    has_Portuguese_caption_or_overlay: bool = False
    is_textless_standalone_media: bool = False


def recover_redacted_slug(text: str, external_url: Optional[str]) -> str:
    """
    If text contains <redacted_us_address> or <redacted_us_phone>,
    extract the human-readable slug from the external URL for verification context.
    """
    if "<redacted" not in text or not external_url:
        return text
    parsed = urlparse(external_url)
    slug = parsed.path.strip("/").replace("-", " ").replace("/", " ")
    return f"{text} [Recovered URL Slug Context: {slug}]"


def check_pt_br_language_gate(job: PostJobInput) -> bool:
    """
    Returns True if the job qualifies for standard evaluation in the PT-BR queue.
    Exceptions:
    1. Foreign spoken transcript WITH Portuguese caption/overlay -> Evaluate normally (True).
    2. Textless/speechless standalone photo or video -> Evaluate normally (True).
    """
    if job.is_textless_standalone_media or job.has_Portuguese_caption_or_overlay:
        return True

    combined = f"{job.content_in_review} {job.text_in_media} {job.mid_video_overlay_text}"
    pt_markers = re.findall(
        r"\b(não|para|com|que|uma|está|pelo|sobre|governo|saúde|verdade|falso)\b",
        combined.lower(),
    )
    return len(pt_markers) > 0


def build_targeted_search_queries(claim_keywords: str, is_health_or_global: bool = False) -> List[str]:
    """Generate targeted search queries prioritized for PT-BR fact-checkers or clinical authorities."""
    domains = GLOBAL_MEDICAL_DOMAINS if is_health_or_global else PT_BR_FACT_CHECK_DOMAINS
    site_filter = " OR ".join(f"site:{d}" for d in domains[:4])
    return [
        f"{claim_keywords} ({site_filter})",
        f"{claim_keywords}",
    ]


def format_verification_report(
    rating: EvaluationRating,
    central_claim: str = "No Claim",
    category: Optional[ClaimCategory] = None,
    search_method: str = "keyword search",
    search_terms: str = "",
    source_1_name: str = "",
    source_2_name: str = "",
    evidence_summary: str = "",
    rationale_sentence: str = "",
    evidence_urls: Optional[List[str]] = None,
    no_claim_intent: str = "share a personal opinion",
) -> str:
    """Formats the final verification report into Option A, Option B, or Option C."""
    evidence_urls = evidence_urls or []

    if rating == EvaluationRating.NO_CLAIM:
        return (
            "**Potential Central Claim:** No Claim\n"
            "**Final Evaluation Rating:** No Claim\n\n"
            "**Feedback**\n"
            "Always consider the primary purpose of the post in determining if there is a statement "
            "of fact which needs to be evaluated. The primary intent of this post is to "
            f"{no_claim_intent}. Nowhere within the post text, media, or on the linked website are "
            "there specific falsifiable statements of fact presented that would need to be evaluated. "
            "As a result, this job would be appropriately marked as having no claim.\n\n"
            "**Potential Evidence Sources:**\n"
            "- N/A (No Claim)"
        )

    if rating == EvaluationRating.NO_EVIDENCE:
        cat_label = category.value if category else "politics and social issues"
        return (
            f"**Potential Central Claim:** {central_claim}\n"
            "**Final Evaluation Rating:** No Evidence / Unverified\n\n"
            "**Feedback**\n"
            f'A {search_method} conducted on Google using the keywords "{search_terms}" '
            "did not reveal any trustworthy news, official, or fact-checking sources that confirm "
            "or refute the specific claim presented within this job.\n\n"
            "Based upon the lack of available trustworthy evidence from recognized authorities or "
            "established news organizations, this job would be appropriately labeled as no evidence / "
            f"unverified and categorized as {cat_label}.\n\n"
            "**Potential Evidence Sources:**\n"
            f"- No trustworthy evidence found (Queries run: {search_terms})"
        )

    # Option A: True, False, Partly False, False or Partly False
    cat_label = category.value if category else "politics and social issues"
    sources_str = "\n".join(f"- {url}" for url in evidence_urls) if evidence_urls else "- N/A"
    return (
        f"**Potential Central Claim:** {central_claim}\n"
        f"**Final Evaluation Rating:** {rating.value}\n\n"
        "**Feedback**\n"
        f'A {search_method} conducted on Google using the keywords "{search_terms}" reveals '
        f"multiple trustworthy sources, including articles on {source_1_name} and {source_2_name}, "
        "which directly address the specific claim presented within this job.\n\n"
        f"According to the {source_1_name} article, {evidence_summary}\n\n"
        f"Based upon this information, the job would be appropriately labeled as {rating.value.lower()} "
        f"and categorized as {cat_label} since {rationale_sentence}\n\n"
        "**Potential Evidence Sources:**\n"
        f"{sources_str}"
    )
