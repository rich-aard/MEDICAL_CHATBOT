import os
from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.components.embedding import get_embedding_model

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

from app.config.config import DB_FAISS_PATH

logger = get_logger(__name__)


def load_vector_store() -> FAISS:
    """
    Loads an existing local FAISS vector store database from disk.
    """
    try:
        embedding_model = get_embedding_model()

        if os.path.exists(DB_FAISS_PATH):
            logger.info(f"Loading existing FAISS vector store from: {DB_FAISS_PATH}")

            vector_store = FAISS.load_local(
                folder_path=DB_FAISS_PATH,
                embeddings=embedding_model,
                allow_dangerous_deserialization=True,
            )
            logger.info("FAISS vector store successfully loaded into memory.")
            return vector_store
        else:
            logger.warning(
                f"No pre-existing vector store identified at path: {DB_FAISS_PATH}"
            )
            raise CustomException(f"Vector store directory missing: {DB_FAISS_PATH}")
    except Exception as e:
        err_msg = CustomException(
            "Pipeline execution failed while loading the vector store.",
            original_error=e,
        )
        logger.error(str(err_msg))
        raise err_msg


def create_save_vector_store(chunks: List[Document]) -> FAISS:
    """
    Generates embeddings for raw text chunks and saves the binary FAISS index to disk.
    """
    try:
        if not chunks:
            raise CustomException(
                "Cannot create vector store: Received an empty list of document chunks."
            )

        embedding_model = get_embedding_model()
        batch_size = 64
        logger.info(f"Initializing baseline FAISS index with first batch of {min(batch_size, len(chunks))} chunks...")
        
        first_batch = chunks[:batch_size]
        vector_store = FAISS.from_documents(
            documents=first_batch,
            embedding=embedding_model
        )

        # Iteratively process the remaining chunks
        if len(chunks) > batch_size:
            logger.info("Processing remaining chunks sequentially in batches of 64...")
            for i in range(batch_size, len(chunks), batch_size):
                current_batch = chunks[i : i + batch_size]
                vector_store.add_documents(documents=current_batch)
                logger.info(f"Embedded up to chunk index: {min(i + batch_size, len(chunks))}/{len(chunks)}")
        
        logger.info(f"Saving binary FAISS index assets locally to target path: {DB_FAISS_PATH}")
        vector_store.save_local(folder_path=DB_FAISS_PATH)
        
        logger.info("Successfully generated and saved local vector store database.")
        return vector_store
    except Exception as e:
        err_msg = CustomException(
            "Pipeline execution failed during vector store generation phase.",
            original_error=e,
        )
        logger.error(str(err_msg))
        raise err_msg
