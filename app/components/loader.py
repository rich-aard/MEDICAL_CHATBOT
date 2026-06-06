import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

from app.config.config import DATA_PATH, CHUNK_SIZE, CHUNK_OVERLAP

logger = get_logger(__name__)


def load_files() -> List[Document]:
    """
    Loads documents from the data path.
    """
    try:
        if not os.path.exists(DATA_PATH):
            raise CustomException(f"Data Path does not exist: {DATA_PATH}")
        logger.info(f"Initializing Document Loader for directory: {DATA_PATH}")

        loader = DirectoryLoader(path=DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)

        raw_documents = []

        for doc in loader.lazy_load():
            raw_documents.append(doc)

        if not raw_documents:
            logger.warning(
                f"No valid PDF files identified in target directory: {DATA_PATH}"
            )
        else:
            logger.info(f"Successfully loaded {len(raw_documents)} documents.")

        return raw_documents
    except Exception as e:
        err_msg = CustomException("Cannot load data", original_error=e)
        logger.error(str(err_msg))
        raise err_msg


def create_chunks(documents: List[Document]) -> List[Document]:
    """
    Splits documents into smaller semantic text fragments based on configured parameters.
    """
    try:
        if not documents:
            raise CustomException(
                "Ingestion halted: Text fragmentation context received an empty documents list."
            )
        logger.info(f"Found {len(documents)} documents.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

        chunks = text_splitter.split_documents(documents=documents)

        logger.info(f"Created {len(chunks)} chunks.")

        return chunks
    except Exception as e:
        err_msg = CustomException(
            "Pipeline processing failed during text chunk generation phase",
            original_error=e,
        )
        logger.error(str(err_msg))

        raise err_msg
