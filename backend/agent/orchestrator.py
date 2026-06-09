"""
Asteria Agent Orchestrator — The Brain of the AI Agent
Implements ReAct (Reasoning + Acting) loop for true autonomous behavior
"""
import os
import json
import uuid
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv
import tempfile
from .tools import TOOL_REGISTRY, list_all_schemes, scheme_lookup

load_dotenv(override=True)

# Support for Hugging Face Spaces: inject GCP credentials from Secret
if "GCP_CREDENTIALS_JSON" in os.environ:
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        f.write(os.environ["GCP_CREDENTIALS_JSON"])
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name

client = genai.Client(vertexai=True, project="asteria-497909", location="us-central1")

# ─── Intent Types ─────────────────────────────────────────────────────────────
INTENTS = {
    "APPLY_SCHEME": "User wants to apply for a scheme — guide step by step",
    "CHECK_ELIGIBILITY": "User wants to know if they qualify for a scheme",
    "GET_DOCUMENTS": "User wants the document checklist for a scheme",
    "KNOW_SCHEME": "User wants general info about a scheme",
    "LIST_SCHEMES": "User wants to see all available schemes",
    "COMPLAINT": "User has a complaint or problem with a scheme",
    "GENERAL_QA": "General question about government services",
    "GREETING": "User is greeting or starting conversation"
}

# ─── Scheme name to key mapping ───────────────────────────────────────────────
SCHEME_ALIASES = {
    # English aliases
    "pm kisan": "PM_KISAN", "kisan": "PM_KISAN", "pmkisan": "PM_KISAN",
    "ayushman": "AYUSHMAN_BHARAT", "pmjay": "AYUSHMAN_BHARAT", "health": "AYUSHMAN_BHARAT",
    "awas": "PM_AWAS", "housing": "PM_AWAS", "ghar": "PM_AWAS", "makaan": "PM_AWAS",
    "ujjwala": "UJJWALA", "lpg": "UJJWALA", "gas": "UJJWALA",
    "jan dhan": "JAN_DHAN", "jandhan": "JAN_DHAN", "bank account": "JAN_DHAN",
    "fasal bima": "FASAL_BIMA", "crop insurance": "FASAL_BIMA", "fasal": "FASAL_BIMA",
    "ration": "RATION_CARD", "rashan": "RATION_CARD", "ration card": "RATION_CARD",
    # Bhojpuri aliases
    "किसान": "PM_KISAN", "धान": "PM_KISAN",
    "घर": "PM_AWAS", "मकान": "PM_AWAS",
    "राशन": "RATION_CARD", "अनाज": "RATION_CARD",
    "इलाज": "AYUSHMAN_BHARAT", "दवाई": "AYUSHMAN_BHARAT",
    # Assamese aliases
    "কৃষক": "PM_KISAN", "ধান": "PM_KISAN",
    "ঘৰ": "PM_AWAS", "মাটি": "PM_AWAS",
    "ৰেচন": "RATION_CARD",
    "চিকিৎসা": "AYUSHMAN_BHARAT",
}


