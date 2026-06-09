---
license: mit
language:
- bho
- as
tags:
- civic
- government-schemes
- low-resource
- adaption
- ai-agent
- synthetic
pretty_name: Asteria Bhojpuri & Assamese Civic Q&A
size_categories:
- 1K<n<10K
---

# 🌟 Asteria: Low-Resource Civic Q&A Dataset

![Asteria Banner](https://img.shields.io/badge/Asteria-AI_Agent-indigo?style=for-the-badge&logo=google-gemini)
![Languages](https://img.shields.io/badge/Languages-Bhojpuri_%7C_Assamese-success?style=for-the-badge)
![Adaption](https://img.shields.io/badge/Powered_by-Adaption_Data-blue?style=for-the-badge)

Welcome to the **Asteria Civic Q&A Dataset**! This dataset was built to empower AI agents to assist rural Indian citizens in their native dialects (**Bhojpuri** and **Assamese**) with navigating essential government schemes.

## 🎯 Purpose
Created for the **AI Agent Hackathon 2026**, this dataset addresses the critical gap in low-resource language support for public services. It provides a highly specialized, domain-specific foundation for AI agents handling civic queries.

## 📊 Dataset Statistics
- **Total Q&A Pairs:** 1,228
- **Bhojpuri (bho):** 636 pairs
- **Assamese (asm):** 592 pairs
- **Generation Method:** 100% Synthetic (Gemini 2.5 Flash via Vertex AI)
- **Evaluation:** Evaluated and pushed via the **Adaptive Data Platform**.

## 🏛️ Domain Coverage (Government Schemes)
The dataset covers high-impact Indian government schemes:
- 🌾 **PM Kisan Samman Nidhi** (Agriculture)
- 🏥 **Ayushman Bharat** (Healthcare)
- 🏠 **PM Awas Yojana** (Housing)
- ⛽ **PM Ujjwala Yojana** (Energy/LPG)
- 🏦 **PM Jan Dhan Yojana** (Financial Inclusion)
- 🌾 **PM Fasal Bima Yojana** (Crop Insurance)
- 🍚 **Ration Card Services** (Food Security)

## 💡 Key Features
1. **Authentic Dialects:** Uses rural linguistic nuances (e.g., *बा/बाटे* in Bhojpuri, *আছিল/কৰিব* in Assamese) rather than formal textbook translation.
2. **Intent-Driven:** Tagged with specific user intents (`APPLY_SCHEME`, `CHECK_ELIGIBILITY`, `GET_DOCUMENTS`, `KNOW_SCHEME`).
3. **Adaptive Feedback Loop:** Fully compatible with the **Adaption API**. The dataset is designed to grow and refine based on real user interactions (Thumbs Up / Thumbs Down).

## 🛠️ Data Structure
Each JSONL record contains:
```json
{
  "language": "bhojpuri",
  "domain": "agriculture",
  "intent": "CHECK_ELIGIBILITY",
  "scheme": "PM_KISAN",
  "query": "का हम पीएम किसान योजना खातिर फॉर्म भर सकेनी?",
  "response": "हाँ बिल्कुल! अगर रउआ लगे खुद के खेती वाला जमीन बा...",
  "feedback": "correct",
  "source": "gemini_synthetic"
}
```

## 🚀 How we built it
1. **Synthetic Generation:** We leveraged **Vertex AI (Gemini 2.5 Flash)** with strict dialect guidelines to generate realistic queries a rural citizen might ask.
2. **Quality Control:** Handled rate-limits dynamically and ensured responses were detailed (3-5 sentences with practical advice).
3. **Adaption Platform Sync:** Every single pair was pushed to the Adaption platform to seed the AI Agent's memory.

## 🏆 Hackathon Details
- **Team/Creator:** Afuu-coder
- **Problem Statement:** Low Resource Language AI Agent + Adaptive Data + Evaluation Pipeline

## 🙏 Credits & Acknowledgements
- **Adaption**: Special thanks to Adaption for providing the **Adaptive Data** platform. This project heavily relies on the Adaption API for real-time dataset ingestion, evaluation, and user feedback loop processing to continuously improve the agent's performance in low-resource languages.

---
*Built with ❤️ for rural India.*
