"""
Push dataset to HuggingFace Hub
Run: python scripts/push_to_huggingface.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

HF_TOKEN = os.getenv("HF_TOKEN")
HF_USERNAME = os.getenv("HF_USERNAME", "Afuu-coder")
DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset")

DATASET_CARD = """---
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
- hackathon
- adaptive-data
pretty_name: Asteria — Bhojpuri & Assamese Civic AI Agent Dataset
size_categories:
- n<1K
task_categories:
- question-answering
- text-generation
---

# 🌟 Asteria — Bhojpuri & Assamese Civic Q&A Dataset

> Built for **AI Agents Hackathon 2026** by HackIndia using **Adaptive Data by Adaption**

A first-of-its-kind dataset of government scheme Q&A pairs in **Bhojpuri** and **Assamese** — two severely low-resource Indian languages with 60+ million combined speakers.

## 🎯 Dataset Purpose

This dataset powers **Asteria**, an autonomous AI Agent that helps rural Indian citizens access government welfare schemes by conversing in their native language.

## 📊 Dataset Statistics

| Language | Code | Speakers | Q&A Pairs | Domain |
|----------|------|----------|-----------|--------|
| Bhojpuri | bho | 50M+ (Bihar, UP, Jharkhand) | ~150 | Government Schemes |
| Assamese | asm | 15M+ (Assam) | ~150 | Government Schemes |

## 🏛️ Government Schemes Covered

| Scheme | Domain | Benefit |
|--------|--------|---------|
| PM Kisan Samman Nidhi | Agriculture | ₹6,000/year for farmers |
| Ayushman Bharat | Healthcare | ₹5 lakh health insurance |
| PM Awas Yojana | Housing | ₹1.2 lakh for house construction |
| PM Ujjwala Yojana | Energy | Free LPG connection |
| Jan Dhan Yojana | Finance | Zero-balance bank account |
| PM Fasal Bima | Agriculture | Crop insurance |
| Ration Card (NFSA) | Food Security | Subsidized food grains |

## 📁 Dataset Fields

```json
{
  "language": "bhojpuri",
  "language_code": "bho",
  "domain": "agriculture",
  "intent": "APPLY_SCHEME",
  "scheme": "PM_KISAN",
  "query": "PM Kisan mein apply kaise karein? (in Bhojpuri)",
  "response": "PM Kisan mein... (detailed answer in Bhojpuri)",
  "feedback": "correct",
  "eval_factual": 9.0,
  "eval_language": 8.5,
  "eval_helpfulness": 9.0,
  "eval_overall": 8.8,
  "source": "asteria_agent"
}
```

## 🔄 Data Sources

1. **HuggingFace ai4bharat/IndicQA** — Assamese Q&A pairs (benchmark dataset)
2. **Gemini 1.5 Flash Generation** — Synthetic civic Q&A pairs
3. **Hand-crafted seed pairs** — Expert-verified Q&A in authentic dialect
4. **Live agent conversations** — Real user interactions (feedback-filtered)

## 🤖 Built With

- **Adaptive Data by Adaption** — Dataset ingestion, evaluation, and management platform
- **Gemini 1.5 Flash** — AI agent and synthetic data generation
- **ChromaDB** — RAG memory for continuous improvement

## 📋 Intent Types

| Intent | Description |
|--------|-------------|
| `KNOW_SCHEME` | User wants general info about a scheme |
| `CHECK_ELIGIBILITY` | User wants to know if they qualify |
| `GET_DOCUMENTS` | User wants document checklist |
| `APPLY_SCHEME` | User wants step-by-step application help |
| `COMPLAINT` | User has a problem/grievance |
| `GENERAL_QA` | General civic question |
| `LIST_SCHEMES` | User wants to see available schemes |

## 🏆 Hackathon Context

Built for the **Adaptive Data Track** at **AI Agents Hackathon 2026** organized by HackIndia.

**Problem Statement addressed:**
> *"Build an AI agent for a low-resource language using Adaptive Data, where the dataset continuously improves through user feedback and corrections"*

## 📜 Citation

```bibtex
@dataset{asteria_civic_qa_2026,
  title={Asteria — Bhojpuri and Assamese Civic Q&A Dataset},
  author={Afuu-coder},
  year={2026},
  publisher={HuggingFace},
  note={Built using Adaptive Data by Adaption for AI Agents Hackathon 2026}
}
```

## 🙏 Credits

Dataset collected and curated using the **[Adaptive Data platform by Adaption](https://adaption.ai)**.

## 📄 License

[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
"""


def push_to_huggingface():
    print("=" * 60)
    print("🤗 Pushing to HuggingFace Hub")
    print(f"   Repo: {HF_USERNAME}/asteria-bhojpuri-assamese-civic-qa")
    print("=" * 60)

    try:
        from datasets import Dataset, DatasetDict
        from huggingface_hub import HfApi

        # Load local datasets
        bho_pairs, asm_pairs = [], []

        bho_file = os.path.join(DATASET_DIR, "bhojpuri_civic_qa.jsonl")
        asm_file = os.path.join(DATASET_DIR, "assamese_civic_qa.jsonl")

        if os.path.exists(bho_file):
            with open(bho_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        bho_pairs.append(json.loads(line.strip()))
                    except:
                        pass
        else:
            print("   ⚠️  bhojpuri_civic_qa.jsonl not found — run build_dataset.py first")

        if os.path.exists(asm_file):
            with open(asm_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        asm_pairs.append(json.loads(line.strip()))
                    except:
                        pass
        else:
            print("   ⚠️  assamese_civic_qa.jsonl not found — run build_dataset.py first")

        if not bho_pairs and not asm_pairs:
            print("   ❌ No data to push! Run: python scripts/build_dataset.py first")
            return

        print(f"\n   Bhojpuri pairs: {len(bho_pairs)}")
        print(f"   Assamese pairs: {len(asm_pairs)}")

        # Create HuggingFace datasets
        dataset_dict = {}
        if bho_pairs:
            dataset_dict["bhojpuri"] = Dataset.from_list(bho_pairs)
        if asm_pairs:
            dataset_dict["assamese"] = Dataset.from_list(asm_pairs)

        full_ds = DatasetDict(dataset_dict)
        repo_id = f"{HF_USERNAME}/asteria-bhojpuri-assamese-civic-qa"

        print(f"\n   Uploading to {repo_id}...")
        full_ds.push_to_hub(repo_id, token=HF_TOKEN, private=False)

        # Upload dataset card
        api = HfApi(token=HF_TOKEN)
        api.upload_file(
            path_or_fileobj=DATASET_CARD.encode("utf-8"),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset"
        )

        print(f"\n✅ SUCCESS!")
        print(f"   🔗 https://huggingface.co/datasets/{repo_id}")
        print(f"\n📋 Next: Fill submission form at")
        print(f"   https://uc9yb.share.hsforms.com/2VyQDViA5RQOCS3ydhGF6mA")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check HF_TOKEN in .env")
        print("  2. Run: pip install datasets huggingface-hub")
        print("  3. Run build_dataset.py first to generate data")


if __name__ == "__main__":
    push_to_huggingface()