class AsteriaAgent:
    def __init__(self):
        self.sessions = {}  # In-memory session storage

    def get_or_create_session(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "language": "bhojpuri",
                "history": [],
                "user_profile": {},
                "current_scheme": None,
                "current_step": 1,
                "intent": None,
                "turn_count": 0
            }
        return self.sessions[session_id]

    def detect_scheme(self, text: str) -> str | None:
        """Detect which scheme the user is asking about"""
        text_lower = text.lower()
        for alias, scheme_key in SCHEME_ALIASES.items():
            if alias.lower() in text_lower:
                return scheme_key
        return None

    async def detect_intent_and_plan(self, user_message: str, session: dict) -> dict:
        """
        Step 1 of ReAct: THINK — Detect intent and plan actions
        Returns: {intent, scheme, tools_to_call, reasoning}
        """
        language = session["language"]
        lang_name = "Bhojpuri" if language == "bhojpuri" else "Assamese"
        history_text = "\n".join([
            f"User: {h['user']}\nAgent: {h['agent'][:100]}..."
            for h in session["history"][-3:]  # Last 3 turns
        ])
        available_schemes = [k for k in ["PM_KISAN", "AYUSHMAN_BHARAT", "PM_AWAS", "UJJWALA", "JAN_DHAN", "FASAL_BIMA", "RATION_CARD"]]

        plan_prompt = f"""You are the planning brain of Asteria — an AI agent helping rural Indian citizens access government schemes. 
The user speaks {lang_name}.

Recent conversation:
{history_text or "No history yet"}

User's current message: "{user_message}"

Available government schemes: {available_schemes}

Analyze and return ONLY a JSON object with:
- "intent": one of {list(INTENTS.keys())}
- "scheme": the scheme key if mentioned (null if none detected)  
- "reasoning": 1 sentence explaining what the user wants
- "tools_to_call": list of tools to use (from: scheme_lookup, check_eligibility, get_document_list, get_form_guide, list_all_schemes, search_schemes_by_tags)
- "needs_more_info": list of info needed from user (empty if we have enough)
- "form_step": which form step to show (1 if starting, null if not applying)

Examples:
- "PM Kisan mein apply karna hai" → intent=APPLY_SCHEME, scheme=PM_KISAN, tools=[check_eligibility, get_document_list, get_form_guide]
- "Ka PM Kisan ke layi eligible hain?" → intent=CHECK_ELIGIBILITY, scheme=PM_KISAN, tools=[check_eligibility]
- "Kaunse scheme hain?" → intent=LIST_SCHEMES, tools=[list_all_schemes]
- "Hello" → intent=GREETING, tools=[]

Return ONLY JSON (no markdown):"""

        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=plan_prompt
            )
            text = response.text.strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            plan = json.loads(text)

            # Also try direct scheme detection as fallback
            if not plan.get("scheme"):
                detected = self.detect_scheme(user_message)
                if detected:
                    plan["scheme"] = detected

            return plan
        except Exception as e:
            # Fallback plan
            detected_scheme = self.detect_scheme(user_message)
            return {
                "intent": "GENERAL_QA",
                "scheme": detected_scheme,
                "reasoning": "Could not parse intent, defaulting to general QA",
                "tools_to_call": ["scheme_lookup"] if detected_scheme else [],
                "needs_more_info": [],
                "form_step": None
            }

    def execute_tools(self, plan: dict, session: dict) -> dict:
        """
        Step 2 of ReAct: ACT — Execute the planned tools
        Returns tool results
        """
        results = {}
        language = session["language"]
        scheme_key = plan.get("scheme") or session.get("current_scheme")
        user_profile = session.get("user_profile", {})

        for tool_name in plan.get("tools_to_call", []):
            if tool_name not in TOOL_REGISTRY:
                continue
            try:
                tool_fn = TOOL_REGISTRY[tool_name]
                if tool_name == "scheme_lookup":
                    results[tool_name] = tool_fn(scheme_key, language) if scheme_key else {"found": False}
                elif tool_name == "check_eligibility":
                    results[tool_name] = tool_fn(scheme_key, user_profile, language) if scheme_key else {"found": False}
                elif tool_name == "get_document_list":
                    results[tool_name] = tool_fn(scheme_key, language) if scheme_key else {"found": False}
                elif tool_name == "get_form_guide":
                    step = plan.get("form_step") or session.get("current_step", 1)
                    results[tool_name] = tool_fn(scheme_key, step, language) if scheme_key else {"found": False}
                elif tool_name == "list_all_schemes":
                    results[tool_name] = tool_fn(language)
                elif tool_name == "search_schemes_by_tags":
                    # Extract keywords from user message
                    results[tool_name] = tool_fn(["farmer", "health", "house"], language)
            except Exception as e:
                results[tool_name] = {"error": str(e)}

        return results

    async def synthesize_response(
        self,
        user_message: str,
        plan: dict,
        tool_results: dict,
        session: dict
    ) -> str:
        """
        Step 3 of ReAct: OBSERVE + RESPOND — Generate final response
        """
        language = session["language"]
        lang_name = "Bhojpuri" if language == "bhojpuri" else "Assamese"
        intent = plan.get("intent", "GENERAL_QA")

        # Build context from tool results
        tool_context = json.dumps(tool_results, ensure_ascii=False, indent=2)

        history_text = "\n".join([
            f"User: {h['user']}\nAsteria: {h['agent']}"
            for h in session["history"][-2:]
        ])

        system_prompt = f"""You are Asteria — a warm, helpful AI agent that helps rural Indian citizens access government welfare schemes. 

CRITICAL RULES:
1. ALWAYS respond in {lang_name} language — NOT Hindi, NOT English (except for scheme names/technical terms)
2. Use simple, conversational language that a village person can understand
3. Be warm and respectful — use "आप" (Bhojpuri) or "আপুনি" (Assamese)
4. For APPLY_SCHEME intent — give step-by-step guidance, one step at a time
5. Always mention the helpline number at the end
6. Keep responses concise — max 4-5 sentences
7. If user needs documents — list them clearly with numbers

LANGUAGE RULES for {lang_name}:
{"- Use Bhojpuri: हऊ, बाटे, करीं, जाईं, मिलिही, बढ़ियाँ" if language == "bhojpuri" else "- Use Assamese: আছে, কৰক, যাওক, পাব, ভাল"}
- Do NOT use formal Hindi like "आपको", "करना है", "मिलेगा"
- {"Bhojpuri ending: बा, हऊ, बाटे, रहे, मिलिही" if language == "bhojpuri" else "Assamese ending: আছে, হ'ব, পাব, কৰিব"}

Intent being handled: {intent}
Tool results: {tool_context}

Previous conversation:
{history_text}

User just said: "{user_message}"

Respond naturally in {lang_name}:"""

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt
        )
        return response.text.strip()

    async def chat(
        self,
        user_message: str,
        session_id: str,
        language: str = "bhojpuri"
    ) -> dict:
        """
        Main entry point — Full ReAct loop
        Returns complete response with reasoning trace
        """
        session = self.get_or_create_session(session_id)
        session["language"] = language
        session["turn_count"] += 1

        reasoning_trace = []

        # ── THINK: Detect intent and plan ──────────────────────────────────
        reasoning_trace.append("🧠 Analyzing intent...")
        plan = await self.detect_intent_and_plan(user_message, session)
        reasoning_trace.append(f"📌 Intent: {plan.get('intent')} | Scheme: {plan.get('scheme')} | Reason: {plan.get('reasoning')}")

        # Update session state
        if plan.get("scheme"):
            session["current_scheme"] = plan["scheme"]
        if plan.get("form_step"):
            session["current_step"] = plan["form_step"]

        # ── ACT: Execute tools ─────────────────────────────────────────────
        if plan.get("tools_to_call"):
            reasoning_trace.append(f"🔧 Using tools: {plan['tools_to_call']}")
            tool_results = self.execute_tools(plan, session)
            reasoning_trace.append(f"✅ Tools executed successfully")
        else:
            tool_results = {}

        # ── RESPOND: Synthesize response ───────────────────────────────────
        reasoning_trace.append("✍️ Generating response...")
        response = await self.synthesize_response(user_message, plan, tool_results, session)

        # Update history
        session["history"].append({
            "user": user_message,
            "agent": response,
            "intent": plan.get("intent"),
            "scheme": plan.get("scheme"),
            "tools_used": plan.get("tools_to_call", [])
        })

        # Get scheme data for evaluation
        scheme_data = None
        if session.get("current_scheme") and session["current_scheme"] in ["PM_KISAN", "AYUSHMAN_BHARAT", "PM_AWAS", "UJJWALA", "JAN_DHAN", "FASAL_BIMA", "RATION_CARD"]:
            scheme_result = tool_results.get("scheme_lookup", {})
            if scheme_result.get("found"):
                scheme_data = scheme_result.get("raw")

        return {
            "response": response,
            "session_id": session_id,
            "intent": plan.get("intent"),
            "scheme": session.get("current_scheme"),
            "reasoning_trace": reasoning_trace,
            "tools_used": plan.get("tools_to_call", []),
            "needs_more_info": plan.get("needs_more_info", []),
            "current_step": session.get("current_step"),
            "scheme_data": scheme_data,
            "turn_count": session["turn_count"]
        }

    def advance_step(self, session_id: str) -> int:
        """Advance to next form step"""
        session = self.get_or_create_session(session_id)
        session["current_step"] = session.get("current_step", 1) + 1
        return session["current_step"]

    def update_profile(self, session_id: str, profile_data: dict):
        """Update user profile info collected during conversation"""
        session = self.get_or_create_session(session_id)
        session["user_profile"].update(profile_data)


# Singleton
asteria_agent = AsteriaAgent()
