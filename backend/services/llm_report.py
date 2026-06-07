"""
LLM Report Generator — AutoAB

Takes the statistical analysis results + LLM diff analysis and generates
a clear, plain-English experiment report with a concrete recommendation.
"""

import json
from config import get_settings

settings = get_settings()

REPORT_PROMPT = """
You are a senior data scientist writing an A/B experiment report for a product team.

EXPERIMENT DETAILS:
  Name:             {experiment_name}
  Duration:         {duration_days} days
  Control Users:    {control_users}
  Treatment Users:  {treatment_users}

WHAT CHANGED (AI Diff Analysis):
{diff_summary}

STATISTICAL RESULTS:
{results_json}

Write a concise, actionable experiment report. Return ONLY valid JSON:
{{
    "verdict":      "SHIP_B" | "KEEP_A" | "CONTINUE" | "INVESTIGATE",
    "confidence":   "HIGH" | "MEDIUM" | "LOW",
    "headline":     "One sentence summary (e.g. Red button drives +28% conversion lift)",
    "what_changed": "Plain English description of the changes tested",
    "what_happened": "What the data shows — metrics, lifts, p-values in plain language",
    "risks_to_consider": ["Risk 1", "Risk 2"],
    "recommendation": "Clear actionable recommendation",
    "next_steps": ["Step 1", "Step 2"]
}}
"""


async def generate_report(experiment, analysis_results: dict, diff_analysis: dict) -> dict:
    """
    Generate an LLM-powered final report.

    Args:
        experiment:      SQLAlchemy Experiment ORM object
        analysis_results: Output from ABTestAnalyser.run_all_tests()
        diff_analysis:   Output from analyse_diff_with_llm()
    """
    diff_summary = diff_analysis.get("summary", "No diff analysis available.")
    results_json = json.dumps(analysis_results.get("results", {}), indent=2)

    prompt = REPORT_PROMPT.format(
        experiment_name  = experiment.name,
        duration_days    = experiment.duration_days,
        control_users    = analysis_results.get("experiment_summary", {}).get("control_users", 0),
        treatment_users  = analysis_results.get("experiment_summary", {}).get("treatment_users", 0),
        diff_summary     = diff_summary,
        results_json     = results_json,
    )

    return await _call_llm(prompt)


async def _call_llm(prompt: str) -> dict:
    """Groq API (free) → Ollama fallback."""

    if settings.groq_api_key:
        try:
            from groq import AsyncGroq
            client   = AsyncGroq(api_key=settings.groq_api_key)
            response = await client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1024,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except Exception as e:
            print(f"[Report LLM Groq error] {e}")

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
            return json.loads(resp.json().get("response", "{}").strip())
    except Exception as e:
        return {
            "error":          str(e),
            "verdict":        "INVESTIGATE",
            "confidence":     "LOW",
            "headline":       "LLM report unavailable — check Groq API key or Ollama.",
            "recommendation": "Review statistical results manually.",
            "what_changed":   "",
            "what_happened":  "",
            "risks_to_consider": [],
            "next_steps":     [],
        }
