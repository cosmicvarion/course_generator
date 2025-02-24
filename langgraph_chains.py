"""
langgraph_chains.py
Async prompt pipelines for outline, lessons, and refinement,
using LangGraph and streaming responses from OpenAI.
"""
import langchain_core.prompts as prompts
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from pydantic import BaseModel
from typing import Optional

# 1) Instantiate an LLM with streaming=True
llm = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True)

# -------------------------
# STATE MODELS
# -------------------------
class OutlineState(BaseModel):
    title: str
    description: str
    outline: Optional[str] = None

class LessonsState(BaseModel):
    outline: str
    lessons: Optional[str] = None

class RefineState(BaseModel):
    lessons: str
    feedback: str
    refined_lessons: Optional[str] = None

# -------------------------
# OUTLINE GENERATION
# -------------------------
outline_prompt = prompts.PromptTemplate.from_template(
    """
    You are an expert curriculum designer. 
    Given a course title and description, produce a clear, bullet-point course outline.

    Title: {title}
    Description: {description}

    Requirements:
    - Include multiple modules/sections
    - Briefly describe each module in 1-2 sentences
    - Return the outline in a well-structured list
    """
)

# Async function for outline generation node
async def generate_outline_async(state: OutlineState):
    """
    Receives {"title": ..., "description": ...} as input,
    invokes the LLM, and yields a dict with the generated outline.
    """
    # Build a streaming pipeline: prompt -> llm (no final parser).
    pipeline = outline_prompt | llm
    
    # We'll accumulate partial chunks into a growing string.
    partial_outline = ""
    
    # .astream(...) yields partial text chunks.
    async for chunk in pipeline.astream({"title": state.title, "description": state.description}):
        partial_outline += chunk.content
        
        # Each yield returns the updated OutlineState so far.
        yield OutlineState(
            title=state.title,
            description=state.description,
            outline=partial_outline
        )

# Build the outline graph
outline_graph = StateGraph(OutlineState)
outline_graph.add_node("generate_outline", generate_outline_async)
outline_graph.set_entry_point("generate_outline")
compiled_outline_graph = outline_graph.compile()


# -------------------------
# LESSONS GENERATION
# -------------------------
lessons_prompt = prompts.PromptTemplate.from_template(
    """
    You are an expert instructor. Given the course outline below, generate detailed lessons
    for each module. Include:
      1. A short overview
      2. Key objectives
      3. Lesson structure (lecture, activities, discussions)
      4. Recommended resources/references

    Outline:
    {outline}

    Return the lesson content in a structured format.
    """
)

async def generate_lessons_async(state: LessonsState):
    """
    Receives {"outline": ...} as input,
    invokes the LLM, and yields a dict with the generated lessons.
    """
    pipeline = lessons_prompt | llm
    partial_lessons = ""
    
    async for chunk in pipeline.astream({"outline": state.outline}):
        partial_lessons += chunk.content
        
        yield LessonsState(
            outline=state.outline,
            lessons=partial_lessons
        )

lessons_graph = StateGraph(LessonsState)
lessons_graph.add_node("generate_lessons", generate_lessons_async)
lessons_graph.set_entry_point("generate_lessons")
compiled_lessons_graph = lessons_graph.compile()


# -------------------------
# REFINEMENT
# -------------------------
refine_prompt = prompts.PromptTemplate.from_template(
    """
    You are a senior curriculum reviewer. Given the existing lessons and user feedback,
    refine or improve the lesson content. Be specific and provide a fully updated version.

    Lessons:
    {lessons}

    Feedback:
    {feedback}
    """
)

async def refine_lessons_async(state: RefineState):
    """
    Receives {"lessons": ..., "feedback": ...},
    invokes the LLM, and yields a dict with the refined lessons.
    """
    pipeline = refine_prompt | llm
    partial_refined = ""
    
    async for chunk in pipeline.astream({"lessons": state.lessons, "feedback": state.feedback}):
        partial_refined += chunk.content
        
        yield RefineState(
            lessons=state.lessons,
            feedback=state.feedback,
            refined_lessons=partial_refined
        )

refine_graph = StateGraph(RefineState)
refine_graph.add_node("refine_lessons", refine_lessons_async)
refine_graph.set_entry_point("refine_lessons")
compiled_refine_graph = refine_graph.compile()
