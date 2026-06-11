"""
Asteria FastAPI Backend — Main Application
Full AI Agent API with Adaptive Data integration
"""
import os
import uuid
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from agent.orchestrator import asteria_agent
from adaption.client import adaption_client
from adaption.evaluator import evaluation_agent
from adaption.exporter import export_to_huggingface

# ─── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Asteria AI Agent API",
    description="AI Agent for low-resource Indian languages (Bhojpuri + Assamese)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# ─── Request/Response Models ──────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: str = "bhojpuri"  # "bhojpuri" or "assamese"


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    feedback: str  # "correct" or "wrong"
    query: Optional[str] = None
    response: Optional[str] = None
    language: Optional[str] = "bhojpuri"
    domain: Optional[str] = "civic"
    intent: Optional[str] = "GENERAL_QA"
    scheme: Optional[str] = None


class StepRequest(BaseModel):
    session_id: str


# ─── Background Tasks ─────────────────────────────────────────────────────────
async def log_to_adaption(
    query: str,
    response: str,
    language: str,
    domain: str,
    intent: str,
    scheme: str,
    session_id: str,
    scheme_data: dict = None
):
    """Background task: evaluate response + push to Adaption"""
    try:
        # Run evaluation
        eval_scores = await evaluation_agent.evaluate_response(
            query=query,
            response=response,
            language=language,
            domain=domain,
            scheme=scheme,
            scheme_data=scheme_data
        )

        # Push to Adaption
        await adaption_client.ingest_qa_pair(
            query=query,
            response=response,
            language=language,
            domain=domain,
            intent=intent,
            scheme=scheme,
            eval_scores=eval_scores,
            session_id=session_id
        )
    except Exception as e:
        print(f"[Adaption background task error]: {e}")


# ─── Routes ───────────────────────────────────────────────────────────────────

# @app.get("/")
# async def serve_frontend():
#     \"\"\"Serve the frontend\"\"\"
#     frontend_path = os.path.join(FRONTEND_DIR, "index.html")
#     if os.path.exists(frontend_path):
#         return FileResponse(frontend_path)
#     return {"message": "Asteria API is running!", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Asteria AI Agent",
        "version": "1.0.0",
        "languages": ["bhojpuri", "assamese"],
        "adaption_key_set": bool(os.getenv("ADAPTION_API_KEY")),
        "gemini_key_set": bool(os.getenv("GEMINI_API_KEY"))
    }


@app.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Main chat endpoint — Full ReAct agent loop
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Run the agent
        result = await asteria_agent.chat(
            user_message=request.message,
            session_id=session_id,
            language=request.language
        )

        # Generate a unique message ID
        message_id = str(uuid.uuid4())

        # Background: Evaluate + Push to Adaption (non-blocking)
        background_tasks.add_task(
            log_to_adaption,
            query=request.message,
            response=result["response"],
            language=request.language,
            domain="civic_schemes",
            intent=result.get("intent", "GENERAL_QA"),
            scheme=result.get("scheme", ""),
            session_id=session_id,
            scheme_data=result.get("scheme_data")
        )

        return {
            "response": result["response"],
            "session_id": session_id,
            "message_id": message_id,
            "intent": result.get("intent"),
            "scheme": result.get("scheme"),
            "reasoning_trace": result.get("reasoning_trace", []),
            "tools_used": result.get("tools_used", []),
            "current_step": result.get("current_step"),
            "turn_count": result.get("turn_count", 1)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """
    Submit user feedback on a response (correct / wrong)
    This drives the self-improving dataset
    """
    if request.feedback not in ["correct", "wrong"]:
        raise HTTPException(status_code=400, detail="Feedback must be 'correct' or 'wrong'")

    # Update in Adaption
    background_tasks.add_task(
        adaption_client.update_feedback,
        session_id=request.session_id,
        message_id=request.message_id,
        feedback=request.feedback
    )

    # If wrong feedback + we have the Q&A pair, log it with wrong tag
    if request.query and request.response:
        background_tasks.add_task(
            adaption_client.ingest_qa_pair,
            query=request.query,
            response=request.response,
            language=request.language or "bhojpuri",
            domain=request.domain or "civic",
            intent=request.intent or "GENERAL_QA",
            scheme=request.scheme,
            feedback=request.feedback,
            session_id=request.session_id
        )

    return {
        "status": "success",
        "message": "Feedback submitted — dataset improving! 🎯",
        "feedback": request.feedback
    }


@app.post("/next-step")
async def next_step(request: StepRequest):
    """Advance to the next form step in guided application flow"""
    new_step = asteria_agent.advance_step(request.session_id)
    return {"session_id": request.session_id, "current_step": new_step}


@app.get("/schemes")
async def get_all_schemes(language: str = "bhojpuri"):
    """Get list of all available government schemes"""
    from agent.tools import list_all_schemes
    schemes = list_all_schemes(language)
    return {"schemes": schemes, "total": len(schemes), "language": language}


@app.get("/schemes/{scheme_key}")
async def get_scheme(scheme_key: str, language: str = "bhojpuri"):
    """Get detailed info about a specific scheme"""
    from agent.tools import scheme_lookup
    result = scheme_lookup(scheme_key, language)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail=f"Scheme '{scheme_key}' not found")
    return result


@app.get("/stats")
async def get_stats():
    """Get dataset statistics — shows Adaption integration progress"""
    stats = adaption_client.get_local_stats()
    return {
        "dataset_stats": stats,
        "platform": "Adaptive Data by Adaption",
        "project": "AI Agents Hackathon 2026",
        "languages": ["Bhojpuri (bho)", "Assamese (asm)"],
        "huggingface": f"https://huggingface.co/datasets/Afuu-coder/asteria-bhojpuri-assamese-civic-qa"
    }


@app.post("/export/huggingface")
async def export_dataset():
    """Export collected dataset to HuggingFace Hub"""
    result = export_to_huggingface()
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session history"""
    session = asteria_agent.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "language": session.get("language"),
        "turn_count": session.get("turn_count", 0),
        "current_scheme": session.get("current_scheme"),
        "history_count": len(session.get("history", []))
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
