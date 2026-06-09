"""
Agent Tools — The functions that make Asteria a TRUE AI Agent
(not just a chatbot)
"""
import json
import os
from typing import Optional

# Load schemes database
SCHEMES_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "schemes_db.json")

def _load_schemes() -> dict:
    with open(SCHEMES_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

SCHEMES = _load_schemes()

# ─── TOOL 1: Scheme Lookup ───────────────────────────────────────────────────

def scheme_lookup(scheme_key: str, language: str = "bhojpuri") -> dict:
    """
    Look up a government scheme by key.
    Returns all scheme info in the requested language.
    """
    if scheme_key not in SCHEMES:
        return {"found": False, "message": f"Scheme '{scheme_key}' not found"}

    scheme = SCHEMES[scheme_key]
    lang = language.lower()

    return {
        "found": True,
        "scheme_key": scheme_key,
        "name": scheme.get(f"{lang}_name") or scheme["full_name"],
        "domain": scheme["domain"],
        "benefit": scheme.get(f"benefit_{lang}") or scheme["benefit"],
        "helpline": scheme["helpline"],
        "website": scheme["website"],
        "raw": scheme
    }


def search_schemes_by_tags(tags: list, language: str = "bhojpuri") -> list:
    """Search schemes by keywords/tags"""
    results = []
    tags_lower = [t.lower() for t in tags]

    for key, scheme in SCHEMES.items():
        scheme_tags = scheme.get("tags", [])
        if any(tag in scheme_tags for tag in tags_lower):
            lang = language.lower()
            results.append({
                "scheme_key": key,
                "name": scheme.get(f"{lang}_name") or scheme["full_name"],
                "domain": scheme["domain"],
                "benefit": scheme.get(f"benefit_{lang}") or scheme["benefit"]
            })

    return results


# ─── TOOL 2: Eligibility Checker ─────────────────────────────────────────────

def check_eligibility(scheme_key: str, user_profile: dict, language: str = "bhojpuri") -> dict:
    """
    Check if a user is eligible for a scheme.
    Returns eligibility status + what's missing.
    """
    if scheme_key not in SCHEMES:
        return {"eligible": None, "reason": "Scheme not found"}

    scheme = SCHEMES[scheme_key]
    eligibility = scheme.get("eligibility", {})
    lang = language.lower()

    # Get eligibility text in the right language
    elig_text = scheme.get(f"eligibility_{lang}") or str(eligibility)

    # Check based on what user told us
    missing = []
    notes = []

    # Check common requirements
    if "bank_account" in str(eligibility) and not user_profile.get("has_bank_account"):
        missing.append("bank_account")
    if "land_ownership" in str(eligibility) and user_profile.get("has_land") is None:
        missing.append("land_ownership_confirmation")
    if "gender" in eligibility:
        gender_req = eligibility["gender"].lower()
        if "women" in gender_req and user_profile.get("gender", "").lower() not in ["female", "woman", "mahila", "lady"]:
            notes.append("This scheme is only for women")

    # If we don't have enough info, ask
    if len(missing) > 0:
        questions = {
            "bank_account": {
                "bhojpuri": "का आपके पास आधार से जुड़ल बैंक खाता बा?",
                "assamese": "আপোনাৰ আধাৰৰ সৈতে বেংক একাউণ্ট আছে নে?"
            },
            "land_ownership_confirmation": {
                "bhojpuri": "का रउरा के पास खेती के जमीन बा?",
                "assamese": "আপোনাৰ কৃষি মাটি আছে নে?"
            }
        }
        missing_questions = [
            questions.get(m, {}).get(lang, f"Please provide: {m}")
            for m in missing
        ]
        return {
            "eligible": "unknown",
            "missing_info": missing,
            "questions": missing_questions,
            "eligibility_criteria": elig_text
        }

    return {
        "eligible": True,
        "eligibility_criteria": elig_text,
        "notes": notes,
        "message": "User appears eligible based on provided information"
    }


# ─── TOOL 3: Document List ────────────────────────────────────────────────────

def get_document_list(scheme_key: str, language: str = "bhojpuri") -> dict:
    """
    Get the required document checklist for a scheme.
    Returns documents in the requested language.
    """
    if scheme_key not in SCHEMES:
        return {"found": False, "documents": []}

    scheme = SCHEMES[scheme_key]
    lang = language.lower()

    docs = scheme.get(f"documents_{lang}") or scheme.get("documents", [])

    return {
        "found": True,
        "scheme_key": scheme_key,
        "scheme_name": scheme.get(f"{lang}_name") or scheme["full_name"],
        "documents": docs,
        "total": len(docs),
        "tip_bhojpuri": "सभी कागज के फोटोकॉपी और असली दोनों रखव",
        "tip_assamese": "সকলো কাগজৰ ফটোকপি আৰু মূলটো দুয়োটাকে ৰাখক"
    }


# ─── TOOL 4: Step-by-Step Form Guide ─────────────────────────────────────────

def get_form_guide(scheme_key: str, step: int = 1, language: str = "bhojpuri") -> dict:
    """
    Get step-by-step form guidance for applying to a scheme.
    Returns one step at a time for guided experience.
    """
    if scheme_key not in SCHEMES:
        return {"found": False}

    scheme = SCHEMES[scheme_key]
    lang = language.lower()

    steps = scheme.get(f"apply_steps_{lang}") or scheme.get("apply_steps", [])
    total_steps = len(steps)

    if step < 1 or step > total_steps:
        return {
            "found": True,
            "completed": True,
            "message_bhojpuri": f"बधाई! {scheme.get('bhojpuri_name', scheme['full_name'])} के लिए आवेदन पूरा भइल!",
            "message_assamese": f"অভিনন্দন! {scheme.get('assamese_name', scheme['full_name'])}ৰ বাবে আবেদন সম্পূৰ্ণ হ'ল!",
            "total_steps": total_steps,
            "helpline": scheme["helpline"],
            "website": scheme["website"]
        }

    current_step = steps[step - 1]
    next_step = steps[step] if step < total_steps else None

    return {
        "found": True,
        "completed": False,
        "scheme_key": scheme_key,
        "scheme_name": scheme.get(f"{lang}_name") or scheme["full_name"],
        "current_step": step,
        "total_steps": total_steps,
        "step_text": current_step,
        "next_step_preview": next_step,
        "progress_percent": int((step / total_steps) * 100),
        "helpline": scheme["helpline"],
        "website": scheme["website"]
    }


# ─── TOOL 5: List All Schemes ─────────────────────────────────────────────────

def list_all_schemes(language: str = "bhojpuri", domain: str = None) -> list:
    """List all available schemes, optionally filtered by domain"""
    lang = language.lower()
    results = []

    for key, scheme in SCHEMES.items():
        if domain and scheme["domain"] != domain:
            continue
        results.append({
            "scheme_key": key,
            "name": scheme.get(f"{lang}_name") or scheme["full_name"],
            "domain": scheme["domain"],
            "benefit": scheme.get(f"benefit_{lang}") or scheme["benefit"],
            "helpline": scheme["helpline"]
        })

    return results


# Tool registry for the agent
TOOL_REGISTRY = {
    "scheme_lookup": scheme_lookup,
    "check_eligibility": check_eligibility,
    "get_document_list": get_document_list,
    "get_form_guide": get_form_guide,
    "search_schemes_by_tags": search_schemes_by_tags,
    "list_all_schemes": list_all_schemes,
}
