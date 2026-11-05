"""
Automated Pytest suite for Aletheia Verify & Aletheia Lint
"""

from app.caption_linter import audit_captions
from app.claim_engine import (
    ClaimCategory,
    EvaluationRating,
    PostJobInput,
    check_pt_br_language_gate,
    format_verification_report,
    recover_redacted_slug,
)


def test_valid_captions_pass():
    short = "Two golden retrievers sit on a wooden porch next to a red ceramic bowl."
    detailed = (
        "Two golden retrievers sit side by side on a weathered grey wooden porch "
        "in front of a white panelled door with brass hardware. A glossy red ceramic "
        "water bowl rests near the dogs on the left side of the planks."
    )
    result = audit_captions(short, detailed)
    assert result.is_valid is True
    assert result.detailed_meaningful_word_count >= 26
    assert len(result.violations) == 0


def test_prohibited_caption_terms_flagged():
    short = "The image shows a close-up shot of a vintage watch."
    detailed = (
        "In this image, a luxury gold watch appears to be resting on a table "
        "in the frame overall in view."
    )
    result = audit_captions(short, detailed)
    assert result.is_valid is False
    assert any("META_WORDING" in v for v in result.violations)
    assert any("CAMERA_FRAMING" in v for v in result.violations)
    assert any("AGE_PROVENANCE" in v for v in result.violations)


def test_pt_br_language_gate_with_overlay_exception():
    # English transcript, but has Portuguese overlay -> Must pass language gate!
    job = PostJobInput(
        transcript="Look at what happened yesterday in Washington.",
        mid_video_overlay_text="Polícia Federal descobre novo esquema",
        has_Portuguese_caption_or_overlay=True,
    )
    assert check_pt_br_language_gate(job) is True


def test_redacted_slug_recovery():
    recovered = recover_redacted_slug(
        "Visit us at <redacted_us_address>",
        "https://example.com/events/123-main-street-boston-festival",
    )
    assert "123 main street boston festival" in recovered
