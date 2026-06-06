from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.common.logger import get_logger
from app.common.custom_exception import CustomException
from app.components.retriever import create_rag_qa_chain

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """
    Handles application startup and shutdown events cleanly,
    bypassing deprecated on_event triggers.
    """
    try:
        logger.info("Server lifespan initializing. Setting up RAG engine...")
        fastapi_app.state.rag_chain = create_rag_qa_chain()
        logger.info("RAG Engine successfully cached into application state.")
    except Exception as e:
        logger.critical(f"Server failed to start up due to a fatal chain error: {e}")
        raise e

    yield

    # Everything after 'yield' runs when the server stops
    logger.info("Server lifespan shutting down. Cleaning up application state...")
    fastapi_app.state.rag_chain = None


app = FastAPI(title="AI Medical Chatbot", lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


chat_session_history = []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"messages": chat_session_history, "error": None}
    )


@app.post("/", response_class=HTMLResponse)
async def handle_chat_query(request: Request, prompt: str = Form(...)):
    error_context = None

    if not prompt.strip():
        return RedirectResponse(url="/", status_code=303)

    try:
        chat_session_history.append({"role": "user", "content": prompt})
        logger.info(f"Received question from frontend framework: '{prompt}'")

        current_chain = request.app.state.rag_chain
        if current_chain is None:
            raise CustomException("Retrieval generation service is uninitialized.")

        ai_response = current_chain.invoke(prompt)
        chat_session_history.append({"role": "assistant", "content": ai_response})

    except Exception as e:
        error_context = f"Failed to retrieve clean context validation metrics: {str(e)}"
        logger.error(f"Routing error detected: {error_context}")

        if chat_session_history and chat_session_history[-1]["role"] == "user":
            chat_session_history.pop()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"messages": chat_session_history, "error": error_context}
    )


@app.get("/clear")
async def clear():
    logger.info("Clearing active conversational memory records.")
    chat_session_history.clear()
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.app:app", host="127.0.0.1", port=8000, reload=True)
