from app.components.loader import load_files, create_chunks
from app.components.vector_store import create_save_vector_store

from app.common.logger import get_logger
from app.common.custom_exception import CustomException


logger = get_logger(__name__)


def process_store_pdf():
    try:
        logger.info("Creating vectorstore.")

        raw_documents = load_files()

        chunks = create_chunks(documents=raw_documents)

        create_save_vector_store(chunks)
    except Exception as e:
        err_msg = CustomException("Failed to process the files", original_error=e)
        logger.error(str(err_msg))

        raise err_msg


if __name__ == "__main__":
    process_store_pdf()
