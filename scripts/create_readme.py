"""
Dataset README Generator — for HuggingFace & Kaggle
Also creates the dataset/ folder structure
"""
import os
import json

DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

README_CONTENT = """---
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
- adaptive-data
- adaption
pretty_name: Asteria Bhojpuri & Assamese Civic Q&A
---

# Asteria — Bhojpuri & Assamese Civic Q&A Dataset

Built using **Adaptive Data by [Adaption](https://adaption.ai)** for the **AI Agents Hackathon 2026**.

## Overview

First-of-its-kind Q&A dataset covering Indian government schemes in:
- **Bhojpuri** (bho) — 50M+ speakers in Bihar, UP, Jharkhand
- **Assamese** (asm) — 15M+ speakers in Assam

## Schemes Covered

PM Kisan · Ayushman Bharat · PM Awas Yojana · Ujjwala Yojana · Jan Dhan · Fasal Bima · Ration Card

## Built With Adaptive Data (Adaption)

This dataset was ingested, adapted, evaluated, and exported using the 
**Adaptive Data platform by Adaption** (https://adaption.ai).

The dataset continuously improves through:
1. User feedback (✓ Correct / ✗ Wrong)  
2. Automatic evaluation (factual accuracy + language quality + helpfulness)
3. Live agent conversation collection

## Credits

**Adaptive Data by Adaption** — https://adaption.ai  
Built for AI Agents Hackathon 2026 by HackIndia
"""

with open(os.path.join(DATASET_DIR, "README.md"), "w", encoding="utf-8") as f:
    f.write(README_CONTENT)

print("✅ Dataset README created")
print(f"   Path: {DATASET_DIR}/README.md")
