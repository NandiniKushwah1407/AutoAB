"""
LLM-Powered Diff Analyser — AutoAB

Flow:
  1. Playwright crawls both Version A and Version B URLs
  2. Extract visible text + key HTML elements
  3. Compute a unified diff between the two
  4. Send the diff to Groq (Llama 3.1 70B, free) → fallback to Ollama (local)
  5. LLM returns: what changed, hypotheses, which metrics to track
"""

import asyncio
import json
from typing import Optional
from config import get_settings

settings = get_settings()

# ── LLM Prompt Template ───────────────────────────────────────
DIFF_PROMPT = """
You are an expert UX analyst and A/B testing specialist.

Two versions of a web application are being compared in an A/B test:
- Version A (Control):   {url_a}
- Version B (Treatment): {url_b}

Here is the content diff between the two versions:

{diff_content}

Analyse this diff and return ONLY valid JSON with EXACTLY this structure (no extra text):
{{
    "changes_detected": [
        {{
            "element":     "e.g. CTA Button",
            "change":      "e.g. Color changed from blue (#4A90D9) to red (#E63946)",
            "impact_area": "e.g. conversion_rate, urgency, visual hierarchy"
        }}
    ],
    "hypotheses": [
        {{
            "id":         "H1",
            "hypothesis": "e.g. Red CTA button will increase conversion rate",
            "metric":     "e.g. conversion_rate",
            "direction":  "increase"
        }}
    ],
    "recommended_metrics": {{
        "primary":    "e.g. conversion_rate",
        "secondary":  ["e.g. ctr", "e.g. session_duration"],
        "guardrails": ["e.g. bounce_rate"]
    }},
    "risk_factors": [
        "e.g. Red button may reduce accessibility for colour-blind users"
    ],
    "summary": "One-paragraph plain English summary of what changed and what to expect."
}}
"""


# ── Web Crawler ───────────────────────────────────────────────
async def crawl_page(url: str) -> str:
    """
    Use Playwright headless browser to extract visible content.
    Handles React/Vue/Angular SPAs correctly (fully renders JS).
    """
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=20_000)

            # Extract key UI elements — buttons, headings, text, links
            content = await page.evaluate("""() => {
                const selectors = 'h1,h2,h3,h4,p,button,a,input,label,li,span,nav,header,section,footer,[class*="price"],[class*="cta"],[class*="hero"]';
                const els = document.querySelectorAll(selectors);
                return Array.from(els)
                    .map(e => `[${e.tagName}|${e.className.slice(0,40)}] ${e.textContent.trim().slice(0, 300)}`)
                    .filter(s => s.length > 10)
                    .join('\\n');
            }""")
            await browser.close()
            return content or "[No content extracted]"

    except ImportError:
        return "[Playwright not installed — run: playwright install chromium]"
    except Exception as e:
        return f"[Crawl error for {url}: {str(e)[:200]}]"


# ── Diff Computation ──────────────────────────────────────────
def compute_diff(text_a: str, text_b: str) -> str:
    """Compute a human-readable unified diff between two page texts."""
    import difflib
    diff = list(difflib.unified_diff(
        text_a.splitlines(),
        text_b.splitlines(),
        lineterm="",
        fromfile="Version A (Control)",
        tofile="Version B (Treatment)",
        n=3,
    ))
    # Limit to 250 lines to fit in LLM context window
    return "\n".join(diff[:250]) if diff else "No visible differences detected between the two versions."


# ── Main Entry Point ──────────────────────────────────────────
async def analyse_diff_with_llm(url_a: str, url_b: str) -> dict:
    """
    Main function: crawl → diff → LLM analysis.
    Returns structured JSON with changes, hypotheses, recommended metrics.
    """
    # 1. Crawl both pages in parallel
    text_a, text_b = await asyncio.gather(
        crawl_page(url_a),
        crawl_page(url_b),
    )

    # 2. Compute diff
    diff_content = compute_diff(text_a, text_b)

    # 3. Build prompt
    prompt = DIFF_PROMPT.format(
        url_a=url_a,
        url_b=url_b,
        diff_content=diff_content,
    )

    # 4. Call LLM
    result = await _call_llm(prompt)

    # 5. Attach metadata
    result["meta"] = {
        "url_a":              url_a,
        "url_b":              url_b,
        "diff_lines":         len(diff_content.splitlines()),
        "content_a_length":   len(text_a),
        "content_b_length":   len(text_b),
    }
    return result


# ── LLM Caller (Groq → Ollama fallback) ──────────────────────
async def _call_llm(prompt: str) -> dict:
    """Try Groq API first (free, fast). Falls back to local Ollama."""

    # ── Try Groq (free tier: 14,400 req/day, Llama 3.1 70B) ──
    if settings.groq_api_key:
        try:
            from groq import AsyncGroq
            client   = AsyncGroq(api_key=settings.groq_api_key)
            response = await client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2048,
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"[Groq JSON parse error] {e}")
        except Exception as e:
            print(f"[Groq API error, trying Ollama] {e}")

    # ── Fallback: Ollama local (free, runs on your machine) ───
    try:
        import httpx
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model":  settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
            raw = resp.json().get("response", "{}").strip()
            return json.loads(raw)
    except Exception as e:
        return {
            "error":   str(e),
            "summary": "LLM analysis unavailable. Check your GROQ_API_KEY or Ollama connection.",
            "changes_detected":      [],
            "hypotheses":            [],
            "recommended_metrics":   {"primary": "conversion_rate", "secondary": [], "guardrails": []},
            "risk_factors":          [],
        }
