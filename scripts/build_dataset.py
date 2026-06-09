"""
Smart Dataset Builder — 4-Source Strategy
==========================================
Source 1: ai4bharat/IndicQA (Assamese QA — HuggingFace se)
Source 2: ai4bharat/IndicTrans (Hindi→Bhojpuri translation base)
Source 3: Hand-crafted civic seed pairs (guaranteed quality)
Source 4: Gemini synthetic generation (fill the gaps)

Then: Push everything to Adaptive Data (Adaption platform)

Run: python scripts/build_dataset.py
"""

import os
import sys
import json
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from google import genai
client = genai.Client(vertexai=True, project="asteria-497909", location="us-central1")


# ═══════════════════════════════════════════════════════════════
# SOURCE 1: HuggingFace — ai4bharat/IndicQA (Assamese)
# ═══════════════════════════════════════════════════════════════

def fetch_indicqa_assamese(max_samples: int = 100) -> list:
    """
    Fetch Assamese Q&A pairs from ai4bharat/IndicQA dataset on HuggingFace.
    This is a real NLP benchmark dataset.
    Filter for civic/government relevant questions.
    """
    print("\n📥 SOURCE 1: Fetching ai4bharat/IndicQA (Assamese) from HuggingFace...")
    try:
        from datasets import load_dataset

        # Load the Assamese split
        ds = load_dataset("ai4bharat/IndicQA", "as", split="test", trust_remote_code=True)
        print(f"   Total IndicQA Assamese samples: {len(ds)}")

        civic_keywords = [
            # Assamese civic keywords
            "চৰকাৰ", "আঁচনি", "যোজনা", "কৃষি", "স্বাস্থ্য",
            "শিক্ষা", "পানী", "বিদ্যুৎ", "ৰাজ্য", "চৰকাৰী",
            "বেংক", "টকা", "সুবিধা", "আইন",
            # Also general knowledge (useful for civic QA base)
            "ভাৰত", "অসম", "সমাজ", "পৰিয়াল"
        ]

        civic_pairs = []
        all_pairs = []

        for item in ds:
            try:
                question = item.get("question", "")
                answers = item.get("answers", {})
                context = item.get("context", "")

                # Get answer text
                answer_texts = answers.get("text", []) if isinstance(answers, dict) else []
                if not answer_texts:
                    continue
                answer = answer_texts[0]

                if not question or not answer or len(answer) < 10:
                    continue

                pair = {
                    "language": "assamese",
                    "domain": "general_knowledge",
                    "intent": "KNOW_SCHEME",
                    "scheme": None,
                    "query": question,
                    "response": answer,
                    "context": context[:200] if context else "",
                    "feedback": "correct",
                    "source": "ai4bharat_IndicQA_HuggingFace"
                }

                # Check if civic-relevant
                is_civic = any(kw in question or kw in context for kw in civic_keywords)
                if is_civic:
                    pair["domain"] = "civic"
                    civic_pairs.append(pair)
                else:
                    all_pairs.append(pair)

            except Exception:
                continue

        # Prioritize civic pairs, then fill from general
        selected = civic_pairs[:max_samples]
        remaining = max_samples - len(selected)
        if remaining > 0:
            selected.extend(all_pairs[:remaining])

        print(f"   ✅ Civic-relevant: {len(civic_pairs)} | General: {len(all_pairs)}")
        print(f"   📦 Selected: {len(selected)} Assamese pairs")
        return selected

    except Exception as e:
        print(f"   ⚠️ IndicQA fetch failed: {e}")
        print("   → Will use Gemini generation as fallback")
        return []


# ═══════════════════════════════════════════════════════════════
# SOURCE 2: HuggingFace — Translate Bhojpuri Dataset
# ═══════════════════════════════════════════════════════════════

