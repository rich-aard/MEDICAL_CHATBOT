from langchain_huggingface import HuggingFaceEmbeddings

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

from app.config.config import HUGGINGFACE_EMBEDDING_MODEL

logger = get_logger(__name__)


def get_embedding_model():
    """
    Initializes and retrieves the configured Hugging Face text embedding model.
    """
    try:
        logger.info(f"Initializing the embedding model:{HUGGINGFACE_EMBEDDING_MODEL}")

        embedding_model = HuggingFaceEmbeddings(model_name=HUGGINGFACE_EMBEDDING_MODEL)

        logger.info(
            f"Successfully loaded {HUGGINGFACE_EMBEDDING_MODEL} from hugging face."
        )

        return embedding_model
    except Exception as e:
        err_msg = CustomException(
            "An error occurred while loading the embedding model from Hugging Face.",
            original_error=e,
        )
        logger.error(str(err_msg))
        raise err_msg
