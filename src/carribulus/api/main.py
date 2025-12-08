from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from .models import ChatRequest, ChatResponse, ChatSession, Message
from .db import db
from .utils import generate_rolling_summary
from ..crew import Carribulus
import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "API is running. Go to /docs to test the chat endpoint via Swagger UI."}

MAX_RECENT_MESSAGES = 6

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # 1. Retrieve or Create Session
    if request.session_id:
        session_data = await db.get_session(request.session_id)
        if not session_data:
            # If ID provided but not found, create new
            session = ChatSession(session_id=request.session_id)
        else:
            session = ChatSession(**session_data)
    else:
        session = ChatSession()

    # 2. Add User Message
    user_msg = Message(role="user", content=request.message)
    session.recent_messages.append(user_msg)

    # 3. Construct Context for Agent
    # Combine Summary + Recent Messages
    recent_history_text = "\n".join([f"{m.role}: {m.content}" for m in session.recent_messages])
    full_context = f"Summary of past conversation:\n{session.summary}\n\nRecent conversation:\n{recent_history_text}"

    # 4. Initialize and run CrewAI Agent
    # The inputs expected by the crew tasks need to be aligned.
    # We'll pass 'topic' (the user message) and 'chat_history' (the context)
    crew_instance = Carribulus()
    inputs = {
        "topic": request.message,
        "chat_history": full_context,
        "current_date": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        # kickoff() returns a CrewOutput object, we want the raw string usually
        result = crew_instance.crew().kickoff(inputs=inputs)
        response_text = str(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

    # 5. Add Assistant Message
    assistant_msg = Message(role="assistant", content=response_text)
    session.recent_messages.append(assistant_msg)

    # 6. Update Rolling Summary if needed
    if len(session.recent_messages) > MAX_RECENT_MESSAGES:
        # Take the oldest half of messages to summarize
        messages_to_summarize = session.recent_messages[:MAX_RECENT_MESSAGES//2]
        messages_to_keep = session.recent_messages[MAX_RECENT_MESSAGES//2:]
        
        new_summary = generate_rolling_summary(session.summary, messages_to_summarize)
        
        session.summary = new_summary
        session.recent_messages = messages_to_keep

    session.updated_at = datetime.datetime.now(datetime.timezone.utc)

    # 7. Save Session
    await db.save_session(session.model_dump())

    return ChatResponse(
        session_id=session.session_id,
        response=response_text,
        history_summary=session.summary
    )

if __name__ == "__main__":
    import uvicorn
    # RUN using uvicorn src.carribulus.api.main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
