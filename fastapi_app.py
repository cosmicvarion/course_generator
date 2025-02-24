"""
fastapi_app.py
Exposes SSE endpoints for course outline, lessons, and refinement,
using async LangGraph calls from langgraph_chains.py
"""
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uuid

load_dotenv()

# Import the async graphs from langgraph_chains.py
from langgraph_chains import (
    compiled_outline_graph,
    compiled_lessons_graph,
    compiled_refine_graph,
)

app = FastAPI()

# Simple in-memory session storage
SESSIONS = {}

# Models
class CourseInput(BaseModel):
    title: str
    description: str

class LessonsInput(BaseModel):
    session_id: str

class RefinementInput(BaseModel):
    session_id: str
    feedback: str

@app.post("/stream_outline")
async def stream_outline(course_input: CourseInput):
    """
    1) Create session
    2) Stream the generated outline via SSE
    3) Save final outline to session
    """
    
    word_count = len(course_input.description.split())
    if word_count > 200:
        raise HTTPException(status_code=400, detail=f"Description is too long ({word_count} words). Maximum allowed is 200.")
    
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "course_title": course_input.title,
        "course_description": course_input.description,
        "outline": None,
        "lessons": None,
    }

    async def event_generator():
        # Yield an SSE event containing the session_id
        first_event = {"session_id": session_id}
        yield f"data: {json.dumps(first_event)}\n\n"
        yield "\n"
        
        # Collect events from the compiled graph
        async for event in compiled_outline_graph.astream(
            {"title": course_input.title, "description": course_input.description},
            stream_mode="updates"
        ):
            event_dict = dict(event)
            
            # Convert each event to SSE format
            yield f"data: {json.dumps(event_dict)}\n\n"
            yield "\n"

            SESSIONS[session_id]["outline"] = event_dict["generate_outline"]["outline"]

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/stream_lessons/{session_id}")
async def stream_lessons(session_id: str):
    """
    Streams detailed lessons based on the stored outline.
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")

    outline = SESSIONS[session_id]["outline"]
    print("SESSIONS[session_id]", SESSIONS[session_id])
    print("outline", outline)
    if not outline:
        raise HTTPException(status_code=400, detail="No outline found for this session.")

    async def event_generator():
        async for event in compiled_lessons_graph.astream(
            {"outline": outline},
            stream_mode="updates"
        ):
            event_dict = dict(event)
            yield f"data: {json.dumps(event_dict)}\n\n"
            SESSIONS[session_id]["lessons"] = event_dict["generate_lessons"]["lessons"]

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/stream_refine_lessons")
async def stream_refine_lessons(ref_input: RefinementInput):
    """
    Streams refined lessons based on user feedback.
    """
    session_id = ref_input.session_id
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")

    lessons = SESSIONS[session_id]["lessons"]
    if not lessons:
        raise HTTPException(status_code=400, detail="No lessons found to refine.")

    async def event_generator():
        async for event in compiled_refine_graph.astream(
            {"lessons": lessons, "feedback": ref_input.feedback},
            stream_mode="updates"
        ):
            event_dict = dict(event)
            yield f"data: {json.dumps(event_dict)}\n\n"
            
            SESSIONS[session_id]["lessons"] = event_dict["refine_lessons"]["lessons"]

    return StreamingResponse(event_generator(), media_type="text/event-stream")
