# README

## Prompt Chain Flow Diagram
```
flowchart TB
    A((User Input\\Course Title + Description)):::input --> B{Chain 1\\Generate Outline}:::chain
    B --> C([Outline Output]):::output
    C --> D{Chain 2\\Generate Lessons}:::chain
    D --> E([Detailed Lessons Output]):::output
    E --> F{Optional Chain 3\\Refinement}:::chain
    F --> G([Refined Lessons Output]):::output

    classDef input fill:#FFEDD5,stroke:#333,stroke-width:1px,color:#000
    classDef chain fill:#DBEAFE,stroke:#333,stroke-width:1px,color:#000
    classDef output fill:#DCFCE7,stroke:#333,stroke-width:1px,color:#000
```

## How to Use the Streaming Endpoints

1. **Run the App**  
   ```bash
   uvicorn fastapi_app:app --reload
   ```

2. **Stream Outline**  
   - **Request** (POST):  
     ```
     http://localhost:8000/stream_outline
     ```
   - **Body** (JSON):
     ```json
     {
       "title": "Introduction to Robotics",
       "description": "Explore the basics of robotics, from hardware design to control algorithms..."
     }
     ```
   - **Response**:  
     Returns an **SSE** (Server-Sent Events) stream. For each node result, you’ll receive an event like:
     ```
     data: {"outline": "1. Overview of Robotics\n2. Robot Hardware\n..."}
     ```
   - **Session ID**:  
     Yielded as an event `"session_id": session_id`.
   - After streaming completes, the final outline is stored in `SESSIONS[session_id]["outline"]`.

3. **Stream Lessons**  
   - **Request** (GET):  
     ```
     http://localhost:8000/stream_lessons/{session_id}
     ```
   - **Response**:  
     An **SSE** stream with one or more events containing `"lessons": "..."`
     ```json
     data: {"lessons": "..."}
     ```
   - The final lessons text is stored in `SESSIONS[session_id]["lessons"]`.

4. **Stream Refinement**  
   - **Request** (POST):  
     ```
     http://localhost:8000/stream_refine_lessons
     ```
   - **Body** (JSON):
     ```json
     {
       "session_id": "<the-session-id-from-above>",
       "feedback": "Please include more hands-on activities for module 2."
     }
     ```
   - **Response**:  
     An **SSE** stream with `"refined_lessons": "..."`
     ```
     data: {"refined_lessons": "..."}
     ```
   - The final refined lessons text is stored in `SESSIONS[session_id]["lessons"]`.