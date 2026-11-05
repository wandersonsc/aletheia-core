"""
Aletheia Studio — Web Application & API Server
Serves the interactive Aletheia Analyst Workbench UI and verification endpoints.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from app.caption_linter import audit_captions
from app.claim_engine import (
    PostJobInput,
    build_targeted_search_queries,
    check_pt_br_language_gate,
    recover_redacted_slug,
)

app = FastAPI(
    title="Aletheia Studio",
    description="Multimodal OSINT Claim Verification & Visual Caption QA Workbench",
    version="0.3.0",
)


class CaptionLintRequest(BaseModel):
    short_caption: str
    detailed_caption: str


class ClaimVerifyRequest(BaseModel):
    content_in_review: str = ""
    creation_time: Optional[str] = None
    external_link_url: Optional[str] = None
    text_in_media: str = ""
    mid_video_overlay_text: str = ""
    transcript: str = ""
    has_Portuguese_caption_or_overlay: bool = False
    is_textless_standalone_media: bool = False
    claim_keywords: str = ""
    is_health_or_global: bool = False


WORKBENCH_HTML = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ALETHEIA // OSINT & Visual QA Workbench</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans">
    <header class="border-b border-slate-800 bg-slate-900/60 px-6 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-3">
            <span class="h-3 w-3 rounded-full bg-emerald-400"></span>
            <h1 class="text-lg font-bold tracking-widest uppercase">Aletheia Studio</h1>
            <span class="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded">v0.3.0 // PT-BR & Global</span>
        </div>
        <div class="text-xs text-slate-400">Multimodal Verification & Visual Caption Linter</div>
    </header>

    <main class="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Module 1: Aletheia Lint (Visual Caption QA) -->
        <section class="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 class="text-base font-semibold text-emerald-400 uppercase tracking-wider">
                1. Aletheia Lint // Visual Caption QA
            </h2>
            <div>
                <label class="block text-xs text-slate-400 mb-1">Short Caption (1 sentence, 6–25 words)</label>
                <input id="shortCap" type="text" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm"
                    placeholder="Two golden retrievers sit on a wooden porch next to a red bowl.">
            </div>
            <div>
                <label class="block text-xs text-slate-400 mb-1">Detailed Caption (1–3 sentences, min 26 meaningful words)</label>
                <textarea id="detailedCap" rows="4" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm"
                    placeholder="Expand on the short caption with visible color, position, material, quantity, and background details..."></textarea>
            </div>
            <button onclick="runCaptionAudit()" class="bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium px-4 py-2 rounded-lg">
                Run Compliance Audit
            </button>
            <pre id="lintOutput" class="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 overflow-x-auto hidden"></pre>
        </section>

        <!-- Module 2: Aletheia Verify (OSINT Claim Pre-Check) -->
        <section class="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 class="text-base font-semibold text-sky-400 uppercase tracking-wider">
                2. Aletheia Verify // PT-BR & Global OSINT Engine
            </h2>
            <div>
                <label class="block text-xs text-slate-400 mb-1">Post Text / Content in Review</label>
                <textarea id="postContent" rows="3" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm"
                    placeholder="Paste social media post text, transcript, or mid-video overlay text..."></textarea>
            </div>
            <div>
                <label class="block text-xs text-slate-400 mb-1">External Link URL (for &lt;redacted&gt; slug unmasking)</label>
                <input id="extUrl" type="text" class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm"
                    placeholder="https://example.com/news/article-slug">
            </div>
            <button onclick="runClaimPrecheck()" class="bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium px-4 py-2 rounded-lg">
                Generate OSINT Verification Queries
            </button>
            <pre id="claimOutput" class="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 overflow-x-auto hidden"></pre>
        </section>
    </main>

    <script>
        async function runCaptionAudit() {
            const res = await fetch('/api/v1/lint-caption', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    short_caption: document.getElementById('shortCap').value,
                    detailed_caption: document.getElementById('detailedCap').value
                })
            });
            const data = await res.json();
            const out = document.getElementById('lintOutput');
            out.classList.remove('hidden');
            out.textContent = JSON.stringify(data, null, 2);
        }

        async function runClaimPrecheck() {
            const res = await fetch('/api/v1/precheck-claim', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    content_in_review: document.getElementById('postContent').value,
                    external_link_url: document.getElementById('extUrl').value
                })
            });
            const data = await res.json();
            const out = document.getElementById('claimOutput');
            out.classList.remove('hidden');
            out.textContent = JSON.stringify(data, null, 2);
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def serve_workbench():
    """Serves the interactive Aletheia Studio web interface."""
    return WORKBENCH_HTML


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "aletheia-core"}


@app.post("/api/v1/lint-caption")
def lint_caption_endpoint(payload: CaptionLintRequest):
    result = audit_captions(payload.short_caption, payload.detailed_caption)
    return {
        "is_valid": result.is_valid,
        "short_word_count": result.short_word_count,
        "detailed_meaningful_word_count": result.detailed_meaningful_word_count,
        "violations": result.violations,
        "recommended_tags": result.recommended_tags,
    }


@app.post("/api/v1/precheck-claim")
def precheck_claim_endpoint(payload: ClaimVerifyRequest):
    job = PostJobInput(
        content_in_review=payload.content_in_review,
        creation_time=payload.creation_time,
        external_link_url=payload.external_link_url,
        text_in_media=payload.text_in_media,
        mid_video_overlay_text=payload.mid_video_overlay_text,
        transcript=payload.transcript,
        has_Portuguese_caption_or_overlay=payload.has_Portuguese_caption_or_overlay,
        is_textless_standalone_media=payload.is_textless_standalone_media,
    )
    passes_language_gate = check_pt_br_language_gate(job)
    unmasked_content = recover_redacted_slug(job.content_in_review, job.external_link_url)
    queries = build_targeted_search_queries(
        payload.claim_keywords or job.content_in_review[:80],
        is_health_or_global=payload.is_health_or_global,
    )
    return {
        "passes_pt_br_language_gate": passes_language_gate,
        "unmasked_content": unmasked_content,
        "recommended_search_queries": queries,
    }
