"""
HuggingFace Dataset Exporter
Exports the Adaption-collected Q&A pairs to HuggingFace Hub
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HF_USERNAME = os.getenv("HF_USERNAME", "Afuu-coder")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "asteria-bhojpuri-assamese-civic-qa")
LOCAL_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "adaption_log.jsonl")


def load_qa_pairs(min_quality: float = 6.0) -> list:
    """Load Q&A pairs from local log, filtering by quality"""
    pairs = []
    if not os.path.exists(LOCAL_LOG_PATH):
        return pairs

    with open(LOCAL_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                if "query" not in record:
                    continue

                # Filter by feedback and quality
                if record.get("feedback") == "wrong":
                    continue  # Skip wrong-flagged pairs

                eval_scores = record.get("eval_scores", {})
                overall = eval_scores.get("overall_score", 7.0) if eval_scores else 7.0
                if overall < min_quality:
                    continue

                pairs.append({
                    "id": f"{record.get('session_id', 'unknown')}_{len(pairs)}",
                    "language": record.get("language", "unknown"),
                    "language_code": "bho" if record.get("language") == "bhojpuri" else "asm",
                    "domain": record.get("domain", "civic"),
                    "intent": record.get("intent", "GENERAL_QA"),
                    "scheme": record.get("scheme", ""),
                    "query": record.get("query", ""),
                    "response": record.get("response", ""),
                    "feedback": record.get("feedback", ""),
                    "eval_factual": eval_scores.get("factual_accuracy", 0) if eval_scores else 0,
                    "eval_language": eval_scores.get("language_quality", 0) if eval_scores else 0,
                    "eval_helpfulness": eval_scores.get("helpfulness", 0) if eval_scores else 0,
                    "eval_overall": overall,
                    "source": "asteria_agent",
                    "timestamp": record.get("timestamp", "")
                })
            except Exception:
                continue

    return pairs


def export_to_huggingface() -> dict:
    """Export dataset to HuggingFace Hub"""
    try:
        from huggingface_hub import HfApi, DatasetCard
        from datasets import Dataset, DatasetDict

        pairs = load_qa_pairs()
        if not pairs:
            return {"status": "error", "message": "No Q&A pairs to export"}

        # Split by language
        bhojpuri_pairs = [p for p in pairs if p["language"] == "bhojpuri"]
        assamese_pairs = [p for p in pairs if p["language"] == "assamese"]

        # Create datasets
        dataset_dict = {}
        if bhojpuri_pairs:
            dataset_dict["bhojpuri"] = Dataset.from_list(bhojpuri_pairs)
        if assamese_pairs:
            dataset_dict["assamese"] = Dataset.from_list(assamese_pairs)

        if not dataset_dict:
            return {"status": "error", "message": "No valid pairs after filtering"}

        full_dataset = DatasetDict(dataset_dict)

        # Push to hub
        repo_id = f"{HF_USERNAME}/{HF_DATASET_REPO}"
        full_dataset.push_to_hub(
            repo_id,
            token=HF_TOKEN,
            private=False
        )

        # Create dataset card
        card_content = f"""---
language:
- bho
- asm
license: cc-by-4.0
tags:
- civic
- government-schemes
- low-resource-language
- bhojpuri
- assamese
- india
- ai-agents
pretty_name: Asteria — Bhojpuri & Assamese Civic Q&A Dataset
size_categories:
- n<1K
---

# Asteria — Bhojpuri & Assamese Civic Q&A Dataset

A dataset of government scheme Q&A pairs in **Bhojpuri** and **Assamese** — two low-resource Indian languages.

## Dataset Description

This dataset was collected by **Asteria**, an AI Agent built for the AI Agents Hackathon 2026. The agent helps rural Indian citizens access government welfare schemes by conversing in their native language.

### Supported Languages
- **Bhojpuri** (bho) — spoken by 50+ million people in Bihar, UP, Jharkhand
- **Assamese** (asm) — spoken by 15+ million people in Assam

### Domains Covered
- Agriculture (PM Kisan, Fasal Bima)
- Healthcare (Ayushman Bharat)  
- Housing (PM Awas Yojana)
- Energy (Ujjwala Yojana)
- Finance (Jan Dhan)
- Food Security (Ration Card)

### Dataset Fields
- `query`: User question in Bhojpuri/Assamese
- `response`: AI agent response in the same language
- `language`: Language name (bhojpuri/assamese)
- `language_code`: ISO code (bho/asm)
- `domain`: Scheme domain
- `intent`: User intent (APPLY_SCHEME, CHECK_ELIGIBILITY, GET_DOCUMENTS, etc.)
- `scheme`: Government scheme name
- `eval_factual`: Factual accuracy score (0-10)
- `eval_language`: Language quality score (0-10)
- `eval_helpfulness`: Helpfulness score (0-10)
- `eval_overall`: Overall quality score (0-10)

## Built With

- **Adaptive Data by Adaption** — For dataset ingestion, evaluation, and management
- **Gemini 1.5 Flash** — AI agent backbone
- **ChromaDB** — RAG memory for continuous improvement

## Credits

Dataset collected and curated using the **Adaptive Data platform by Adaption**.  
Built for the **AI Agents Hackathon 2026** organized by HackIndia.

## License

Creative Commons Attribution 4.0 International (CC BY 4.0)
"""
        api = HfApi(token=HF_TOKEN)
        api.upload_file(
            path_or_fileobj=card_content.encode(),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset"
        )

        return {
            "status": "success",
            "repo_id": repo_id,
            "url": f"https://huggingface.co/datasets/{repo_id}",
            "total_pairs": len(pairs),
            "bhojpuri": len(bhojpuri_pairs),
            "assamese": len(assamese_pairs)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    result = export_to_huggingface()
    print(json.dumps(result, indent=2))
