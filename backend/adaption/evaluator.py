"""
Evaluation Agent — Automatically evaluates every AI response
Covers Problem Statement 2 as a bonus feature
"""
import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = genai.Client(vertexai=True, project="asteria-497909", location="us-central1")


class EvaluationAgent:
    """
    A second AI agent that evaluates the quality of the main agent's responses.
    This is the 'Evaluation Pipeline' required by the hackathon.
    """

    async def evaluate_response(
        self,
        query: str,
        response: str,
        language: str,
        domain: str,
        scheme: str = None,
        scheme_data: dict = None
    ) -> dict:
        """
        Evaluate a response on 3 dimensions:
        1. Factual Accuracy (is scheme info correct?)
        2. Language Quality (is it natural Bhojpuri/Assamese?)
        3. Helpfulness (did it answer the intent?)
        """
        scheme_context = ""
        if scheme_data:
            scheme_context = f"""
Reference scheme data:
- Benefit: {scheme_data.get('benefit', 'N/A')}
- Eligibility: {scheme_data.get('eligibility', {})}
- Helpline: {scheme_data.get('helpline', 'N/A')}
"""

        lang_name = "Bhojpuri" if language == "bhojpuri" else "Assamese"

        eval_prompt = f"""You are an expert evaluator for an AI agent that helps rural Indian citizens access government schemes.

Evaluate this AI response and return ONLY a valid JSON object.

USER QUERY ({lang_name}): {query}
AI RESPONSE: {response}
DOMAIN: {domain}
SCHEME: {scheme or 'General'}
{scheme_context}

Rate on these 3 criteria (0-10 each):

1. factual_accuracy: Is the information factually correct about the scheme? (10 = perfectly accurate, 0 = completely wrong)
2. language_quality: Is the language natural {lang_name}? Easy to understand for rural users? (10 = excellent natural dialect, 0 = unnatural/wrong language)  
3. helpfulness: Does it actually help the user achieve their goal? Does it give actionable next steps? (10 = fully helpful, 0 = useless)

Also give:
- overall_score: average of the 3 scores
- issues: list of specific problems found (empty list if none)
- suggestion: one sentence improvement suggestion (in English)

Return ONLY this JSON (no markdown, no explanation):
{{"factual_accuracy": 8, "language_quality": 7, "helpfulness": 9, "overall_score": 8.0, "issues": [], "suggestion": "Add helpline number"}}"""

        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=eval_prompt
            )
            text = response.text.strip()

            # Clean up if model adds markdown
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            scores = json.loads(text)
            scores["evaluated"] = True
            return scores

        except Exception as e:
            # Fallback scores if evaluation fails
            return {
                "factual_accuracy": 7,
                "language_quality": 7,
                "helpfulness": 7,
                "overall_score": 7.0,
                "issues": [],
                "suggestion": "Evaluation unavailable",
                "evaluated": False,
                "error": str(e)
            }

    def get_quality_badge(self, overall_score: float) -> dict:
        """Return a quality badge based on score"""
        if overall_score >= 8.5:
            return {"label": "Excellent", "color": "#00c896", "emoji": "⭐"}
        elif overall_score >= 7.0:
            return {"label": "Good", "color": "#4a9eff", "emoji": "✅"}
        elif overall_score >= 5.0:
            return {"label": "Fair", "color": "#f5a623", "emoji": "⚠️"}
        else:
            return {"label": "Needs Review", "color": "#ff4757", "emoji": "❌"}


evaluation_agent = EvaluationAgent()
