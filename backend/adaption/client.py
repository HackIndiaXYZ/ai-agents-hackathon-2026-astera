"""
Adaption API Client — Adaptive Data Platform Integration
Handles: Ingest, Evaluate, Export
"""
import os
import httpx
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ADAPTION_API_KEY = os.getenv("ADAPTION_API_KEY")
ADAPTION_BASE_URL = os.getenv("ADAPTION_BASE_URL", "https://api.adaption.ai")


class AdaptionClient:
    def __init__(self):
        self.api_key = ADAPTION_API_KEY
        self.base_url = ADAPTION_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Platform": "Asteria-HackathonAI"
        }
        # Local fallback log (in case Adaption API has issues)
        self.local_log_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "adaption_log.jsonl"
        )
        os.makedirs(os.path.dirname(self.local_log_path), exist_ok=True)

    def _log_locally(self, record: dict):
        """Always log locally as backup"""
        record["timestamp"] = datetime.utcnow().isoformat()
        with open(self.local_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    async def ingest_qa_pair(
        self,
        query: str,
        response: str,
        language: str,
        domain: str,
        intent: str,
        scheme: str = None,
        feedback: str = None,
        eval_scores: dict = None,
        session_id: str = None
    ) -> dict:
        """
        Push a Q&A pair to the Adaptive Data platform.
        This is the core integration point for the hackathon.
        """
        record = {
            "query": query,
            "response": response,
            "language": language,
            "domain": domain,
            "intent": intent,
            "scheme": scheme,
            "feedback": feedback,
            "eval_scores": eval_scores,
            "session_id": session_id,
            "source": "asteria_agent",
            "project": "ai-agents-hackathon-2026"
        }

        # Always save locally
        self._log_locally(record)

        # Push to Adaption API
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try the dataset ingestion endpoint
                payload = {
                    "data": {
                        "input": query,
                        "output": response,
                        "metadata": {
                            "language": language,
                            "language_code": "bho" if language == "bhojpuri" else "asm",
                            "domain": domain,
                            "intent": intent,
                            "scheme": scheme,
                            "feedback": feedback,
                            "eval_scores": eval_scores,
                            "session_id": session_id,
                            "source": "asteria_agent",
                            "project": "ai-agents-hackathon-2026",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                }

                resp = await client.post(
                    f"{self.base_url}/v1/datasets/ingest",
                    headers=self.headers,
                    json=payload
                )

                if resp.status_code in (200, 201):
                    return {"status": "success", "adaption_id": resp.json().get("id"), "local": True}
                else:
                    # Try alternate endpoint format
                    resp2 = await client.post(
                        f"{self.base_url}/datasets",
                        headers=self.headers,
                        json=payload
                    )
                    if resp2.status_code in (200, 201):
                        return {"status": "success", "adaption_id": resp2.json().get("id"), "local": True}
                    else:
                        return {"status": "local_only", "error": f"API {resp.status_code}", "local": True}

        except Exception as e:
            return {"status": "local_only", "error": str(e), "local": True}

    async def update_feedback(self, session_id: str, message_id: str, feedback: str) -> dict:
        """Update feedback for a specific Q&A pair"""
        record = {
            "action": "feedback_update",
            "session_id": session_id,
            "message_id": message_id,
            "feedback": feedback
        }
        self._log_locally(record)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.patch(
                    f"{self.base_url}/v1/datasets/feedback",
                    headers=self.headers,
                    json={"session_id": session_id, "message_id": message_id, "feedback": feedback}
                )
                return {"status": "success" if resp.status_code in (200, 201) else "local_only"}
        except Exception as e:
            return {"status": "local_only", "error": str(e)}

    def get_local_stats(self) -> dict:
        """Get statistics from local log"""
        try:
            records = []
            if os.path.exists(self.local_log_path):
                with open(self.local_log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            records.append(json.loads(line.strip()))
                        except Exception:
                            pass

            qa_records = [r for r in records if "query" in r]
            bhojpuri = [r for r in qa_records if r.get("language") == "bhojpuri"]
            assamese = [r for r in qa_records if r.get("language") == "assamese"]
            positive_fb = [r for r in qa_records if r.get("feedback") == "correct"]

            return {
                "total_pairs": len(qa_records),
                "bhojpuri_pairs": len(bhojpuri),
                "assamese_pairs": len(assamese),
                "positive_feedback": len(positive_fb),
                "domains": list(set(r.get("domain", "") for r in qa_records))
            }
        except Exception:
            return {"total_pairs": 0, "bhojpuri_pairs": 0, "assamese_pairs": 0}


# Singleton instance
adaption_client = AdaptionClient()
