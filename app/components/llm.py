from langchain_groq import ChatGroq
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

from app.config.config import GROQ_API_KEY, GROQ_LLM_MODEL

logger = get_logger(__name__)


def load_llm():
    """
    Initializes and returns Groq Chat model.
    """
    try:
        if not GROQ_API_KEY:
            raise CustomException(
                "Hugging Face API token is missing. Check your environment configuration."
            )

        logger.info(f"Initializing Groq Inference Core using model: {GROQ_LLM_MODEL}")

        llm = ChatGroq(
            model=GROQ_LLM_MODEL,
            temperature=0.2,
            api_key=GROQ_API_KEY,
        )

        logger.info("Successfully established connection to the LLM endpoint.")
        return llm
    except Exception as e:
        err_msg = CustomException(
            "An error occurred while loading the chat model from Hugging Face.",
            original_error=e,
        )
        logger.error(str(err_msg))
        raise err_msg