def fetch_bhojpuri_translation_data(max_samples: int = 50) -> list:
    """
    Fetch from 1rsh/translate-bhojpuri-hi-karya dataset.
    Use Bhojpuri text as seed for generating civic Q&A.
    """
    print("\n📥 SOURCE 2: Fetching Bhojpuri translation base from HuggingFace...")
    try:
        from datasets import load_dataset

        ds = load_dataset("1rsh/translate-bhojpuri-hi-karya", split="train", trust_remote_code=True)
        print(f"   Total Bhojpuri translation samples: {len(ds)}")

        # Extract Bhojpuri vocabulary/sentences as examples
        bhojpuri_samples = []
        for i, item in enumerate(ds):
            if i >= max_samples:
                break
            try:
                # Get Bhojpuri text
                bho_text = item.get("bhojpuri") or item.get("bho") or item.get("source") or ""
                hi_text = item.get("hindi") or item.get("hi") or item.get("target") or ""

                if bho_text and len(bho_text) > 10:
                    bhojpuri_samples.append({
                        "bhojpuri": bho_text,
                        "hindi": hi_text
                    })
            except Exception:
                continue

        print(f"   ✅ Got {len(bhojpuri_samples)} Bhojpuri text samples for vocabulary reference")
        return bhojpuri_samples

    except Exception as e:
        print(f"   ⚠️ Bhojpuri dataset fetch failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# SOURCE 3: Gemini Synthetic Generation (Main Bhojpuri Source)
# ═══════════════════════════════════════════════════════════════

SCHEME_INFO = {
    "PM_KISAN": {"domain": "agriculture", "benefit": "₹6000/year for farmers"},
    "AYUSHMAN_BHARAT": {"domain": "healthcare", "benefit": "₹5 lakh health insurance"},
    "PM_AWAS": {"domain": "housing", "benefit": "₹1.2 lakh for house construction"},
    "UJJWALA": {"domain": "energy", "benefit": "Free LPG connection for women"},
    "JAN_DHAN": {"domain": "finance", "benefit": "Zero-balance bank account"},
    "FASAL_BIMA": {"domain": "agriculture", "benefit": "Crop insurance"},
    "RATION_CARD": {"domain": "food", "benefit": "Subsidized food grains"},
}


async def generate_civic_pairs_gemini(
    scheme_key: str,
    language: str,
    count: int = 12,
    bhojpuri_vocab: list = None
) -> list:
    """Generate authentic civic Q&A pairs using Gemini"""

    scheme = SCHEME_INFO[scheme_key]
    lang_name = "Bhojpuri (भोजपुरी rural dialect)" if language == "bhojpuri" else "Assamese (অসমীয়া)"

    # Bhojpuri dialect guide with real examples
    dialect_guide = ""
    if language == "bhojpuri":
        dialect_guide = """
BHOJPURI DIALECT RULES (MUST FOLLOW):
- Use बा / बाटे (not है/हैं)
- Use होखे / होखेला (not होना/होता)
- Use मिलेला / मिलिही (not मिलेगा)
- Use जाईं / जाओ (not जाएं)
- Use चाही / चाहीं (not चाहिए)
- Use रउरा / रउआ (for आप)
- Use हऊ (for मैं)
- Use बानी / हईं (not हूं/हो)
- Use करीं / करव (not करें/करो)
- Use का (not क्या)
- Example: "PM Kisan में ka-ka documents चाही?" ✅
- WRONG: "PM Kisan में क्या दस्तावेज चाहिए?" ❌"""
    else:
        dialect_guide = """
ASSAMESE RULES (MUST FOLLOW):
- Use আছে, আছিল (not है/था)
- Use কৰক, কৰিব (polite forms)
- Use পাব, পাৰিব (will get/can)
- Use লাগিব, লাগে (need/needs)
- Use যাওক, যাব (go/will go)
- Use হ'ব, হৈছে (will be/has been)"""

    prompt = f"""Generate {count} realistic Q&A pairs in {lang_name} about {scheme_key} government scheme.

Scheme: {scheme_key}
Benefit: {scheme["benefit"]}
Domain: {scheme["domain"]}

{dialect_guide}

Generate questions that REAL rural Indian citizens would ask. Mix of:
- Basic: "What is this scheme?" / "What benefit do I get?"
- Eligibility: "Am I eligible?" / "Who can apply?"
- Documents: "What documents do I need?"
- Process: "How do I apply?" / "Where do I go?"
- Problems: "My application was rejected, what to do?"
- Status: "How do I check my application status?"
- Amounts: "When will I get the money?"

Return ONLY a valid JSON array:
[
  {{
    "query": "question in {lang_name}",
    "response": "detailed helpful answer in {lang_name} (3-5 sentences, practical advice)",
    "intent": "KNOW_SCHEME"
  }}
]

Intent options: KNOW_SCHEME, CHECK_ELIGIBILITY, GET_DOCUMENTS, APPLY_SCHEME, COMPLAINT, GENERAL_QA
Return ONLY JSON, no markdown, no explanation:"""

    try:
        import asyncio
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else parts[0]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        pairs = json.loads(text)
        enriched = []
        for p in pairs:
            if "query" in p and "response" in p and len(p["response"]) > 20:
                enriched.append({
                    "language": language,
                    "domain": scheme["domain"],
                    "intent": p.get("intent", "KNOW_SCHEME"),
                    "scheme": scheme_key,
                    "query": p["query"],
                    "response": p["response"],
                    "feedback": "correct",
                    "source": "gemini_synthetic"
                })
        return enriched

    except Exception as e:
        print(f"     ⚠️ Generation failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# SOURCE 4: Hand-crafted Seed (from generate_seed_data.py)
# ═══════════════════════════════════════════════════════════════

def load_existing_seed() -> list:
    """Load any existing hand-crafted seed pairs"""
    seed_files = [
        os.path.join(os.path.dirname(__file__), "..", "dataset", "bhojpuri_civic_qa.jsonl"),
        os.path.join(os.path.dirname(__file__), "..", "dataset", "assamese_civic_qa.jsonl"),
    ]
    pairs = []
    for path in seed_files:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        pairs.append(json.loads(line.strip()))
                    except Exception:
                        pass
    return pairs


# ═══════════════════════════════════════════════════════════════
# PUSH TO ADAPTION
# ═══════════════════════════════════════════════════════════════

async def push_all_to_adaption(pairs: list) -> int:
    """Push all pairs to Adaptive Data platform"""
    from adaption.client import adaption_client
    success = 0
    print(f"\n📤 Pushing {len(pairs)} pairs to Adaptive Data platform...")

    for i, pair in enumerate(pairs):
        try:
            result = await adaption_client.ingest_qa_pair(
                query=pair["query"],
                response=pair["response"],
                language=pair["language"],
                domain=pair.get("domain", "civic"),
                intent=pair.get("intent", "KNOW_SCHEME"),
                scheme=pair.get("scheme"),
                feedback=pair.get("feedback", "correct"),
                session_id=f"dataset_build_{pair.get('source', 'unknown')}"
            )
            if result.get("local"):
                success += 1

            if (i + 1) % 20 == 0:
                print(f"   → {i+1}/{len(pairs)} pushed...")
        except Exception as e:
            print(f"   ⚠️ Push error at {i}: {e}")

    return success


# ═══════════════════════════════════════════════════════════════
# MAIN BUILD PIPELINE
# ═══════════════════════════════════════════════════════════════

async def main():
    print("=" * 65)
    print("🌟 ASTERIA — Smart Dataset Builder")
    print("   Sources: HuggingFace + Gemini + Hand-crafted")
    print("=" * 65)

    all_pairs = []

    # ── Step 1: Load existing seed data ────────────────────────
    existing = load_existing_seed()
    if existing:
        print(f"\n✅ Existing seed pairs loaded: {len(existing)}")
        all_pairs.extend(existing)
    else:
        print("\n⚠️  No existing seed data. Run generate_seed_data.py first OR continuing...")

    # ── Step 2: HuggingFace — IndicQA Assamese ─────────────────
    indicqa_pairs = fetch_indicqa_assamese(max_samples=80)
    all_pairs.extend(indicqa_pairs)

    # ── Step 3: HuggingFace — Bhojpuri translation vocab ───────
    bho_vocab = fetch_bhojpuri_translation_data(max_samples=50)

    # ── Step 4: Gemini generation for all schemes ───────────────
    print("\n🤖 GEMINI GENERATION — Civic Q&A for all schemes...")
    schemes = list(SCHEME_INFO.keys())
    languages = ["bhojpuri", "assamese"]

    iterations = 6 # 6 iterations * 14 combos = 84 requests. 84 * 18 = 1512 pairs.
    for i in range(iterations):
        print(f"\n   --- Generation Batch {i+1}/{iterations} ---")
        for scheme in schemes:
            for lang in languages:
                print(f"   → {scheme} / {lang}...", end=" ", flush=True)
                pairs = await generate_civic_pairs_gemini(
                    scheme_key=scheme,
                    language=lang,
                    count=18,
                    bhojpuri_vocab=bho_vocab if lang == "bhojpuri" else None
                )
                all_pairs.extend(pairs)
                print(f"✓ +{len(pairs)} pairs")
                await asyncio.sleep(4.5)  # Strict rate limit for Vertex AI free tier

    # ── Step 5: Stats ───────────────────────────────────────────
    bho_pairs = [p for p in all_pairs if p["language"] == "bhojpuri"]
    asm_pairs = [p for p in all_pairs if p["language"] == "assamese"]

    print(f"\n{'='*65}")
    print(f"📊 DATASET SUMMARY")
    print(f"{'='*65}")
    print(f"   Total pairs     : {len(all_pairs)}")
    print(f"   Bhojpuri (bho)  : {len(bho_pairs)}")
    print(f"   Assamese (asm)  : {len(asm_pairs)}")
    print(f"\n   Sources breakdown:")

    from collections import Counter
    sources = Counter(p.get("source", "unknown") for p in all_pairs)
    for src, count in sources.items():
        print(f"   • {src}: {count}")

    # ── Step 6: Save locally ────────────────────────────────────
    output_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "bhojpuri_civic_qa.jsonl"), "w", encoding="utf-8") as f:
        for p in bho_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(os.path.join(output_dir, "assamese_civic_qa.jsonl"), "w", encoding="utf-8") as f:
        for p in asm_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # Combined file
    with open(os.path.join(output_dir, "combined_dataset.jsonl"), "w", encoding="utf-8") as f:
        for p in all_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"\n💾 Saved to dataset/")

    # ── Step 7: Push to Adaption ────────────────────────────────
    pushed = await push_all_to_adaption(all_pairs)
    print(f"   ✅ Pushed {pushed}/{len(all_pairs)} pairs to Adaptive Data")

    print(f"\n{'='*65}")
    print(f"🎉 DATASET BUILD COMPLETE!")
    print(f"   {len(all_pairs)} Q&A pairs ready")
    print(f"   Bhojpuri: {len(bho_pairs)} | Assamese: {len(asm_pairs)}")
    print(f"\nNext: python scripts/push_to_huggingface.py")
    print(f"{'='*65}")


if __name__ == "__main__":
    asyncio.run(main())
